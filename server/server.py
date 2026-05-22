import socket
import threading
import json
import os
from datetime import datetime

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 9999))

resources = {
    "Sala_1": {"blocks": [], "reservations": []},
    "Sala_2": {"blocks": [], "reservations": []},
    "Proiector": {"blocks": [], "reservations": []}
}

clients = {} 
lock = threading.Lock()

def is_overlap(s1, e1, s2, e2):
    return max(s1, s2) < min(e1, e2)

def check_availability(res_name, start, end, ignore_res_id=None):
    if res_name not in resources:
        return False
    res = resources[res_name]
    
    # Verificăm blocurile temporare
    for b in res["blocks"]:
        if is_overlap(start, end, b["start"], b["end"]):
            return False
            
    # Verificăm rezervările finale
    for r in res["reservations"]:
        if ignore_res_id and r["id"] == ignore_res_id:
            continue
        if is_overlap(start, end, r["start"], r["end"]):
            return False
    return True

def broadcast(message):
    data = json.dumps(message).encode('utf-8')
    for conn in list(clients.keys()):
        try:
            conn.sendall(data + b'\n')
        except:
            pass

def handle_client(conn, addr):
    username = None
    try:
        buffer = ""
        while True:
            data = conn.recv(4096)
            if not data:
                break
            buffer += data.decode('utf-8')
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if not line.strip(): continue
                req = json.loads(line)
                
                with lock:
                    action = req.get("action")
                    
                    if action == "LOGIN":
                        username = req["name"]
                        clients[conn] = username
                        conn.sendall(json.dumps({"status": "ok", "msg": f"Bun venit, {username}!", "resources": resources}).encode('utf-8') + b'\n')
                    
                    elif action == "BLOCK":
                        res_name, start, end = req["resource"], req["start"], req["end"]
                        if check_availability(res_name, start, end):
                            resources[res_name]["blocks"].append({"user": username, "start": start, "end": end})
                            conn.sendall(json.dumps({"status": "ok", "msg": "Resursa a fost blocata cu succes."}).encode() + b'\n')
                            broadcast({"action": "NOTIFY", "msg": f"{username} a blocat temporar {res_name}."})
                        else:
                            conn.sendall(json.dumps({"status": "error", "msg": "Suprapunere detectata! Resursa este ocupata/blocata."}).encode() + b'\n')

                    elif action == "UNBLOCK":
                        res_name, start, end = req["resource"], req["start"], req["end"]
                        if res_name in resources:
                            res = resources[res_name]
                            res["blocks"] = [b for b in res["blocks"] if not (b["user"] == username and b["start"] == start and b["end"] == end)]
                            conn.sendall(json.dumps({"status": "ok", "msg": "Blocajul a fost anulat."}).encode() + b'\n')
                            broadcast({"action": "NOTIFY", "msg": f"{username} a anulat blocajul pentru {res_name}."})

                    elif action == "RESERVE":
                        res_name, start, end = req["resource"], req["start"], req["end"]
                        if res_name in resources:
                            res = resources[res_name]
                            res["blocks"] = [b for b in res["blocks"] if not (b["user"] == username and b["start"] == start and b["end"] == end)]
                            res_id = str(datetime.now().timestamp())
                            res["reservations"].append({"id": res_id, "user": username, "start": start, "end": end})
                            conn.sendall(json.dumps({"status": "ok", "msg": f"Rezervare finalizata cu ID-ul: {res_id}"}).encode() + b'\n')
                            broadcast({"action": "NOTIFY", "msg": f"{username} a finalizat o rezervare pentru {res_name}."})

                    elif action == "MODIFY":
                        res_name, res_id, n_start, n_end = req["resource"], req["id"], req["new_start"], req["new_end"]
                        if check_availability(res_name, n_start, n_end, ignore_res_id=res_id):
                            for r in resources[res_name]["reservations"]:
                                if r["id"] == res_id and r["user"] == username:
                                    r["start"], r["end"] = n_start, n_end
                                    conn.sendall(json.dumps({"status": "ok", "msg": "Rezervarea a fost modificata."}).encode() + b'\n')
                                    broadcast({"action": "NOTIFY", "msg": f"{username} a modificat o rezervare la {res_name}."})
                                    break
                        else:
                            conn.sendall(json.dumps({"status": "error", "msg": "Suprapunere detectata la modificare."}).encode() + b'\n')

                    elif action == "DELETE":
                        res_name, res_id = req["resource"], req["id"]
                        if res_name in resources:
                            res = resources[res_name]
                            res["reservations"] = [r for r in res["reservations"] if not (r["id"] == res_id and r["user"] == username)]
                            conn.sendall(json.dumps({"status": "ok", "msg": "Rezervarea a fost stearsa."}).encode() + b'\n')
                            broadcast({"action": "NOTIFY", "msg": f"{username} a sters o rezervare la {res_name}."})
                        
    except Exception as e:
        pass 
    finally:
        with lock:
            if username:
                for res_name, data in resources.items():
                    original_len = len(data["blocks"])
                    data["blocks"] = [b for b in data["blocks"] if b["user"] != username]
                    if len(data["blocks"]) < original_len:
                        broadcast({"action": "NOTIFY", "msg": f"Toate blocajele lui {username} au fost eliberate automat."})
            if conn in clients:
                del clients[conn]
        conn.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[*] Serverul asculta pe portul {PORT}...")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
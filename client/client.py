import socket
import threading
import json
import sys

HOST = '127.0.0.1'
PORT = 9999

def listen_messages(sock):
    buffer = ""
    while True:
        try:
            data = sock.recv(4096)
            if not data: break
            buffer += data.decode('utf-8')
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if not line.strip(): continue
                msg = json.loads(line)
                
                if msg.get("action") == "NOTIFY":
                    print(f"\n[NOTIFICARE IN TIMP REAL] {msg['msg']}\n> ", end="", flush=True)
                elif msg.get("status") == "error":
                    print(f"\n[EROARE] {msg['msg']}\n> ", end="", flush=True)
                elif msg.get("status") == "ok" and "resources" in msg:
                    print(f"\n[SERVER] {msg['msg']}")
                    print("=== LISTA RESURSE ===")
                    for name, data in msg["resources"].items():
                        print(f"- {name}:")
                        if not data["reservations"] and not data["blocks"]:
                            print("  (Resursa este libera)")
                        for r in data["reservations"]: 
                            print(f"  [REZERVARE] {r['start']} -> {r['end']} de {r['user']} (ID: {r['id']})")
                        for b in data["blocks"]: 
                            print(f"  [BLOCAJ TEMPORAR] {b['start']} -> {b['end']} de {b['user']}")
                    print("=====================\n> ", end="", flush=True)
                else:
                    print(f"\n[SERVER] {msg.get('msg', 'OK')}\n> ", end="", flush=True)
        except Exception as e:
            print("\nConexiunea cu serverul a fost inchisa.", flush=True)
            break

def send_req(sock, req):
    sock.sendall(json.dumps(req).encode('utf-8') + b'\n')

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except ConnectionRefusedError:
        print(f"Nu ma pot conecta la {HOST}:{PORT}. Asigura-te ca serverul este pornit!")
        return

    name = input("Introdu numele tau de utilizator: ")
    send_req(sock, {"action": "LOGIN", "name": name})

    threading.Thread(target=listen_messages, args=(sock,), daemon=True).start()

    help_menu = """
--- COMENZI DISPONIBILE ---
1. BLOCK <resursa> <start> <end>
2. UNBLOCK <resursa> <start> <end>
3. RESERVE <resursa> <start> <end>
4. MODIFY <resursa> <id_rezervare> <new_start> <new_end>
5. DELETE <resursa> <id_rezervare>
*(Format date: YYYY-MM-DDTHH:MM | Resurse: Sala_1, Sala_2, Proiector)*
    """
    print(help_menu)

    while True:
        try:
            cmd = input().strip().split()
            if not cmd: continue
            
            action = cmd[0].upper()
            if action == "BLOCK" and len(cmd) == 4:
                send_req(sock, {"action": "BLOCK", "resource": cmd[1], "start": cmd[2], "end": cmd[3]})
            elif action == "UNBLOCK" and len(cmd) == 4:
                send_req(sock, {"action": "UNBLOCK", "resource": cmd[1], "start": cmd[2], "end": cmd[3]})
            elif action == "RESERVE" and len(cmd) == 4:
                send_req(sock, {"action": "RESERVE", "resource": cmd[1], "start": cmd[2], "end": cmd[3]})
            elif action == "MODIFY" and len(cmd) == 5:
                send_req(sock, {"action": "MODIFY", "resource": cmd[1], "id": cmd[2], "new_start": cmd[3], "new_end": cmd[4]})
            elif action == "DELETE" and len(cmd) == 3:
                send_req(sock, {"action": "DELETE", "resource": cmd[1], "id": cmd[2]})
            else:
                print("Comanda invalida. Verifica numarul de parametri.")
                print("> ", end="", flush=True)
        except KeyboardInterrupt:
            print("\nDeconectare...")
            break

if __name__ == "__main__":
    main()
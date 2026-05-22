# 📅 Sistem pentru Rezervarea Resurselor (Client-Server)

O aplicație distribuită de tip client-server care permite utilizatorilor să vizualizeze, să blocheze temporar și să rezerve resurse partajate pe intervale de timp. Aplicația utilizează comunicare prin socket-uri TCP și un protocol bazat pe JSON pentru a asigura sincronizarea în timp real a tuturor clienților conectați.

## ⚙️ Arhitectură și Tehnologii

Aplicația este construită folosind **Python 3** și funcționează pe un model concurent. 
* **Serverul** acceptă conexiuni multiple folosind `threading` și gestionează un sistem de *lock-uri* (mutex) pentru a preveni condițiile de cursă (race conditions) la modificarea datelor.
* **Clientul** rulează un fir de execuție secundar (`daemon thread`) dedicat exclusiv ascultării mesajelor de la server, permițând astfel primirea notificărilor în timp real (broadcast) fără a bloca interfața în linia de comandă.
* **Infrastructură:** Serverul este containerizat folosind **Docker** și lansat prin **Docker Compose**.

## 🚀 Instrucțiuni de Rulare

### 1. Pornirea Serverului (Docker)
Asigură-te că ai Docker instalat. Din rădăcina proiectului, rulează comanda:

```bash
docker compose up --build
```

Serverul va porni și va asculta conexiuni pe portul **9999**.

### 2. Pornirea Clientului (Local)
Deschide un terminal nou și rulează scriptul clientului:

```bash
python client.py
```

*Notă: Implicit, clientul se conectează la `127.0.0.1:9999`. Sistemul suportă conectarea simultană a oricâtor clienți.*

## 💬 Protocolul de Comunicare (JSON over TCP)

Schimbul de mesaje între client și server se face trimițând obiecte JSON, serializate ca șiruri de caractere și delimitate de caracterul `\n`.

### Acțiuni trimise de Client (`action`):
* `LOGIN` - Înregistrarea numelui de utilizator.
* `BLOCK` - Blocarea temporară a unei resurse (pentru a preveni rezervarea ei de către altcineva în timp ce utilizatorul completează detaliile).
* `UNBLOCK` - Eliberarea blocajului temporar.
* `RESERVE` - Transformarea unui blocaj într-o rezervare finală (generează un ID unic de rezervare).
* `MODIFY` - Modificarea intervalului orar pentru o rezervare existentă.
* `DELETE` - Ștergerea definitivă a unei rezervări.

### Răspunsuri și Notificări de la Server:
* `status: "ok" / "error"` - Confirmarea sau respingerea acțiunii (ex: suprapunere detectată).
* `NOTIFY` - Mesaj de tip broadcast trimis către toți clienții pentru a-i informa că starea unei resurse s-a modificat (ex: "*UserX a blocat temporar Sala_1*").

## 🛠️ Funcționalități Implementate

- [x] **Conectare și listare:** La conectare, clientul primește instantaneu starea la zi a resurselor (`Sala_1`, `Sala_2`, `Proiector`).
- [x] **Blocare temporară:** Verificare strictă a suprapunerilor cu rezervările și blocajele existente.
- [x] **Rezervare definitivă:** Translatarea unui blocaj într-o rezervare persistentă, cu ID unic (timestamp).
- [x] **Modificare / Ștergere:** Clienții își pot gestiona doar propriile rezervări.
- [x] **Notificări Real-Time:** Orice modificare este propagată instant către toți utilizatorii activi.
- [x] **Cleanup la Deconectare:** Dacă un client își închide aplicația (sau cade conexiunea) având un blocaj temporar activ, serverul detectează deconectarea și eliberează automat resursa, notificând restul clienților.

## 📝 Formatul Datelor
Pentru comenzi, intervalele de timp sunt transmise sub formă de text. Se recomandă formatul ISO: `YYYY-MM-DDTHH:MM` (ex: `2026-05-25T14:00`). Validarea suprapunerilor este agnostică la format, atâta timp cât datele pot fi comparate lexicografic corect.
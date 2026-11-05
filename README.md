# Multi-Threaded Online Chat Application

A high-performance, multi-threaded GUI chat application developed in **Python** using **PyQt5** and **TCP Socket Programming**. The project implements a client-server architecture with custom JSON application-layer protocols, thread synchronization, and real-time message broadcasting.

---

##  Technical Specifications & Architecture
* **Language:** Python 3.x
* **GUI Framework:** PyQt5
* **Networking Protocol:** TCP/IP (Stream Sockets via Python `socket` module)
* **Concurrency Model:** Multi-threading via Python `threading` and PyQt5 `QThread` / `pyqtSignal`
* **Data Interchange Format:** JSON Protocol Framing (Message Type, Payload, Timestamp)

---

##  Key Technical Features & Engineering Highlights

### 1. Robust Server-Side Concurrency & Thread Synchronization
* **Non-Blocking Client Handling:** The server spawns a dedicated worker thread for each connected client to handle concurrent incoming messages without blocking the main event loop.
* **Thread-Safe Data Structures:** Employs thread synchronization mechanisms (Mutex locks) to safely update shared resources, connected client pools, and active channel states.

### 2. Custom Application-Layer JSON Protocol
* Implements a structured protocol format for request/response framing:
  * **Authentication & Handshake:** Secure payload exchange for login/registration.
  * **Real-Time Broadcasting:** Packet parsing for routing messages to specific chat rooms or individual clients.
  * **Status Signals:** System heartbeat notifications (user joined, left, typing status).

### 3. Asynchronous PyQt5 Event-Driven GUI
* **Decoupled Architecture:** Separates networking logic from the UI rendering thread using custom `QThread` workers and `pyqtSignal` channels to maintain a responsive user interface during heavy network I/O.
* **Custom Dynamic UI:** Responsive chat windows, room navigation, and user lists built with modular PyQt5 widgets.

---


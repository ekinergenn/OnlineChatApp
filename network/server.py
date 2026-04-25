import socket
import threading
import json

class ChatServer:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"[SUNUCU] {self.host}:{self.port} üzerinde çalışıyor...")

        while True:
            client_sock, addr = self.server_socket.accept()
            print(f"[BAĞLANTI] {addr} bağlandı.")
            self.clients.append(client_sock)
            
            thread = threading.Thread(target=self.handle_client, args=(client_sock, addr))
            thread.start()

    def handle_client(self, conn, addr):
        while True:
            try:
                # 1. Ham veriyi al
                raw_data = conn.recv(4096)
                if not raw_data:
                    break

                # 2. Protokolüne uygun olarak veriyi parçala (<END> ayırıcısını kontrol et)
                decoded_data = raw_data.decode('utf-8')
                messages = decoded_data.split("<END>")

                for msg in messages:
                    if not msg: continue
                    
                    packet = json.loads(msg)
                    print(f"[GELEN PAKET] {addr}: {packet}")

                    # 3. Gelen paketi işle ve cevap hazırla
                    self.process_request(conn, packet)

            except Exception as e:
                print(f"[HATA] {addr} hatası: {e}")
                break

        print(f"[AYRILDI] {addr} bağlantısı kesildi.")
        self.clients.remove(conn)
        conn.close()

    def process_request(self, conn, packet):
        """İstemcinin gönderdiği 'type' değerine göre cevap üretir."""
        msg_type = packet.get("type")
        
        # Senin logReg_service içindeki paket yapına uygun kontrol
        if msg_type == "login_request":
            payload = packet.get("payload", {})
            name = payload.get("name")
            password = payload.get("password")

            # BASİT KONTROL: Admin/1234 ise başarılı sayalım
            if name == "admin" and password == "1234":
                response = {
                    "type": "login_response",
                    "payload": {
                        "status": "success",
                        "message": "Hoş geldin admin!",
                        "user_id": 1
                    }
                }
            else:
                response = {
                    "type": "login_response",
                    "payload": {
                        "status": "fail",
                        "message": "Kullanıcı adı veya şifre hatalı!"
                    }
                }
            
            self.send_packet(conn, response)

    def send_packet(self, conn, packet_dict):
        """Senin Protocol.py yapına uygun şekilde gönderim yapar."""
        json_data = json.dumps(packet_dict) + "<END>"
        conn.sendall(json_data.encode('utf-8'))

if __name__ == "__main__":
    server = ChatServer()
    server.start()
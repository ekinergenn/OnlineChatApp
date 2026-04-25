import socket
import json
from network.message_handler import MessageHandler
from network.protocol import Protocol

class Client:
    def __init__(self,services:list, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.message_handler = MessageHandler(services)

    def register_services(self, services_dict):
            """Servisler yaratıldıktan sonra Client'a bu fonksiyonla tanıtılır."""
            self.message_handler.services = services_dict
    def connect(self):
        """Sunucuya bağlanmayı dener."""
        try:
            self.client_socket.connect((self.host, self.port))
            print("[SİSTEM] Sunucuya başarıyla bağlanıldı.")
            return True
        except Exception as e:
            print(f"[HATA] Sunucuya bağlanılamadı: {e}")
            return False

    def send_data(self,packet) -> bool:
        """Veriyi güvenli bir şekilde karşıya gönderir."""
        try:
            self.client_socket.sendall(Protocol.create_packet(packet))
            return True
        except socket.error as e:
            print(f"[AĞ HATASI] Veri gönderilemedi: {e}")
            return False

    def receive_data(self, buffer_size=4096) -> bytes:
        """Ağdan gelen veriyi okur. Bağlantı koparsa boş byte döndürür."""
        try:
            data = self.client_socket.recv(buffer_size)
            return data
        except ConnectionResetError:
            print("[AĞ UYARISI] Karşı taraf bağlantıyı kopardı.")
            return b""

    def listen_for_messages(self):
        """Sürekli olarak sunucudan mesaj bekler. 
        UYARI: Bu fonksiyon ana programı donduracağı için ayrı thread'de çağrılmalıdır!"""
        while True:
            try:
                data = self.receive_data()
                if not data:
                    break
                self.message_handler.handle_incoming_data(data)
                
            except Exception:
                print("\n[SİSTEM] Sunucu bağlantısı koptu.")
                self.client_socket.close()
                break
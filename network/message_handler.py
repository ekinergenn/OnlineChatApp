# network/message_handler.py
from network.protocol import Protocol

class MessageHandler:
    def __init__(self, services):
        # Yönlendirme yapabilmek için servisleri içeri alıyoruz
        self.services = services

    def handle_incoming_data(self, raw_bytes: bytes):
        """Ağdan gelen ham veriyi ayrıştırır ve doğru servise yönlendirir."""
        
        # 1. Protokol aracılığıyla paketi aç
        packet = Protocol.parse_packet(raw_bytes)
        msg_type = packet.get("type")
        payload = packet.get("payload")
        print(packet)
        # 2. Mesajın türüne göre ilgili iş mantığını (Service) tetikle
        if msg_type == "chat_message":
            # Örneğin: Şifreli mesajı çözmesi ve ekrana basması için servise gönder
            self.services['chat_service'].receive_new_message(payload)
            
        elif msg_type == "login_response":
            self.services['logreg_service'].handle_server_response(payload)
            
        elif msg_type == "error":
            print("[HATA] Sunucudan hatalı paket geldi.")
            
        else:
            print(f"[UYARI] Bilinmeyen paket türü: {msg_type}")
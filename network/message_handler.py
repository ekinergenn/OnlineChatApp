from network.protocol import Protocol

class MessageHandler:
    def __init__(self, services):
        self.services = services

    def handle_incoming_data(self, raw_bytes: bytes):
        packet = Protocol.parse_packet(raw_bytes)
        msg_type = packet.get("type")
        payload = packet.get("payload")
        print(packet)

        if msg_type == "chat_message":
            self.services['chat_service'].receive_new_message(payload)

        elif msg_type == "login_response":
            self.services['logreg_service'].handle_server_response(payload)

        elif msg_type == "register_response":
            self.services['logreg_service'].handle_register_response(payload)

        elif msg_type == "delete_chat_response":
            self.services['chat_service'].handle_delete_chat_response(payload)

        elif msg_type == "search_users_response":
            self.services['chat_service'].handle_search_response(payload)

        elif msg_type == "get_user_chats_response":
            self.services['chat_service'].handle_get_user_chats_response(payload)
            
        elif msg_type == "create_chat_response":
            self.services['chat_service'].handle_create_chat_response(payload)

        elif msg_type == "error":
            print("[HATA] Sunucudan hatalı paket geldi.")

        else:
            print(f"[UYARI] Bilinmeyen paket türü: {msg_type}")
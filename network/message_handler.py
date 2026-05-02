from network.protocol import Protocol

class MessageHandler:
    def __init__(self, services):
        self.services = services

    def handle_incoming_data(self, raw_str: str):
        print(f"[HANDLER DEBUG] Ham veri geldi: {raw_str[:50]}...")
        packet = Protocol.parse_packet(raw_str)
        msg_type = packet.get("type")
        payload = packet.get("payload")
        print(packet)

        if msg_type == "chat_message":
            self.services['message_service'].receive_new_message(payload)
            
        elif msg_type == "messages_read_receipt":
            self.services['message_service'].receive_messages_read_receipt(payload)

        elif msg_type == "typing_indicator":
            self.services['message_service'].receive_typing_indicator(payload)

        elif msg_type == "user_status_update":
            self.services['chat_service'].handle_user_status_update(payload)

        elif msg_type == "get_user_status_response":
            self.services['chat_service'].handle_user_status_response(payload)

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

        elif msg_type == "block_user_response":
            self.services['block_service'].handle_block_response(payload)

        elif msg_type == "get_block_list_response":
            self.services['block_service'].handle_block_list_response(payload)

        elif msg_type == "error":
            msg = payload.get("message", "Sunucudan hata alındı.")
            print(f"[HATA] {msg}")
            # Opsiyonel: UI'da gösterilmek üzere bir sinyal fırlatılabilir

        elif msg_type == "delete_account_response":
            if payload.get("status") == "success":
                # main_page içinden metodla login ekranına yönlendir
                self.services['logreg_service'].handle_logout_logic()

        elif msg_type == "get_all_users_response":
            self.services['chat_service'].handle_get_all_users_response(payload)

        elif msg_type == "create_group_response":
            self.services['chat_service'].handle_create_group_response(payload)

        elif msg_type == "get_public_key_response":
            if 'encryption_service' in self.services:
                self.services['encryption_service'].handle_get_public_key_response(payload)

        elif msg_type == "get_starred_messages_response":
            print(">>> HANDLER: Sunucudan yıldızlı mesajlar PAKETİ GELDİ!")
            if 'message_service' in self.services:
                self.services['message_service'].handle_get_starred_messages_response(payload)

        elif msg_type == "star_message_response":
            print(f"[İSTEMCİ] Yıldızlama onayı: {payload.get('status')}")

        else:
            print(f"[UYARI] Bilinmeyen paket türü: {msg_type}")
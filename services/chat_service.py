from PyQt5.QtCore import QObject, pyqtSignal
import time
import uuid

class ChatService(QObject):
    delete_chat_response_signal = pyqtSignal(dict)
    receive_message_signal = pyqtSignal(dict)
    user_chats_loaded_signal = pyqtSignal(list)
    search_results_signal = pyqtSignal(list)
    create_chat_response_signal = pyqtSignal(dict) # Sadece tekli sohbet için

    def __init__(self, client):
        super().__init__()
        self.client = client

    def send_chat_message(self, chat_id: str, content: str, sender_id: int, sender: str = ""):
        packet = {
            "type": "chat_message",
            "payload": {
                "message_id": uuid.uuid4().hex,
                "chat_id": chat_id,
                "content": content,
                "sender_id": sender_id,
                "sender": sender,
                "timestamp": int(time.time()),
                "status": "sent",
                "read_by": [sender]
            }
        }
        self.client.send_data(packet)

    def send_mark_as_read(self, chat_id: str, message_ids: list, username: str):
        if not message_ids:
            return
        packet = {
            "type": "mark_messages_read",
            "payload": {
                "chat_id": chat_id,
                "message_ids": message_ids,
                "username": username
            }
        }
        self.client.send_data(packet)

    def receive_new_message(self, payload: dict):
        self.receive_message_signal.emit(payload)

    def send_get_user_chats_request(self, username: str):
        packet = {
            "type": "get_user_chats_request",
            "payload": {
                "username": username
            }
        }
        self.client.send_data(packet)

    def handle_get_user_chats_response(self, payload: dict):
        chats = payload.get("chats", [])
        self.user_chats_loaded_signal.emit(chats)

    def send_create_chat_request(self, target_username: str, my_username: str):
        packet = {
            "type": "create_chat_request",
            "payload": {
                "members": [my_username, target_username]
            }
        }
        self.client.send_data(packet)

    def handle_create_chat_response(self, payload: dict):
        """Sunucudan gelen yeni chat_id bilgisini kontrolcüye iletir."""
        # Payload içinde artık chat_id ve target_username var
        self.create_chat_response_signal.emit(payload)

    def send_search_request(self, query: str, username: str):
        packet = {
            "type": "search_users_request",
            "payload": {
                "query": query,
                "username": username
            }
        }
        self.client.send_data(packet)

    def handle_search_response(self, payload: dict):
        results = payload.get("results", [])
        self.search_results_signal.emit(results)
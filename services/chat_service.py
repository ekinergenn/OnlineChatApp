from PyQt5.QtCore import QObject, pyqtSignal
import time

class ChatService(QObject):
    delete_chat_response_signal = pyqtSignal(dict)
    user_chats_loaded_signal = pyqtSignal(list)
    search_results_signal = pyqtSignal(list)
    create_chat_response_signal = pyqtSignal(dict) # Sadece tekli sohbet için

    def __init__(self, client):
        super().__init__()
        self.client = client
        self._pending_delete_chat_name = None

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

    def send_delete_chat_request(self, chat_id: str, chat_name: str):
        self._pending_delete_chat_name = chat_name  # ← chat_name saklıyoruz
        packet = {
            "type": "delete_chat_request",
            "payload": {"chat_id": chat_id}
        }
        self.client.send_data(packet)

    def handle_delete_chat_response(self, payload: dict):
        payload["chat_name"] = self._pending_delete_chat_name  # ← chat_name ekliyoruz
        self._pending_delete_chat_name = None
        self.delete_chat_response_signal.emit(payload)
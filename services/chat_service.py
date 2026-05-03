from PyQt5.QtCore import QObject, pyqtSignal
import time

class ChatService(QObject):
    delete_chat_response_signal = pyqtSignal(dict)
    user_chats_loaded_signal = pyqtSignal(list)
    search_results_signal = pyqtSignal(list)
    create_chat_response_signal = pyqtSignal(dict) # Sadece tekli sohbet için
    all_users_loaded_signal = pyqtSignal(list)
    create_group_response_signal = pyqtSignal(dict)
    user_status_signal = pyqtSignal(dict)
    messages_read_signal = pyqtSignal(dict) # Yeni: (chat_id, message_ids, read_by)
    privacy_settings_loaded_signal = pyqtSignal(dict) # Yeni: (settings)
    update_privacy_response_signal = pyqtSignal(bool) # Yeni: (success)
    chat_deleted_notification_signal = pyqtSignal(str) # Yeni: (chat_name)

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

    def send_delete_chat_request(self, chat_id: str, chat_name: str, username: str, action: str = "delete"):
        self._pending_delete_chat_name = chat_name
        packet = {
            "type": "delete_chat_request",
            "payload": {
                "chat_id": chat_id,
                "chat_name": chat_name,
                "username": username,
                "action": action  # Sunucuya ne yapacağını söyler
            }
        }
        self.client.send_data(packet)

    def handle_delete_chat_response(self, payload: dict):
        payload["chat_name"] = self._pending_delete_chat_name  # ← chat_name ekliyoruz
        self._pending_delete_chat_name = None
        self.delete_chat_response_signal.emit(payload)

    def send_get_all_users_request(self, username: str):
        packet = {
            "type": "get_all_users_request",
            "payload": {"username": username}
        }
        self.client.send_data(packet)

    def handle_get_all_users_response(self, payload: dict):
        users = payload.get("users", [])
        self.all_users_loaded_signal.emit(users)

    def send_create_group_request(self, group_name: str, members: list):
        packet = {
            "type": "create_group_request",
            "payload": {
                "group_name": group_name,
                "members": members
            }
        }
        self.client.send_data(packet)

    def handle_create_group_response(self, payload: dict):
        self.create_group_response_signal.emit(payload)

    def reset(self):
        #servis içindeki sadece kullanıcıya özel geçici verileri sıfırlar
        self._pending_delete_chat_name = None
        print("[SERVICE] ChatService verileri temizlendi, bağlantı (client) korunuyor.")

    def send_get_user_status_request(self, username: str):
        """Belirli bir kullanıcının online/offline durumunu sorgular."""
        packet = {
            "type": "get_user_status_request",
            "payload": {"username": username}
        }
        self.client.send_data(packet)

    def handle_user_status_response(self, payload: dict):
        """Durum sorgu cevabını UI'a iletir."""
        self.user_status_signal.emit(payload)

    def handle_user_status_update(self, payload: dict):
        """Sunucudan gelen anlık durum değişikliğini UI'a iletir."""
        self.user_status_signal.emit(payload)

    def send_update_privacy_settings(self, username: str, settings: dict):
        self.client.send_data({
            "type": "update_privacy_settings_request",
            "payload": {"username": username, "settings": settings}
        })

    def send_get_privacy_settings(self, username: str):
        self.client.send_data({
            "type": "get_privacy_settings_request",
            "payload": {"username": username}
        })

    def handle_get_privacy_settings_response(self, payload: dict):
        self.privacy_settings_loaded_signal.emit(payload.get("settings", {}))

    def handle_update_privacy_settings_response(self, payload: dict):
        self.update_privacy_response_signal.emit(payload.get("status") == "success")

    def handle_messages_read(self, payload: dict):
        self.messages_read_signal.emit(payload)

    def handle_chat_deleted_notification(self, payload: dict):
        chat_name = payload.get("chat_name")
        if chat_name:
            self.chat_deleted_notification_signal.emit(chat_name)

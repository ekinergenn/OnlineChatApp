from PyQt5.QtCore import QObject, pyqtSignal

class ChatService(QObject):
    # Sunucudan cevap gelince arayüzü güncellemek için sinyal
    create_group_response_signal = pyqtSignal(dict)
    delete_chat_response_signal = pyqtSignal(dict)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def send_create_group_request(self, group_name: str, creator_id: int, members: list):
        """Sunucuya yeni bir grup oluşturma isteği gönderir."""
        packet = {
            "type": "create_group_request",
            "payload": {
                "group_name": group_name,
                "creator_id": creator_id,
                "members": members
            }
        }
        self.client.send_data(packet)

    def handle_server_response(self, payload: dict):
        """Sunucudan gelen grup oluşturma sonucunu işler."""
        self.create_group_response_signal.emit(payload)

    def send_delete_chat_request(self, chat_name: str, user_id: int):
        """Sunucuya sohbet silme isteği gönderir."""
        packet = {
            "type": "delete_chat_request",
            "payload": {
                "chat_name": chat_name,
                "user_id": user_id
            }
        }
        self.client.send_data(packet)

    def handle_delete_chat_response(self, payload: dict):
        """Sunucudan gelen silme yanıtını UI'a iletir."""
        self.delete_chat_response_signal.emit(payload)
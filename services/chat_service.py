from PyQt5.QtCore import QObject, pyqtSignal

class ChatService(QObject):
    # Sunucudan cevap gelince arayüzü güncellemek için sinyal
    create_group_response_signal = pyqtSignal(dict)

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
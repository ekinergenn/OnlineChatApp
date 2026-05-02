from PyQt5.QtCore import QObject, pyqtSignal
import time
import uuid

class MessageService(QObject):
    receive_message_signal = pyqtSignal(dict)
    messages_read_receipt_signal = pyqtSignal(dict)
    typing_indicator_signal = pyqtSignal(dict)
    starred_messages_loaded_signal = pyqtSignal(list)
    unstar_response_signal = pyqtSignal(dict)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def send_chat_message(self, chat_id: str, content: str, sender_id: int, sender: str = "", encrypted_data: dict = None, msg_type: str = "text"):
        payload = {
            "message_id": uuid.uuid4().hex,
            "chat_id": chat_id,
            "content": content,
            "msg_type": msg_type,
            "sender_id": sender_id,
            "sender": sender,
            "timestamp": int(time.time()),
            "status": "sent",
            "read_by": [sender]
        }
        if encrypted_data:
            payload["encrypted_data"] = encrypted_data

        packet = {
            "type": "chat_message",
            "payload": payload
        }
        self.client.send_data(packet)

    def receive_new_message(self, payload: dict):
        self.receive_message_signal.emit(payload)

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

    def receive_messages_read_receipt(self, payload: dict):
        self.messages_read_receipt_signal.emit(payload)

    def send_typing_indicator(self, chat_id: str, sender: str, is_typing: bool):
        """Yazıyor / yazmayı bıraktı sinyalini sunucuya gönderir."""
        packet = {
            "type": "typing_indicator",
            "payload": {
                "chat_id": chat_id,
                "sender": sender,
                "is_typing": is_typing
            }
        }
        self.client.send_data(packet)

    def receive_typing_indicator(self, payload: dict):
        """Sunucudan gelen typing_indicator paketini UI'a iletir."""
        self.typing_indicator_signal.emit(payload)

    def send_unstar_request(self, star_data):
        #ayarlar sayfasından gelen yıldız kaldırma isteğini sunucuya ilet
        payload = {
            "message_id": star_data.get("message_id"),
            "username": star_data.get("starred_by")
        }
        packet = {
            "type": "unstar_request",
            "payload": payload
        }
        self.client.send_data(packet)
        print(f"[SERVICE] Yıldız kaldırma isteği sunucuya iletildi: {payload}")

    def send_star_message(self, message_data: dict):
        #yıldızlama veya yıldız kaldırma isteğini sunucuya gönderir
        packet = {
            "type": "star_message_request",
            "payload": message_data
        }
        self.client.send_data(packet)

    def send_get_starred_messages(self, username: str):
        #kullanıcının tüm yıldızlı mesajlarını sunucudan ister
        packet = {
            "type": "get_starred_messages_request",
            "payload": {"username": username}
        }
        self.client.send_data(packet)

    def handle_get_starred_messages_response(self, payload: dict):
        print(">>> SERVICE: handle_get_starred_messages_response metodu tetiklendi!")
        messages = payload.get("messages", [])
        print(f">>> SERVICE: Sinyal emit ediliyor. Mesaj sayısı: {len(messages)}")
        self.starred_messages_loaded_signal.emit(messages)
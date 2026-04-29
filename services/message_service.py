from PyQt5.QtCore import QObject, pyqtSignal
import time
import uuid

class MessageService(QObject):
    receive_message_signal = pyqtSignal(dict)
    messages_read_receipt_signal = pyqtSignal(dict)

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

from PyQt5.QtCore import QObject, pyqtSignal

class LogRegService(QObject):
    login_response_signal = pyqtSignal(dict)
    register_response_signal = pyqtSignal(dict)

    def __init__(self, client, chat_service=None):
        super().__init__()
        self.client = client
        self.chat_service = chat_service

    def send_login_request(self, name: str, password: str):
        packet = {
            "type": "login_request",
            "payload": {
                "name": name,
                "password": password
            }
        }
        self.client.send_data(packet)

    def send_register_request(self, username: str, password: str, fullname: str, email: str, tel: str):
        packet = {
            "type": "register_request",
            "payload": {
                "username": username,
                "password": password,
                "fullname": fullname,
                "email": email,
                "tel": tel
            }
        }
        self.client.send_data(packet)

    def handle_server_response(self, payload: dict):
        self.login_response_signal.emit(payload)
        if payload.get("status") == "success" and self.chat_service:
            chats = payload.get("chats", [])
            self.chat_service.user_chats_loaded_signal.emit(chats)

    def handle_register_response(self, payload: dict):
        self.register_response_signal.emit(payload)
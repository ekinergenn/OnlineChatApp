from PyQt5.QtCore import QObject, pyqtSignal

class LogRegService(QObject):
    login_response_signal = pyqtSignal(dict)
    register_response_signal = pyqtSignal(dict)
    logout_requested_signal = pyqtSignal()

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

    def send_delete_account_request(self, username, user_id):
        packet = {
            "type": "delete_account_request",
            "payload": {"username": username, "user_id": user_id}
        }
        self.client.send_data(packet)

    def handle_logout_logic(self):
        #hesap silinince çağırılır
        print("[SERVICE] Hesap silme onaylandı, çıkış yapılıyor...")
        self.logout_requested_signal.emit()

    def handle_server_response(self, payload: dict):
        self.login_response_signal.emit(payload)
        # if payload.get("status") == "success" and self.chat_service:
        #     self.chat_service.user_chats_loaded_signal.emit(payload)
        #     print(payload)


    def handle_register_response(self, payload: dict):
        print(payload)
        self.register_response_signal.emit(payload)
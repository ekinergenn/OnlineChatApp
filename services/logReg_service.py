from PyQt5.QtCore import QObject, pyqtSignal

class LogRegService(QObject):
    login_response_signal = pyqtSignal(dict)

    def __init__(self,client):
        super().__init__()
        self.client = client

    def send_login_request(self,name: str,password: str):
        
        packet = {
            "type": "login_request",
            "payload": {
                "name": name,
                "password": password
            }
        }

        self.client.send_data(packet)

    def handle_server_response(self, user_info: dict):
            """MessageHandler paketi buraya yönlendirdiğinde çalışır."""
            print("giris yapildi")
            self.login_response_signal.emit(user_info)
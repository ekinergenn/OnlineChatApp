from PyQt5.QtCore import QObject, pyqtSignal
import time

class BlockService(QObject):
    block_status_changed_signal = pyqtSignal(dict)
    block_list_loaded_signal = pyqtSignal(list)    # Sunucudan gelen engelli listesi

    def __init__(self, client):
        super().__init__()
        self.client = client

    def send_block_user_request(self, blocker_id, blocked_id):
        # sunucuya engelleme isetgi gonderir
        packet = {
            "type": "block_user_request",
            "payload": {
                "blocker_id": blocker_id,
                "blocked_id": blocked_id,
                "timestamp": int(time.time())
            }
        }
        self.client.send_data(packet)

    def send_unblock_user_request(self, blocker_id, blocked_id):
        #sunucuya engel kaldırma istegi gonderir
        packet = {
            "type": "unblock_user_request",
            "payload": {
                "blocker_id": blocker_id,
                "blocked_id": blocked_id,
                "timestamp": int(time.time())
            }
        }
        self.client.send_data(packet)

    def handle_block_response(self, payload: dict):
        #istek sonucu sunucudan gelen veriyi isler
        #  network_manager'dan gelen veriyi sinyalle controller'a yollar
        self.block_status_changed_signal.emit(payload)

    def send_get_block_list_request(self, user_id):
        #engellenen kisilerin listesini sunucudan ister
        packet = {
            "type": "get_block_list_request",
            "payload": {
                "user_id": user_id
            }
        }
        self.client.send_data(packet)

    def handle_block_list_response(self, payload: dict):
        #sunucudan gelen engelli litesini isler
        blocks = payload.get("blocks", [])
        self.block_list_loaded_signal.emit(blocks)
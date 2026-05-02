from PyQt5.QtCore import QObject, pyqtSignal

class CommunityService(QObject):
    user_communities_loaded_signal = pyqtSignal(list)
    search_results_signal = pyqtSignal(list)
    create_community_response_signal = pyqtSignal(dict)
    join_community_response_signal = pyqtSignal(dict)
    community_message_received_signal = pyqtSignal(dict)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def send_create_community_request(self, name, creator):
        self.client.send_data({
            "type": "create_community_request",
            "payload": {"name": name, "creator": creator}
        })

    def send_join_community_request(self, community_id, username):
        self.client.send_data({
            "type": "join_community_request",
            "payload": {"community_id": community_id, "username": username}
        })

    def send_search_communities_request(self, query):
        self.client.send_data({
            "type": "search_communities_request",
            "payload": {"query": query}
        })

    def send_get_user_communities_request(self, username):
        self.client.send_data({
            "type": "get_user_communities_request",
            "payload": {"username": username}
        })

    def send_community_message(self, community_id, sender, content):
        self.client.send_data({
            "type": "community_message",
            "payload": {
                "community_id": community_id,
                "sender": sender,
                "content": content
            }
        })

    def handle_server_response(self, response_type, payload):
        if response_type == "get_user_communities_response":
            self.user_communities_loaded_signal.emit(payload.get("communities", []))
        elif response_type == "search_communities_response":
            self.search_results_signal.emit(payload.get("results", []))
        elif response_type == "create_community_response":
            self.create_community_response_signal.emit(payload)
        elif response_type == "join_community_response":
            self.join_community_response_signal.emit(payload)
        elif response_type == "community_message":
            self.community_message_received_signal.emit(payload)

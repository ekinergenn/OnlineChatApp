from PyQt5.QtWidgets import QMessageBox

class CommunityController:
    def __init__(self, main_page, community_service):
        self.main_page = main_page
        self.community_service = community_service
        self.current_username = None
        self.is_connected = False

    def connect_ui_signals(self):
        """UI sinyallerini bağlar. Login sonrası çağrılır."""
        self.disconnect_ui_signals()
        
        # UI Signals
        self.main_page.communities_page.create_community_signal.connect(self.handle_create_community)
        self.main_page.communities_page.join_community_signal.connect(self.handle_join_community)
        self.main_page.communities_page.search_query_signal.connect(self.handle_search_communities)
        self.main_page.communities_page.send_community_message_signal.connect(self.handle_send_message)
        self.main_page.communities_page.send_community_image_signal.connect(self.handle_send_image)
        
        # Service Signals
        self.community_service.user_communities_loaded_signal.connect(self.on_communities_loaded)
        self.community_service.search_results_signal.connect(self.main_page.communities_page.show_search_results)
        self.community_service.create_community_response_signal.connect(self.on_community_created)
        self.community_service.join_community_response_signal.connect(self.on_community_joined)
        self.community_service.community_message_received_signal.connect(self.on_message_received)
        
        self.is_connected = True

    def disconnect_ui_signals(self):
        """Sinyal bağlantılarını koparır. Logout sırasında çağrılır."""
        try:
            self.main_page.communities_page.create_community_signal.disconnect()
            self.main_page.communities_page.join_community_signal.disconnect()
            self.main_page.communities_page.search_query_signal.disconnect()
            self.main_page.communities_page.send_community_message_signal.disconnect()
            self.main_page.communities_page.send_community_image_signal.disconnect()
            
            self.community_service.user_communities_loaded_signal.disconnect()
            self.community_service.search_results_signal.disconnect()
            self.community_service.create_community_response_signal.disconnect()
            self.community_service.join_community_response_signal.disconnect()
            self.community_service.community_message_received_signal.disconnect()
        except:
            pass
        self.is_connected = False

    def set_current_user(self, profile):
        self.current_username = profile.get("username")
        # Sinyalleri bağla (Eğer daha önce bağlanmadıysa)
        self.connect_ui_signals()
        self.community_service.send_get_user_communities_request(self.current_username)

    def handle_create_community(self, name):
        if self.current_username:
            self.community_service.send_create_community_request(name, self.current_username)

    def handle_join_community(self, community_id):
        if self.current_username:
            self.community_service.send_join_community_request(community_id, self.current_username)

    def handle_search_communities(self, query):
        self.community_service.send_search_communities_request(query)

    def handle_send_message(self, community_id, content):
        if self.current_username:
            self.community_service.send_community_message(community_id, self.current_username, content)

    def handle_send_image(self, community_id, image_path):
        if self.current_username:
            self.community_service.send_community_image(community_id, self.current_username, image_path)

    def on_communities_loaded(self, communities):
        self.main_page.communities_page.load_communities(communities, self.current_username)

    def on_community_created(self, payload):
        if payload.get("status") == "success":
            self.community_service.send_get_user_communities_request(self.current_username)
        else:
            QMessageBox.warning(self.main_page, "Hata", "Topluluk oluşturulamadı.")

    def on_community_joined(self, payload):
        if payload.get("status") == "success":
            self.community_service.send_get_user_communities_request(self.current_username)
        else:
            QMessageBox.warning(self.main_page, "Hata", "Topluluğa katılım sağlanamadı.")

    def on_message_received(self, payload):
        comm_id = payload.get("community_id")
        sender = payload.get("sender")
        content = payload.get("content")
        timestamp = payload.get("timestamp")
        self.main_page.communities_page.add_message_to_ui(comm_id, sender, content, timestamp)

    def reset(self):
        """Oturum kapatıldığında verileri ve sinyalleri temizler."""
        self.current_username = None
        self.disconnect_ui_signals()
        print("[COMMUNITY] Veriler ve sinyaller temizlendi.")

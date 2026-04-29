from PyQt5.QtWidgets import QMessageBox

class ChatController():
    def __init__(self, main_page, chat_service, message_controller):
        self.main_page = main_page
        self.chat_service = chat_service
        self.message_controller = message_controller
        self.current_user_id = None
        self.current_username = None
        self.loaded_chats = set()

        # Signal connections
        self.main_page.search_query_signal.connect(self.handle_search)
        self.main_page.start_chat_signal.connect(self.handle_start_chat)
        
        # Service signals
        self.chat_service.user_chats_loaded_signal.connect(self.load_user_chats)
        self.chat_service.search_results_signal.connect(self.main_page.show_search_results)
        self.chat_service.create_chat_response_signal.connect(self.on_chat_created)

    def set_current_user(self, profile: dict):
        self.current_user_id = profile.get("user_id")
        self.current_username = profile.get("username")
        
        self.chat_service.send_get_user_chats_request(self.current_username)


    def load_user_chats(self, chats: list):
        for chat in chats:
            chat_id = chat.get("chat_id")
            chat_name = chat.get("chat_name", chat_id)
            
            # Add chat to UI
            self.main_page.add_new_chat_to_ui(chat_name)
            # Yükleme işlemi message_controller'a devrediliyor
            self.message_controller.load_historical_messages(chat_name, chat_id, chat.get("messages", []))
            self.loaded_chats.add(chat_id)


    def handle_search(self, query: str):
        self.chat_service.send_search_request(query, self.current_username or "")


    def handle_start_chat(self, target_username: str):
        self.main_page.search_input.clear()
        self.main_page.clear_search_results()

        # 1. Zaten açık bir sekme var mı kontrol et
        already_exists = False
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if hasattr(widget, 'contact_name') and widget.contact_name == target_username:
                already_exists = True
                # Eğer varsa direkt o sekmeye geçiş yapabilirsin
                break

        if already_exists:
            print(f"[BİLGİ] {target_username} ile sohbet zaten yüklü.")
        else:
            # 2. ÖNEMLİ: Hemen add_new_chat_to_ui ÇAĞIRMA!
            # Önce sunucudan chat_id iste[cite: 1]
            print(f"[SİSTEM] {target_username} için ID isteniyor...")
            self.chat_service.send_create_chat_request(target_username, self.current_username)

    def on_chat_created(self, payload: dict):
        """Sunucu 'ID hazır' dediği an burası çalışır."""
        if payload.get("status") == "success":
            chat_id = payload.get("chat_id")
            target_name = payload.get("target_username")
            
            # 3. ŞİMDİ arayüze ekle. Artık elimizde gerçek bir chat_id var![cite: 8]
            self.main_page.add_new_chat_to_ui(target_name)
            
            # UI tarafında bu sekmeye chat_id değerini gizli bir özellik olarak ata
            # Böylece mesaj gönderirken bu ID'yi kullanabiliriz.
            for i in range(self.main_page.chat_screens_stack.count()):
                widget = self.main_page.chat_screens_stack.widget(i)
                if hasattr(widget, 'contact_name') and widget.contact_name == target_name:
                    widget.current_chat_id = chat_id # ID'yi buraya kaydettik
                    break
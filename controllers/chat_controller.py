from PyQt5.QtWidgets import QMessageBox
from services.block_service import BlockService

class ChatController():
    def __init__(self, main_page, chat_service, message_controller, block_service = None):
        self.block_service = block_service
        self.main_page = main_page
        self.chat_service = chat_service
        self.message_controller = message_controller
        self.current_user_id = None
        self.current_username = None
        self.loaded_chats = set()

        # Signal connections
        self.main_page.block_user_signal.connect(self.handle_block_user)
        self.main_page.search_query_signal.connect(self.handle_search)
        self.main_page.start_chat_signal.connect(self.handle_start_chat)
        self.main_page.delete_chat_signal.connect(self.handle_delete_chat)
        self.main_page.profile_page.delete_account_signal.connect(self.handle_delete_account)
        
        # Service signals
        self.chat_service.user_chats_loaded_signal.connect(self.load_user_chats)
        self.chat_service.search_results_signal.connect(self.main_page.show_search_results)
        self.chat_service.create_chat_response_signal.connect(self.on_chat_created)
        self.chat_service.delete_chat_response_signal.connect(self.on_chat_deleted)
        if self.block_service:
            self.block_service.block_status_changed_signal.connect(self.on_block_status_received)

    def set_current_user(self, profile: dict):
        self.current_user_id = profile.get("user_id")
        self.current_username = profile.get("username")
        
        self.chat_service.send_get_user_chats_request(self.current_username)

    def on_block_status_received(self, payload: dict):
        # Sunucudan gelen block yanıtını işle
        blocked_id = payload.get("blocked_id")
        is_blocked = payload.get("is_blocked")
        
        # UI'daki tüm açık sohbetleri tara ve bu kullanıcıya aitse güncelle
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if getattr(widget, 'other_user_id', None) == str(blocked_id):
                self.update_block_ui_elements(getattr(widget, 'contact_name', ""), is_blocked)
                break

    def handle_block_user(self, contact_name):
        # Sohbet ekranından other_user_id'yi al
        target_widget = None
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if getattr(widget, 'contact_name', None) == contact_name:
                target_widget = widget
                break
        
        if not target_widget: return
        receiver_id = getattr(target_widget, 'other_user_id', None)
        if not receiver_id:
            QMessageBox.warning(self.main_page, "Hata", "Kullanıcı bilgisi bulunamadı.")
            return

        is_currently_blocked = (target_widget.block_action.text() == "🔓 Engeli Kaldır")
        
        if is_currently_blocked:
            # Engel kaldır
            self.block_service.send_unblock_user_request(self.current_user_id, receiver_id)
        else:
            # Engelle
            reply = QMessageBox.question(self.main_page, 'Kişiyi Engelle', f"{contact_name} engellensin mi?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.block_service.send_block_user_request(self.current_user_id, receiver_id)

    def update_block_ui_elements(self, contact_name, is_blocked):
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if getattr(widget, 'contact_name', None) == contact_name:
                if hasattr(widget, 'block_action'):
                    text = "🔓 Engeli Kaldır" if is_blocked else "🚫 Kişiyi Engelle"
                    widget.block_action.setText(text)
                break

    def load_user_chats(self, chats: list):
        for chat in chats:
            chat_id = chat.get("chat_id")
            chat_name = chat.get("chat_name", chat_id)
            other_user_id = chat.get("other_user_id")
            block_status = chat.get("block_status", "none")
            
            # Add chat to UI
            self.main_page.add_new_chat_to_ui(chat_name)
            
            # Widget'a ID ve block bilgisini göm
            for i in range(self.main_page.chat_screens_stack.count()):
                widget = self.main_page.chat_screens_stack.widget(i)
                if getattr(widget, 'contact_name', None) == chat_name:
                    widget.other_user_id = str(other_user_id) if other_user_id else None
                    if block_status == "blocked_by_me":
                        widget.block_action.setText("🔓 Engeli Kaldır")
                    else:
                        widget.block_action.setText("🚫 Kişiyi Engelle")
                    break

            # Yükleme işlemi message_controller'a devrediliyor
            self.message_controller.load_historical_messages(chat_name, chat_id, chat.get("messages", []))
            self.loaded_chats.add(chat_id)

    def handle_search(self, query: str):
        self.chat_service.send_search_request(query, self.current_username or "")

    def handle_start_chat(self, target_username: str):
        self.main_page.search_input.clear()
        self.main_page.clear_search_results()

        already_exists = False
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if hasattr(widget, 'contact_name') and widget.contact_name == target_username:
                already_exists = True
                break

        if already_exists:
            print(f"[BİLGİ] {target_username} ile sohbet zaten yüklü.")
        else:
            print(f"[SİSTEM] {target_username} için ID isteniyor...")
            self.chat_service.send_create_chat_request(target_username, self.current_username)

    def on_chat_created(self, payload: dict):
        if payload.get("status") == "success":
            chat_id = payload.get("chat_id")
            target_name = payload.get("target_username")
            
            self.main_page.add_new_chat_to_ui(target_name)
            
            for i in range(self.main_page.chat_screens_stack.count()):
                widget = self.main_page.chat_screens_stack.widget(i)
                if hasattr(widget, 'contact_name') and widget.contact_name == target_name:
                    widget.current_chat_id = chat_id 
                    break

    # TAMAMEN YENİ FONKSİYON
    def handle_delete_chat(self, chat_name: str):
        chat_id = None
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if getattr(widget, 'contact_name', None) == chat_name:
                chat_id = getattr(widget, 'current_chat_id', None)
                break

        if not chat_id:
            self.main_page.remove_chat_from_ui(chat_name)
            return

        self.chat_service.send_delete_chat_request(chat_id, chat_name)

    # TAMAMEN YENİ FONKSİYON
    def on_chat_deleted(self, payload: dict):
        status = payload.get("status")
        chat_name = payload.get("chat_name")

        if status == "success" and chat_name:
            self.main_page.remove_chat_from_ui(chat_name)
        else:
            QMessageBox.warning(self.main_page, "Hata", "Sohbet silinemedi.")

    def handle_delete_account(self):
        # LogRegService üzerinden sunucuya istek gönder
        self.chat_service.client.send_data({
            "type": "delete_account_request",
            "payload": {"username": self.current_username, "user_id": self.current_user_id}
        })
from PyQt5.QtWidgets import QMessageBox
from database import block_repository
from services.block_service import BlockService

class ChatController():
    def __init__(self, main_page, chat_service, message_controller, block_service = None):
        self.block_repo = block_repository
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
        
        # Service signals
        self.chat_service.user_chats_loaded_signal.connect(self.load_user_chats)
        self.chat_service.search_results_signal.connect(self.main_page.show_search_results)
        self.chat_service.create_chat_response_signal.connect(self.on_chat_created)

    def set_current_user(self, profile: dict):
        self.current_user_id = profile.get("user_id")
        self.current_username = profile.get("username")
        
        self.chat_service.send_get_user_chats_request(self.current_username)

    def get_receiver_id_from_name(self, username):
        try:
            from database import user_repository
            users = user_repository.get_all_users()

            if not users:
                print("[DEBUG] users.json boş veya okunamadı!")
                return None

            for user_data in users:
                current_username = str(user_data.get("username", "")).strip().lower()
                target_username = str(username).strip().lower()

                if current_username == target_username:
                    return user_data.get("user_id")

        except Exception as e:
            print(f"[ERROR] get_receiver_id_from_name hatası: {e}")

        return None

    def handle_block_user(self, contact_name):
        receiver_id = self.get_receiver_id_from_name(contact_name)
        if not receiver_id: return

        status = self.block_repo.check_block_status(self.current_user_id, receiver_id)

        is_currently_blocked = (status == "blocked_by_me")
        new_status = not is_currently_blocked

        self.block_repo.add_or_update_block(self.current_user_id, receiver_id, status=new_status)

        if self.block_service:
            if new_status:
                self.block_service.send_block_user_request(self.current_user_id, receiver_id)
            else:
                self.block_service.send_unblock_user_request(self.current_user_id, receiver_id)

        self.update_block_ui_elements(contact_name, new_status)

        msg = "Engel kaldırıldı." if is_currently_blocked else "Kullanıcı engellendi."
        QMessageBox.information(self.main_page, "Bilgi", msg)

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
            
            # Add chat to UI
            self.main_page.add_new_chat_to_ui(chat_name)
            # Yükleme işlemi message_controller'a devrediliyor
            self.message_controller.load_historical_messages(chat_name, chat_id, chat.get("messages", []))
            self.loaded_chats.add(chat_id)

            receiver_id = self.get_receiver_id_from_name(chat_name)
            if receiver_id:
                status = self.block_repo.check_block_status(self.current_user_id, receiver_id)
                # menu yazısı gunceller
                for i in range(self.main_page.chat_screens_stack.count()):
                    widget = self.main_page.chat_screens_stack.widget(i)
                    if getattr(widget, 'contact_name', None) == chat_name:
                        if hasattr(widget, 'block_action'):
                            if status == "blocked_by_me":
                                widget.block_action.setText("🔓 Engeli Kaldır")
                            else:
                                widget.block_action.setText("🚫 Kişiyi Engelle")
                        break

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
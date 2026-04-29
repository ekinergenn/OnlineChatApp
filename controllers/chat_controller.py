from PyQt5.QtWidgets import QMessageBox

class ChatController():
    def __init__(self, main_page, chat_service):
        self.main_page = main_page
        self.chat_service = chat_service
        self.current_user_id = None
        self.current_username = None
        self.loaded_chats = set()

        # Signal connections
        self.main_page.send_message_signal.connect(self.handle_send_message)
        self.main_page.search_query_signal.connect(self.handle_search)
        self.main_page.start_chat_signal.connect(self.handle_start_chat)
        self.main_page.load_history_signal.connect(self.handle_chat_switched)
        
        # Service signals
        self.chat_service.receive_message_signal.connect(self.on_message_received)
        self.chat_service.user_chats_loaded_signal.connect(self.load_user_chats)
        self.chat_service.search_results_signal.connect(self.main_page.show_search_results)
        self.chat_service.create_chat_response_signal.connect(self.on_chat_created)

    def set_current_user(self, profile: dict):
        self.current_user_id = profile.get("user_id")
        self.current_username = profile.get("username")
        
        self.chat_service.send_get_user_chats_request(self.current_username)

    def handle_send_message(self, chat_name, text):
        # Arayüzden o sohbetin gerçek chat_id'sini bul
        actual_chat_id = None
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if hasattr(widget, 'contact_name') and widget.contact_name == chat_name:
                actual_chat_id = getattr(widget, 'current_chat_id', chat_name)
                break

        self.chat_service.send_chat_message(
            chat_id=actual_chat_id, # Artık 'chat_12345' gibi gerçek ID gidiyor[cite: 1]
            content=text,
            sender_id=self.current_user_id or 1,
            sender=self.current_username or ""
        )

    def on_message_received(self, payload: dict):
        chat_id = payload.get("chat_id")
        content = payload.get("content")
        sender = payload.get("sender")
        status = payload.get("status", "delivered")
        message_id = payload.get("message_id")

        is_mine = (sender == self.current_username)
        
        chat_name = chat_id
        target_widget = None
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if getattr(widget, 'current_chat_id', None) == chat_id:
                chat_name = getattr(widget, 'contact_name', chat_id)
                target_widget = widget
                break
                
        self.main_page.add_message_to_ui(chat_name, content, is_mine, status)
        
        if not is_mine:
            # Check if chat is currently active
            current_index = self.main_page.main_stack.currentIndex() # 0 is chats_page
            is_active = False
            
            if current_index == 0:
                active_widget = self.main_page.chat_screens_stack.currentWidget()
                if getattr(active_widget, 'current_chat_id', None) == chat_id:
                    is_active = True
            
            if is_active and message_id:
                self.chat_service.send_mark_as_read(chat_id, [message_id], self.current_username)
            else:
                for i in range(self.main_page.scroll_layout.count()):
                    item = self.main_page.scroll_layout.itemAt(i)
                    if item and item.widget():
                        w = item.widget()
                        if getattr(w, 'contact_name', None) == chat_name:
                            current_count = getattr(w, 'unread_count', 0)
                            self.main_page.update_chat_unread_count(chat_name, current_count + 1)
                            break
                if target_widget and message_id:
                    if not hasattr(target_widget, 'unread_message_ids'):
                        target_widget.unread_message_ids = []
                    target_widget.unread_message_ids.append(message_id)

    def load_user_chats(self, chats: list):
        for chat in chats:
            chat_id = chat.get("chat_id")
            chat_name = chat.get("chat_name", chat_id)
            
            # Add chat to UI
            self.main_page.add_new_chat_to_ui(chat_name)
            
            unread_count = 0
            
            for i in range(self.main_page.chat_screens_stack.count()):
                widget = self.main_page.chat_screens_stack.widget(i)
                if hasattr(widget, 'contact_name') and widget.contact_name == chat_name:
                    widget.current_chat_id = chat_id
                    widget.messages_data = chat.get("messages", [])
                    break
            
            # Load historical messages
            for message in chat.get("messages", []):
                sender = message.get("sender")
                is_mine = (sender == self.current_username)
                
                if not is_mine and self.current_username not in message.get("read_by", []):
                    unread_count += 1
                
                self.main_page.add_message_to_ui(chat_name, message.get("content"), is_mine, message.get("status", "read"))
            
            self.main_page.update_chat_unread_count(chat_name, unread_count)
            self.loaded_chats.add(chat_id)

    def handle_chat_switched(self, chat_name: str):
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if getattr(widget, 'contact_name', None) == chat_name:
                chat_id = getattr(widget, 'current_chat_id', None)
                if not chat_id: break
                
                unread_ids = getattr(widget, 'unread_message_ids', [])
                
                messages_data = getattr(widget, 'messages_data', [])
                for msg in messages_data:
                    if self.current_username not in msg.get("read_by", []) and msg.get("sender") != self.current_username:
                        msg_id = msg.get("message_id")
                        if msg_id and msg_id not in unread_ids:
                            unread_ids.append(msg_id)
                            msg.setdefault("read_by", []).append(self.current_username)
                            
                if unread_ids:
                    self.chat_service.send_mark_as_read(chat_id, unread_ids, self.current_username)
                    widget.unread_message_ids = []
                
                self.main_page.update_chat_unread_count(chat_name, 0)
                break

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
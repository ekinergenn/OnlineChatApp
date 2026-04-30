class MessageController():
    def __init__(self, main_page, message_service):
        self.main_page = main_page
        self.message_service = message_service
        self.current_user_id = None
        self.current_username = None

        # Signal connections
        self.main_page.send_message_signal.connect(self.handle_send_message)
        self.main_page.load_history_signal.connect(self.handle_chat_switched)
        
        # Service signals
        self.message_service.receive_message_signal.connect(self.on_message_received)
        self.message_service.messages_read_receipt_signal.connect(self.on_messages_read_receipt)

    def set_current_user(self, profile: dict):
        self.current_user_id = profile.get("user_id")
        self.current_username = profile.get("username")

    def handle_send_message(self, chat_name, text):
        actual_chat_id = None
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if hasattr(widget, 'contact_name') and widget.contact_name == chat_name:
                actual_chat_id = getattr(widget, 'current_chat_id', chat_name)
                break
                
        self.message_service.send_chat_message(
            chat_id=actual_chat_id,
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

        # 1. Önce Chat ID'ye göre sohbeti arayüzde bulmaya çalış
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if getattr(widget, 'current_chat_id', None) == chat_id:
                chat_name = getattr(widget, 'contact_name', chat_id)
                target_widget = widget
                break

        # 2. Eğer Chat ID ile bulamadıysak (Yani sohbet arayüzde ID olarak henüz tanımlı değilse)
        if target_widget is None:
            # İsim belirleme
            if not is_mine:
                chat_name = sender  # Karşı taraf attıysa, isim onun adıdır.
            else:
                # Biz attıysak ama ID eşleşmediyse (Yeni sohbet):
                # Ya backend'den gelen target_username'i çekeriz, ya da şu an açık olan aktif sekmedeki ismi alırız.
                chat_name = payload.get("target_username")
                if not chat_name:
                    active_w = self.main_page.chat_screens_stack.currentWidget()
                    if hasattr(active_w, 'contact_name'):
                        chat_name = active_w.contact_name

            # Belirlediğimiz isimle arayüzdeki sohbeti isim üzerinden tekrar arayalım
            for i in range(self.main_page.chat_screens_stack.count()):
                w = self.main_page.chat_screens_stack.widget(i)
                if hasattr(w, 'contact_name') and w.contact_name == chat_name:
                    target_widget = w
                    target_widget.current_chat_id = chat_id  # ID'yi ilk defa burada eşleştiriyoruz
                    if not hasattr(target_widget, 'messages_data'):
                        target_widget.messages_data = []
                    break

            # 3. Hala bulamadıysak (Gerçekten ilk defa mesajlaşıyorsak ve sekme hiç yoksa)
            if target_widget is None:
                self.main_page.add_new_chat_to_ui(chat_name)
                for i in range(self.main_page.chat_screens_stack.count()):
                    w = self.main_page.chat_screens_stack.widget(i)
                    if hasattr(w, 'contact_name') and w.contact_name == chat_name:
                        w.current_chat_id = chat_id
                        w.messages_data = []
                        target_widget = w
                        break

        # 4. Kendi adımızı read_by listesinden çıkaralım (Mavi tik hatasını önlemek için)
        actual_read_by = [u for u in payload.get("read_by", []) if u != self.current_username]

        # 5. Mesajı arayüze ekle
        self.main_page.add_message_to_ui(chat_name, content, is_mine, status, read_by=actual_read_by,
                                         message_id=message_id, timestamp=payload.get("timestamp"))

        # 6. Okunmamış mesaj sayısı ve "Görüldü" gönderme işlemleri (Sadece karşıdan gelen mesajlar için)
        if not is_mine:
            # Chat şu an aktif ekranda mı kontrol et
            current_index = self.main_page.main_stack.currentIndex()
            is_active = False

            if current_index == 0:
                active_widget = self.main_page.chat_screens_stack.currentWidget()
                if getattr(active_widget, 'current_chat_id', None) == chat_id:
                    is_active = True

            if is_active and message_id:
                # Ekrandaysa anında okundu bilgisi gönder
                self.message_service.send_mark_as_read(chat_id, [message_id], self.current_username)
            else:
                # Ekranda değilse sol paneldeki okunmamış sayısını arttır
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

    def load_historical_messages(self, chat_name: str, chat_id: str, messages: list):
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if hasattr(widget, 'contact_name') and widget.contact_name == chat_name:
                widget.current_chat_id = chat_id
                widget.messages_data = messages
                break

        unread_count = 0
        for message in messages:
            sender = message.get("sender")
            is_mine = (sender == self.current_username)

            if not is_mine and self.current_username not in message.get("read_by", []):
                unread_count += 1

            # Kendi adımızı read_by listesinden çıkarıyoruz
            actual_read_by = [u for u in message.get("read_by", []) if u != self.current_username]

            # Varsayılan durumu "read" yerine "delivered" yapıyoruz
            self.main_page.add_message_to_ui(chat_name, message.get("content"), is_mine,
                                             message.get("status", "delivered"), read_by=actual_read_by,
                                             timestamp=message.get("timestamp"))
        
        self.main_page.update_chat_unread_count(chat_name, unread_count)

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
                    self.message_service.send_mark_as_read(chat_id, unread_ids, self.current_username)
                    widget.unread_message_ids = []
                
                self.main_page.update_chat_unread_count(chat_name, 0)
                break

    def on_messages_read_receipt(self, payload: dict):
        chat_id = payload.get("chat_id")
        message_ids = payload.get("message_ids", [])

        # chat_id'den chat_name bul
        chat_name = chat_id
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if getattr(widget, 'current_chat_id', None) == chat_id:
                chat_name = getattr(widget, 'contact_name', chat_id)
                break

        self.main_page.update_message_read_status(chat_name, message_ids, payload.get("read_by", ""))

from PyQt5.QtCore import QTimer


class MessageController:
    def __init__(self, main_page, message_service, encryption_service=None):
        self.main_page = main_page
        self.message_service = message_service
        self.encryption_service = encryption_service
        self.current_user_id = None
        self.current_username = None

        # Anahtar hazır olana kadar bekleyen mesajlar: [{chat_name, text, chat_id}]
        self._pending_messages = []

        self._typing_timers = {}

        # UI sinyalleri
        self.main_page.send_message_signal.connect(self.handle_send_message)
        self.main_page.load_history_signal.connect(self.handle_chat_switched)
        self.main_page.typing_signal.connect(self.handle_typing)

        # Servis sinyalleri
        self.message_service.receive_message_signal.connect(self.on_message_received)
        self.message_service.messages_read_receipt_signal.connect(self.on_messages_read_receipt)
        self.message_service.typing_indicator_signal.connect(self.on_typing_indicator_received)

        # E2EE: Anahtar hazır olduğunda bekleyen mesajları gönder
        if self.encryption_service:
            self.encryption_service.public_key_fetched_signal.connect(self._on_public_key_fetched)

    def set_current_user(self, profile: dict):
        self.current_user_id = profile.get("user_id")
        self.current_username = profile.get("username")

    def reset_user_data(self):
        """Oturum kapatıldığında state'i temizler."""
        self.current_user_id = None
        self.current_username = None
        self._pending_messages = []
        for timer in self._typing_timers.values():
            timer.stop()
        self._typing_timers = {}
        print("[CONTROLLER] MessageController sıfırlandı.")

    # ───────────────────────── TYPING ─────────────────────────────────────────

    def handle_typing(self, chat_name: str, is_typing: bool):
        chat_id = None
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if getattr(widget, 'contact_name', None) == chat_name:
                chat_id = getattr(widget, 'current_chat_id', None)
                break
        if chat_id and self.current_username:
            self.message_service.send_typing_indicator(chat_id, self.current_username, is_typing)

    def on_typing_indicator_received(self, payload: dict):
        chat_id = payload.get("chat_id")
        sender = payload.get("sender")
        is_typing = payload.get("is_typing", False)

        chat_name = chat_id
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if getattr(widget, 'current_chat_id', None) == chat_id:
                chat_name = getattr(widget, 'contact_name', chat_id)
                break

        if is_typing:
            self.main_page.show_typing_indicator(chat_name, sender)
            if chat_id in self._typing_timers:
                self._typing_timers[chat_id].stop()
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self.main_page.hide_typing_indicator(chat_name))
            timer.start(5000)
            self._typing_timers[chat_id] = timer
        else:
            if chat_id in self._typing_timers:
                self._typing_timers[chat_id].stop()
                del self._typing_timers[chat_id]
            self.main_page.hide_typing_indicator(chat_name)

    # ───────────────────────── MESAJ GÖNDERME ─────────────────────────────────

    def handle_send_message(self, chat_name: str, text: str):
        actual_chat_id = None
        is_group = False
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if hasattr(widget, 'contact_name') and widget.contact_name == chat_name:
                actual_chat_id = getattr(widget, 'current_chat_id', None)
                is_group = getattr(widget, 'is_group', False)
                break

        if not actual_chat_id:
            print(f"[HATA] '{chat_name}' için chat_id bulunamadı, mesaj gönderilemez!")
            return

        if is_group and self.encryption_service:
            # Grup E2EE: Tüm üyelerin anahtarlarını topla
            widget_ref = None
            for i in range(self.main_page.chat_screens_stack.count()):
                w = self.main_page.chat_screens_stack.widget(i)
                if hasattr(w, 'contact_name') and w.contact_name == chat_name:
                    widget_ref = w
                    break

            members = getattr(widget_ref, 'members', []) if widget_ref else []
            other_members = [m for m in members if m != self.current_username]

            if self.encryption_service.all_group_keys_ready(other_members):
                # Tüm anahtarlar hazır: şifrele ve gönder
                recipient_keys = {m: self.encryption_service.public_keys[m] for m in other_members}
                recipient_keys[self.current_username] = self.encryption_service.get_public_key_pem()
                encrypted_data = self.encryption_service.encrypt_message(text, recipient_keys)
                if encrypted_data:
                    self.message_service.send_chat_message(
                        chat_id=actual_chat_id,
                        content="[Şifreli Mesaj]",
                        sender_id=self.current_user_id or 1,
                        sender=self.current_username or "",
                        encrypted_data=encrypted_data
                    )
                else:
                    print("[GRUP E2EE] Şifreleme başarısız.")
            else:
                # Eksik anahtarlar var: beklet ve çek
                missing = [m for m in other_members if m not in self.encryption_service.public_keys]
                print(f"[GRUP E2EE] Eksik anahtarlar: {missing}, mesaj beklemeye alındı.")
                self._pending_messages.append({
                    "chat_name": chat_name,
                    "text": text,
                    "chat_id": actual_chat_id,
                    "group_members": other_members
                })
                self.encryption_service.fetch_missing_group_keys(other_members)
            return

        if not self.encryption_service:
            # Şifreleme yoksa düz gönder
            self.message_service.send_chat_message(
                chat_id=actual_chat_id,
                content=text,
                sender_id=self.current_user_id or 1,
                sender=self.current_username or ""
            )
            return

        # 1-1 sohbet: E2EE ile şifrele
        recipient = chat_name
        recipient_pub_key = self.encryption_service.public_keys.get(recipient)
        my_pub_key = self.encryption_service.get_public_key_pem()

        if recipient_pub_key and my_pub_key:
            # Her iki taraf için de şifrele (gönderen geçmişi okuyabilsin)
            recipient_keys = {
                recipient: recipient_pub_key,
                self.current_username: my_pub_key
            }
            encrypted_data = self.encryption_service.encrypt_message(text, recipient_keys)
            if encrypted_data:
                self.message_service.send_chat_message(
                    chat_id=actual_chat_id,
                    content="[Şifreli Mesaj]",  # Sunucu bu içeriği görür
                    sender_id=self.current_user_id or 1,
                    sender=self.current_username or "",
                    encrypted_data=encrypted_data
                )
            else:
                print("[HATA] Şifreleme başarısız, mesaj gönderilmedi.")
        else:
            # Anahtar henüz yok: mesajı beklet ve anahtarı sun
            print(f"[E2EE] {recipient} için anahtar bulunamadı, isteniyor ve mesaj beklemeye alındı.")
            self._pending_messages.append({
                "chat_name": chat_name,
                "text": text,
                "chat_id": actual_chat_id
            })
            if not recipient_pub_key:
                self.encryption_service.send_get_public_key_request(recipient)

    def _on_public_key_fetched(self, data: dict):
        """Beklenen anahtar gelince bekleyen mesajları gönder."""
        username = data.get("username")
        for msg in list(self._pending_messages):
            group_members = msg.get("group_members")

            if group_members:
                # Grup mesajı: tüm üyelerin anahtarları geldi mi kontrol et
                if self.encryption_service and self.encryption_service.all_group_keys_ready(group_members):
                    self._pending_messages.remove(msg)
                    self.handle_send_message(msg["chat_name"], msg["text"])
            else:
                # 1-1 mesaj: hedef kişinin anahtarı geldiyse gönder
                if msg["chat_name"] == username:
                    self._pending_messages.remove(msg)
                    self.handle_send_message(msg["chat_name"], msg["text"])

    # ───────────────────────── MESAJ ALMA ─────────────────────────────────────

    def on_message_received(self, payload: dict):
        chat_id = payload.get("chat_id")
        content = payload.get("content")
        sender = payload.get("sender")
        status = payload.get("status", "delivered")
        message_id = payload.get("message_id")

        is_mine = (sender == self.current_username)

        # E2EE: Şifreli içeriği çöz
        encrypted_data = payload.get("encrypted_data")
        if encrypted_data and self.encryption_service:
            decrypted = self.encryption_service.decrypt_message(encrypted_data, self.current_username)
            content = decrypted if decrypted else "[Şifre Çözülemedi]"

        chat_name = chat_id
        target_widget = None

        # 1. Chat ID ile widget bul
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if getattr(widget, 'current_chat_id', None) == chat_id:
                chat_name = getattr(widget, 'contact_name', chat_id)
                target_widget = widget
                break

        # 2. Chat ID yoksa isimle bul
        if target_widget is None:
            if not is_mine:
                chat_name = sender
            else:
                chat_name = payload.get("target_username")
                if not chat_name:
                    active_w = self.main_page.chat_screens_stack.currentWidget()
                    if hasattr(active_w, 'contact_name'):
                        chat_name = active_w.contact_name

            for i in range(self.main_page.chat_screens_stack.count()):
                w = self.main_page.chat_screens_stack.widget(i)
                if hasattr(w, 'contact_name') and w.contact_name == chat_name:
                    target_widget = w
                    target_widget.current_chat_id = chat_id
                    if not hasattr(target_widget, 'messages_data'):
                        target_widget.messages_data = []
                    break

            # 3. Hâlâ yok: yeni sekme aç
            if target_widget is None:
                self.main_page.add_new_chat_to_ui(chat_name)
                for i in range(self.main_page.chat_screens_stack.count()):
                    w = self.main_page.chat_screens_stack.widget(i)
                    if hasattr(w, 'contact_name') and w.contact_name == chat_name:
                        w.current_chat_id = chat_id
                        w.messages_data = []
                        target_widget = w
                        break

        # 4. Kendi read_by'ı temizle
        actual_read_by = [u for u in payload.get("read_by", []) if u != self.current_username]

        # 5. Grup mı?
        is_group = False
        for i in range(self.main_page.chat_screens_stack.count()):
            w = self.main_page.chat_screens_stack.widget(i)
            if getattr(w, 'current_chat_id', None) == chat_id or getattr(w, 'contact_name', None) == chat_name:
                is_group = getattr(w, 'is_group', False)
                break

        # 6. UI'a ekle (duplicate kontrolü mainPage içinde yapılıyor)
        self.main_page.add_message_to_ui(
            chat_name, content, is_mine, status,
            read_by=actual_read_by,
            message_id=message_id,
            timestamp=payload.get("timestamp"),
            sender_name=sender if (is_group and not is_mine) else None
        )

        # 7. Okundu durumu
        if not is_mine:
            current_index = self.main_page.main_stack.currentIndex()
            is_active = False
            if current_index == 0:
                active_widget = self.main_page.chat_screens_stack.currentWidget()
                if getattr(active_widget, 'current_chat_id', None) == chat_id:
                    is_active = True

            if is_active and message_id:
                self.message_service.send_mark_as_read(chat_id, [message_id], self.current_username)
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

    # ───────────────────────── GEÇMİŞ MESAJLAR ───────────────────────────────

    def load_historical_messages(self, chat_name: str, chat_id: str, messages: list):
        is_group = False
        for i in range(self.main_page.chat_screens_stack.count()):
            w = self.main_page.chat_screens_stack.widget(i)
            if getattr(w, 'contact_name', None) == chat_name:
                is_group = getattr(w, 'is_group', False)
                break

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

            actual_read_by = [u for u in message.get("read_by", []) if u != self.current_username]

            # E2EE: Geçmiş şifreli mesajları çöz
            content = message.get("content")
            encrypted_data = message.get("encrypted_data")
            if encrypted_data and self.encryption_service:
                decrypted = self.encryption_service.decrypt_message(encrypted_data, self.current_username)
                content = decrypted if decrypted else "[Şifre Çözülemedi]"

            self.main_page.add_message_to_ui(
                chat_name, content, is_mine,
                message.get("status", "delivered"),
                read_by=actual_read_by,
                timestamp=message.get("timestamp"),
                sender_name=message.get("sender") if (is_group and not is_mine) else None
            )

        self.main_page.update_chat_unread_count(chat_name, unread_count)

    # ───────────────────────── SOHBET DEĞİŞTİ ────────────────────────────────

    def handle_chat_switched(self, chat_name: str):
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if getattr(widget, 'contact_name', None) == chat_name:
                chat_id = getattr(widget, 'current_chat_id', None)
                if not chat_id:
                    break

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

    # ───────────────────────── OKUNDU MAKBUZİ ────────────────────────────────

    def on_messages_read_receipt(self, payload: dict):
        chat_id = payload.get("chat_id")
        message_ids = payload.get("message_ids", [])

        chat_name = chat_id
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if getattr(widget, 'current_chat_id', None) == chat_id:
                chat_name = getattr(widget, 'contact_name', chat_id)
                break

        self.main_page.update_message_read_status(chat_name, message_ids, payload.get("read_by", ""))

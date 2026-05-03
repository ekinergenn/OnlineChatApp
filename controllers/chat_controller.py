from PyQt5.QtWidgets import QMessageBox
from services.block_service import BlockService


class ChatController():
    def __init__(self, main_page, chat_service, message_controller, block_service=None, chatbot_service=None):
        self.block_service = block_service
        self.main_page = main_page
        self.chat_service = chat_service
        self.message_controller = message_controller
        self.chatbot_service = chatbot_service
        self.current_user_id = None
        self.current_username = None
        self.loaded_chats = set()

        self.init_signals()
        self.connect_ui_signals()

    def init_signals(self):
        """Servislerden gelen sinyalleri bağlar (Sabit bağlantılar)."""
        self.chat_service.user_chats_loaded_signal.connect(self.load_user_chats)
        self.chat_service.search_results_signal.connect(self.main_page.show_search_results)
        self.chat_service.create_chat_response_signal.connect(self.on_chat_created)
        self.chat_service.delete_chat_response_signal.connect(self.on_chat_deleted)
        self.chat_service.user_status_signal.connect(self.on_user_status_received)
        self.chat_service.all_users_loaded_signal.connect(self.on_all_users_loaded)
        self.chat_service.create_group_response_signal.connect(self.on_group_created)
        self.message_controller.message_service.messages_read_receipt_signal.connect(self.on_messages_read_received)
        self.chat_service.privacy_settings_loaded_signal.connect(self.on_privacy_settings_received)
        
        if self.block_service:
            self.block_service.block_status_changed_signal.connect(self.on_block_status_received)
            self.block_service.block_list_loaded_signal.connect(self.on_block_list_loaded)

    def connect_ui_signals(self):
        """UI'dan gelen sinyalleri bağlar (Logout/Login döngüsünde yenilenir)."""
        self.disconnect_ui_signals() # Önce temizle
        
        self.main_page.block_user_signal.connect(self.handle_block_user)
        self.main_page.search_query_signal.connect(self.handle_search)
        self.main_page.start_chat_signal.connect(self.handle_start_chat)
        self.main_page.delete_chat_signal.connect(self.handle_delete_chat)
        self.main_page.profile_page.delete_account_signal.connect(self.handle_delete_account)
        self.main_page.load_history_signal.connect(self.handle_chat_opened)
        self.main_page.request_blocked_users_signal.connect(self.handle_request_blocked_users)
        self.main_page.unblock_user_from_settings_signal.connect(self.handle_unblock_from_settings)
        self.main_page.request_all_users_signal.connect(self.handle_request_all_users)
        self.main_page.create_group_signal.connect(self.handle_create_group)
        self.main_page.profile_page.update_profile_signal.connect(self.handle_update_profile)
        self.main_page.leave_group_signal.connect(self.handle_leave_group)
        self.main_page.update_privacy_settings_signal.connect(self.handle_update_privacy)
        self.main_page.get_privacy_settings_signal.connect(self.handle_get_privacy)
        self.main_page.mark_messages_read_signal.connect(self.handle_mark_messages_read)

    def disconnect_ui_signals(self):
        """UI sinyal bağlantılarını güvenli bir şekilde koparır."""
        try:
            self.main_page.block_user_signal.disconnect()
            self.main_page.search_query_signal.disconnect()
            self.main_page.start_chat_signal.disconnect()
            self.main_page.delete_chat_signal.disconnect()
            self.main_page.load_history_signal.disconnect()
            self.main_page.request_blocked_users_signal.disconnect()
            self.main_page.unblock_user_from_settings_signal.disconnect()
            self.main_page.request_all_users_signal.disconnect()
            self.main_page.create_group_signal.disconnect()
            self.main_page.profile_page.update_profile_signal.disconnect()
            self.main_page.profile_page.delete_account_signal.disconnect()
            self.main_page.update_privacy_settings_signal.disconnect()
            self.main_page.get_privacy_settings_signal.disconnect()
        except:
            pass

    def handle_chat_opened(self, chat_name: str):
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)

            if getattr(widget, 'contact_name', None) == chat_name:
                chat_id = getattr(widget, 'current_chat_id', None)
                is_group = getattr(widget, 'is_group', False)
                enc = getattr(self.message_controller, 'encryption_service', None)

                # --- 1. KOŞULLU YÜKLEME (DÖNGÜYÜ KIRAN KISIM) ---
                # Mesaj sayısını kontrol edelim. Sadece stretch varsa (count <= 1) sunucudan isteyelim.
                # Böylece mesajlar zaten ekrandaysa tekrar istek atıp UI'ı tazelemeyiz.
                if hasattr(widget, 'msg_layout'):
                    msg_count = widget.msg_layout.count()
                    if msg_count <= 1 and self.current_username:
                        print(f"[DEBUG] {chat_name} boş görünüyor, geçmiş yükleniyor...")
                        self.chat_service.send_get_user_chats_request(self.current_username)

                # --- 2. DURUM VE ANAHTAR İŞLEMLERİ (Sessiz Çalışır) ---
                if not is_group and chat_name != "__chatbot__":
                    from PyQt5.QtCore import QTimer
                    # Timer kullanımı UI'ın donmasını engeller
                    QTimer.singleShot(150, lambda u=chat_name: self.chat_service.send_get_user_status_request(u))

                    if enc:
                        QTimer.singleShot(250, lambda u=chat_name: enc.send_get_public_key_request(u))

                elif is_group and enc:
                    members = getattr(widget, 'members', [])
                    other_members = [m for m in members if m != self.current_username]
                    if other_members:
                        from PyQt5.QtCore import QTimer
                        QTimer.singleShot(250, lambda m=other_members: enc.fetch_missing_group_keys(m))

                # --- 3. UI KONTROL ---
                widget.update()
                break

    def set_current_user(self, profile: dict):
        self.current_user_id = profile.get("user_id")
        self.current_username = profile.get("username")
        
        # Gizlilik ayarlarını da çek
        self.chat_service.send_get_privacy_settings(self.current_username)
        self.chat_service.send_get_user_chats_request(self.current_username)

    def on_user_status_received(self, payload: dict):
        """Online/offline durumunu sohbet ekranının üst barına yansıtır."""
        username = payload.get("username")
        status = payload.get("status")  # "online" | "offline"
        last_seen_ts = payload.get("last_seen")

        self.main_page.update_chat_status_bar(username, status, last_seen_ts)

    def on_block_status_received(self, payload: dict):
        # Sunucudan gelen detaylı block durumunu işle
        blocked_id = payload.get("blocked_id")
        block_status = payload.get("block_status") # "none", "blocked_by_me", "blocked_by_them", "both"

        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if getattr(widget, 'other_user_id', None) == str(blocked_id):
                self.update_block_ui_elements(getattr(widget, 'contact_name', ""), block_status)
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

    def handle_request_blocked_users(self):
        if self.block_service and self.current_user_id:
            self.block_service.send_get_block_list_request(self.current_user_id)

    def on_block_list_loaded(self, blocks: list):
        if hasattr(self.main_page, 'settings_page'):
            self.main_page.settings_page.load_blocked_users(blocks)

    def handle_unblock_from_settings(self, blocked_id_str):
        if self.block_service and self.current_user_id:
            self.block_service.send_unblock_user_request(self.current_user_id, int(blocked_id_str))
            # Also request updated list
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(200, self.handle_request_blocked_users)

    def update_block_ui_elements(self, contact_name, block_status):
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            if getattr(widget, 'contact_name', None) == contact_name:
                
                is_blocked_by_me = (block_status == "blocked_by_me" or block_status == "both")
                is_blocked_by_them = (block_status == "blocked_by_them" or block_status == "both")
                any_block = (block_status != "none")

                # 1. Menü metnini güncelle (Kişiyi engellediysem "Engeli Kaldır" yazsın)
                if hasattr(widget, 'block_action'):
                    text = "🔓 Engeli Kaldır" if is_blocked_by_me else "🚫 Kişiyi Engelle"
                    widget.block_action.setText(text)
                
                # 2. Mesaj giriş alanlarını kapat/aç ve metni ayarla
                if hasattr(widget, 'msg_input'):
                    widget.msg_input.setEnabled(not any_block)
                    
                    if block_status == "blocked_by_me":
                        placeholder = "Bu kişiyi engellediniz."
                    elif block_status == "blocked_by_them":
                        placeholder = "Bu kişi sizi engellemiş."
                    elif block_status == "both":
                        placeholder = "Karşılıklı engelleme mevcut."
                    else:
                        placeholder = "Bir mesaj yazın"
                    
                    widget.msg_input.setPlaceholderText(placeholder)
                
                if hasattr(widget, 'send_btn'):
                    widget.send_btn.setEnabled(not any_block)
                if hasattr(widget, 'attach_btn'):
                    widget.attach_btn.setEnabled(not any_block)
                
                break

    def load_user_chats(self, chats: list):
        for chat in chats:
            chat_id = chat.get("chat_id")
            chat_name = chat.get("chat_name", chat_id)
            messages = chat.get("messages", [])
            other_user_id = chat.get("other_user_id")
            block_status = chat.get("block_status", "none")
            is_group = chat.get("is_group", False)
            members = chat.get("members", [])  # Grup üyeleri

            # Arayüze sohbet kartını ekle
            self.main_page.add_new_chat_to_ui(chat_name, is_group=is_group)

            # Widget'ı bul ve meta verilerini göm
            for i in range(self.main_page.chat_screens_stack.count()):
                widget = self.main_page.chat_screens_stack.widget(i)
                if getattr(widget, 'contact_name', None) == chat_name:
                    widget.other_user_id = str(other_user_id) if other_user_id else None
                    widget.is_group = is_group
                    widget.members = members

                    # Engelleme durumuna göre UI'ı güncelle (Açılışta yükleme)
                    self.update_block_ui_elements(chat_name, block_status)
                    break

            # 1-1 sohbetlerde kullanıcı durumunu sor (sadece bir kez, dışarıda)
            if not is_group:
                self.chat_service.send_get_user_status_request(chat_name)

            self.message_controller.load_historical_messages(chat_name, chat_id, messages)
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
            other_user_id = payload.get("other_user_id")

            self.main_page.add_new_chat_to_ui(target_name)

            for i in range(self.main_page.chat_screens_stack.count()):
                widget = self.main_page.chat_screens_stack.widget(i)
                if hasattr(widget, 'contact_name') and widget.contact_name == target_name:
                    widget.current_chat_id = chat_id
                    widget.other_user_id = str(other_user_id) if other_user_id else None
                    break

    # TAMAMEN YENİ FONKSİYON
    def handle_delete_chat(self, chat_name: str):
        # İŞTE BURADA ÇAĞIRIYORUZ:
        chat_id = self.get_chat_id_by_name(chat_name)

        if not chat_id:
            # Eğer bellekte ID yoksa (örneğin sadece arama sonucu açılmış ama mesaj atılmamış)
            # sadece arayüzden kaldırıyoruz.
            self.main_page.remove_chat_from_ui(chat_name)
            return

        # ID bulundu, şimdi servise aksiyonu bildiriyoruz
        self.chat_service.send_delete_chat_request(
            chat_id=chat_id,
            chat_name=chat_name,
            username=self.current_username,
            action="delete"  # 'delete' sunucuda hide_group_chat'i tetikler
        )

    def handle_leave_group(self, chat_name: str):
        # İŞTE BURADA ÇAĞIRIYORUZ:
        chat_id = self.get_chat_id_by_name(chat_name)

        if chat_id:
            # Sunucuya aksiyonu 'leave' olarak gönderiyoruz
            self.chat_service.send_delete_chat_request(
                chat_id=chat_id,
                chat_name=chat_name,
                username=self.current_username,
                action="leave"  # 'leave' sunucuda leave_group_chat'i tetikler
            )

    def get_chat_id_by_name(self, chat_name):
        """Arayüzdeki chat_screens_stack içinden isme göre chat_id bulur."""
        for i in range(self.main_page.chat_screens_stack.count()):
            widget = self.main_page.chat_screens_stack.widget(i)
            # Widget'ın ismini kontrol et
            if getattr(widget, 'contact_name', None) == chat_name:
                # O widget'a gömülü olan chat_id'yi al
                chat_id = getattr(widget, 'current_chat_id', None)
                if chat_id:
                    return chat_id

        print(f"[UYARI] '{chat_name}' ismi için chat_id bulunamadı.")
        return None

    # TAMAMEN YENİ FONKSİYON
    def on_chat_deleted(self, payload: dict):
        status = payload.get("status")
        chat_name = payload.get("chat_name")
        action = payload.get("action")

        if status == "success" and chat_name:
            # Arayüzden kaldır (Hem gizlemede hem ayrılmada UI'dan kalkmalı)
            self.main_page.remove_chat_from_ui(chat_name)

            if action == "leave":
                QMessageBox.information(self.main_page, "Bilgi", f"'{chat_name}' grubundan ayrıldınız.")
        else:
            # QMessageBox.warning(self.main_page, "Hata", "İşlem tamamlanamadı.")
            pass

    def handle_delete_account(self):
        # LogRegService üzerinden sunucuya istek gönder
        self.chat_service.client.send_data({
            "type": "delete_account_request",
            "payload": {"username": self.current_username, "user_id": self.current_user_id}
        })

    def handle_request_all_users(self):
        self.chat_service.send_get_all_users_request(self.current_username or "")

    def on_all_users_loaded(self, users: list):
        from ui.groupDialog import GroupCreationDialog
        dialog = GroupCreationDialog(users, self.current_username, parent=self.main_page)
        dialog.create_group_signal.connect(self.handle_create_group)
        dialog.exec_()

    def handle_create_group(self, group_name: str, selected_members: list):
        all_members = [self.current_username] + selected_members
        self.chat_service.send_create_group_request(group_name, all_members)

    def on_group_created(self, payload: dict):
        if payload.get("status") == "success":
            group_name = payload.get("group_name")
            chat_id = payload.get("chat_id")
            members = payload.get("members", [])
            self.main_page.add_new_chat_to_ui(group_name, is_group=True)
            for i in range(self.main_page.chat_screens_stack.count()):
                widget = self.main_page.chat_screens_stack.widget(i)
                if getattr(widget, 'contact_name', None) == group_name:
                    widget.current_chat_id = chat_id
                    widget.is_group = True
                    widget.members = members
                    break
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.main_page, "Hata", "Grup oluşturulamadı.")

    def handle_update_profile(self, data):
        # Username değişmiyor
        data["username"] = self.current_username
        print(f"[DEBUG] Profil güncelleme isteği gönderiliyor: {data}")

        packet = {
            "type": "update_profile_request",
            "payload": data
        }
        self.chat_service.client.send_data(packet)

    def handle_update_privacy(self, settings):
        if self.current_username:
            self.chat_service.send_update_privacy_settings(self.current_username, settings)

    def handle_get_privacy(self, username):
        self.chat_service.send_get_privacy_settings(username)

    def on_privacy_settings_received(self, settings):
        if hasattr(self.main_page, 'settings_page'):
            self.main_page.settings_page.load_privacy_settings(settings)

    def on_messages_read_received(self, payload):
        chat_id = payload.get("chat_id")
        message_ids = payload.get("message_ids", [])
        read_by = payload.get("read_by")
        all_read = payload.get("all_read", False)
        
        # Arayüzdeki tikleri güncelle
        self.main_page.update_message_read_status(chat_id, message_ids, read_by, all_read)

    def handle_mark_messages_read(self, chat_id, message_ids):
        if self.current_username:
            self.message_controller.message_service.send_mark_as_read(chat_id, message_ids, self.current_username)

    def reset_user_data(self):
        self.current_username = None
        self.current_user_id = None
        self.loaded_chats = set()

        # Sinyal bağlantılarını temizle (Mükerrer UI oluşumunu engellemek için)
        self.disconnect_ui_signals()

        # ChatService temizliği
        if hasattr(self, 'chat_service') and self.chat_service is not None:
            self.chat_service.reset()

        # ChatbotService temizliği
        if hasattr(self, 'chatbot_service') and self.chatbot_service is not None:
            self.chatbot_service.reset_conversation()

        print("[CONTROLLER] Kullanıcı verileri ve sinyal bağlantıları temizlendi.")
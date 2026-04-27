from PyQt5.QtWidgets import QInputDialog, QMessageBox
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QDialogButtonBox, QMessageBox
from PyQt5.QtCore import Qt


class CreateGroupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Grup Oluştur")
        self.setFixedSize(300, 400)
        self.setStyleSheet("background-color: #ffffff;")

        layout = QVBoxLayout(self)

        # 1. Grup Adı Girişi
        self.group_name_input = QLineEdit()
        self.group_name_input.setPlaceholderText("Grup Adı")
        self.group_name_input.setStyleSheet("border: 1px solid #d1d7db; border-radius: 8px; padding: 10px;")
        layout.addWidget(self.group_name_input)

        # 2. Kişi Listesi (Şimdilik örnek isimler)
        self.user_list = QListWidget()
        self.user_list.setStyleSheet("border: 1px solid #d1d7db; border-radius: 8px;")


        # Gerçek uygulamada bu liste sunucudan çekilen arkadaş listesi olmalı
        dummy_friends = ["Ahmet Yılmaz", "Ayşe Kaya", "Mehmet", "Hoca"]

        for friend in dummy_friends:
            item = QListWidgetItem(friend)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)  # Checkbox özelliği ekle
            item.setCheckState(Qt.Unchecked)  # Başlangıçta seçili olmasın
            self.user_list.addItem(item)

        layout.addWidget(self.user_list)

        # 3. İptal ve Tamam Butonları
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_data(self):
        """Pencere kapanınca girilen verileri döndürür."""
        group_name = self.group_name_input.text()
        selected_users = []
        for i in range(self.user_list.count()):
            item = self.user_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_users.append(item.text())
        return group_name, selected_users


class ChatController():
    def __init__(self, main_page, chat_service):
        self.main_page = main_page
        self.chat_service = chat_service
        self.current_user_id = None
        self.current_username = None
        self.loaded_chats = set()

        self.main_page.send_message_signal.connect(self.handle_send_message)
        self.chat_service.receive_message_signal.connect(self.on_message_received)
        self.main_page.load_history_signal.connect(self.load_history_for_chat)
        self.main_page.delete_chat_signal.connect(self.handle_delete_chat)
        self.main_page.block_user_signal.connect(self.handle_block_user)
        self.main_page.search_query_signal.connect(self.handle_search)
        self.main_page.start_chat_signal.connect(self.handle_start_chat)

        # Artı butonuna tıklanma olayını bağla
        self.main_page.add_chat_btn.clicked.connect(self.show_create_group_dialog)

        # Servisten gelecek cevabı bekle
        self.chat_service.create_group_response_signal.connect(self.on_group_created)
        self.chat_service.user_chats_loaded_signal.connect(self.load_user_chats)
        self.chat_service.search_results_signal.connect(self.main_page.show_search_results)

        from PyQt5.QtCore import Qt  # En üste import etmeyi unutma
        self.chat_service.delete_chat_response_signal.connect(self.on_chat_deleted, Qt.QueuedConnection)

    def handle_delete_chat(self, chat_name):
        # Kullanıcı arayüzde 'Evet'e bastığında bu çalışır, servise iletir
        self.chat_service.send_delete_chat_request(chat_name, user_id=1)

    def handle_block_user(self, username):
        QMessageBox.information(self.main_page, "Bilgi", f"'{username}' kişisini engelleme özelliği yakında eklenecek.")

    # chat_controller.py — on_chat_deleted içine ekle
    def on_chat_deleted(self, payload):
        if payload.get("status") == "success":
            chat_name = payload.get("chat_name")
            self.loaded_chats.discard(chat_name)  # ← bunu ekle
            QMessageBox.information(self.main_page, "Başarılı", f"'{chat_name}' sohbeti silindi!")
            self.main_page.remove_chat_from_ui(chat_name)
        else:
            QMessageBox.warning(self.main_page, "Hata", "Sohbet silinemedi.")

    def show_create_group_dialog(self):
        # Kendi tasarladığımız dialog penceresini aç
        dialog = CreateGroupDialog(self.main_page)

        if dialog.exec_():  # Eğer 'OK' tuşuna basıldıysa
            group_name, selected_users = dialog.get_data()

            if group_name and selected_users:
                # Servise grup adını ve seçilen kişileri gönder
                self.chat_service.send_create_group_request(group_name, selected_users, creator_id=1)
            else:
                QMessageBox.warning(self.main_page, "Hata", "Lütfen bir grup adı girin ve en az 1 kişi seçin.")

    def on_group_created(self, payload):
        if payload.get("status") == "success":
            group_name = payload.get("group_name")

            # YENİ: Arayüzdeki listeye dinamik olarak ekle!
            self.main_page.add_new_chat_to_ui(group_name)

            QMessageBox.information(self.main_page, "Başarılı", f"'{group_name}' grubu oluşturuldu!")
        else:
            QMessageBox.warning(self.main_page, "Hata", "Grup oluşturulamadı.")

    def handle_send_message(self, chat_name, text):
        print(f"[DEBUG] Mesaj gönderiliyor: chat_name={chat_name}, text={text}, sender_id={self.current_user_id}")
        # Kullanıcı ID'sini şimdilik sabit "1" veriyoruz, ileride Login'den gelen ID olacak
        self.chat_service.send_chat_message(chat_name, text, sender_id=self.current_user_id or 1, sender=self.current_username or "")

    def on_message_received(self, payload: dict):
        chat_name = payload.get("chat_name")
        content = payload.get("content")
        sender = payload.get("sender")  # ← sender_id yerine sender kullan
        status = payload.get("status", "delivered")
        is_mine = (sender == self.current_username)

        self.main_page.add_message_to_ui(chat_name, content, is_mine, status)

    # chat_controller.py
    def load_history_for_chat(self, chat_name: str):
        if chat_name in self.loaded_chats:
            return

        messages = self.chat_service.load_chat_history(chat_name)
        for msg in messages:
            # Hem sender hem sender_id ile kontrol et (eski mesajlar için fallback)
            is_mine = (
                    msg.get("sender") == self.current_username or
                    (msg.get("sender") is None and msg.get("sender_id") == self.current_user_id)
            )
            status = msg.get("status", "delivered")
            self.main_page.add_message_to_ui(
                msg.get("chat_name"),
                msg.get("content"),
                is_mine,
                status
            )
        self.loaded_chats.add(chat_name)

    def set_current_user(self, user_info: dict):
        self.current_user_id = user_info.get("user_id")
        self.current_username = user_info.get("username")
        # is_mine kontrolünü artık bu id ile yap

    def load_user_chats(self, chats: list):
        for chat in chats:
            chat_name = chat.get("chat_name")
            # Zaten listede varsa ekleme
            already_exists = False
            for i in range(self.main_page.chat_screens_stack.count()):
                widget = self.main_page.chat_screens_stack.widget(i)
                if hasattr(widget, 'contact_name') and widget.contact_name == chat_name:
                    already_exists = True
                    break

            if not already_exists:
                self.main_page.add_new_chat_to_ui(chat_name)
                # Geçmişi de yükle
                self.loaded_chats.discard(chat_name)  # tekrar yüklenmesi için
                self.load_history_for_chat(chat_name)

    def handle_search(self, query: str):
        print(f"[DEBUG] Arama: {query}, kullanıcı: {self.current_username}")
        self.chat_service.send_search_request(query, self.current_username or "")

    def handle_start_chat(self, username: str):
        self.main_page.search_input.clear()
        self.main_page.clear_search_results()

        self.chat_service.send_create_chat_request(username, self.current_username)
        self.main_page.add_new_chat_to_ui(username)

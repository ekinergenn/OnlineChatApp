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


class ChatController:
    def __init__(self, main_page, chat_service):
        self.main_page = main_page
        self.chat_service = chat_service

        # Artı butonuna tıklanma olayını bağla
        self.main_page.add_chat_btn.clicked.connect(self.show_create_group_dialog)

        # Servisten gelecek cevabı bekle
        self.chat_service.create_group_response_signal.connect(self.on_group_created)

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
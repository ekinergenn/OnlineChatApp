import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
import threading
from network import Client
from services.block_service import BlockService
from ui import LoginPageUI, RegisterPageUI, MainPageUI
from services import LogRegService
from services.chat_service import ChatService
from services.message_service import MessageService
from services.encryption_service import EncryptionService
from controllers import LogRegController
from controllers.chat_controller import ChatController
from controllers.message_controller import MessageController
from services.chatbot_service import ChatbotService
from services.community_service import CommunityService
from controllers.chatbot_controller import ChatbotController
from controllers.community_controller import CommunityController


class MainApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OnlineChat Uygulaması")
        self.setStyleSheet("QMainWindow { background-color: #f0f2f5; }")
        self.current_user = None

        # 1. Ana widget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 2. UI sayfaları
        self.login_page = LoginPageUI()
        self.register_page = RegisterPageUI()
        self.main_page = MainPageUI()

        self.stacked_widget.addWidget(self.login_page)    # index 0
        self.stacked_widget.addWidget(self.register_page)  # index 1
        self.stacked_widget.addWidget(self.main_page)      # index 2

        # 3. Network
        self.chat_client = Client(services={})

        # 4. Servisler
        GEMINI_API_KEY = "AIzaSyA8VFHD0EcCU98ywUya6uI7LyN82Qd8OJg"
        self.chatbot_service = ChatbotService(GEMINI_API_KEY)
        self.chat_service = ChatService(self.chat_client)
        self.message_service = MessageService(self.chat_client)
        self.logreg_service = LogRegService(self.chat_client, chat_service=self.chat_service)
        self.block_service = BlockService(self.chat_client)
        self.community_service = CommunityService(self.chat_client)
        self.encryption_service = EncryptionService(self.chat_client, keys_dir="keys")

        # 5. Servisleri client'a tanıt
        services_dict = {
            'logreg_service': self.logreg_service,
            'chat_service': self.chat_service,
            'message_service': self.message_service,
            'block_service': self.block_service,
            'community_service': self.community_service,
            'encryption_service': self.encryption_service
        }

        self.chat_client.register_services(services_dict)

        from network.message_handler import MessageHandler
        self.chat_client.message_handler = MessageHandler(services_dict)

        # 6. Controller'lar
        self.auth_controller = LogRegController(
            self.stacked_widget,
            self.login_page,
            self.register_page,
            self.logreg_service,
            on_login_success=self.on_login_success
        )
        self.message_controller = MessageController(
            self.main_page,
            self.message_service,
            self.encryption_service
        )
        self.chat_controller = ChatController(
            self.main_page,
            self.chat_service,
            self.message_controller,
            self.block_service,
            self.chatbot_service
        )
        self.chatbot_controller = ChatbotController(self.main_page, self.chatbot_service)
        self.community_controller = CommunityController(self.main_page, self.community_service)

        # 7. Bağlan ve dinle
        if self.chat_client.connect():
            self.listen_thread = threading.Thread(
                target=self.chat_client.listen_for_messages
            )
            self.listen_thread.daemon = True
            self.listen_thread.start()

        # Çıkış sinyalleri
        self.main_page.profile_page.logout_signal.connect(self.handle_logout)
        self.logreg_service.logout_requested_signal.connect(self.handle_logout)

    def handle_logout(self):
        reply = QMessageBox.question(
            self, 'Oturumu Kapat',
            "Oturumu kapatmak istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.login_page.clear_fields()
            self.main_page.reset_ui()
            self.chat_controller.reset_user_data()
            self.message_controller.reset_user_data()
            self.encryption_service.reset()  # Anahtarları ve önbelleği temizle
            self.stacked_widget.setCurrentIndex(0)
            self.current_user = None

    def on_login_success(self, user_info: dict):
        """Login başarılı olunca çağrılır."""
        self.current_user = user_info
        username = user_info.get("username", "")
        password = user_info.get("password", "")
        encrypted_backup = user_info.get("encrypted_private_key")

        self.main_page.current_username = username
        self.main_page.reset_ui()

        # E2EE: RSA anahtar yönetimi ve Senkronizasyon
        print(f"[E2EE] Anahtar kontrolü yapılıyor: {username}")
        
        server_pub_key = user_info.get("public_key")
        
        # 1. Lokal anahtarı yüklemeyi dene
        local_pub_key = self.encryption_service.load_private_key(username)
        
        should_restore = False
        if local_pub_key:
            # ÖNEMLİ: Lokal anahtar var ama sunucudaki ile aynı mı?
            if server_pub_key and local_pub_key.strip() != server_pub_key.strip():
                print("[E2EE] UYARI: Lokal anahtar sunucudaki ile eşleşmiyor! Senkronizasyon gerekiyor.")
                should_restore = True
            else:
                print("[E2EE] Lokal anahtar doğrulandı ve yüklendi.")
                # Sunucuda yedek yoksa yedekle
                if not encrypted_backup:
                    backup_blob = self.encryption_service.backup_private_key(password)
                    if backup_blob:
                        self.chat_client.send_data({
                            "type": "update_private_key_backup_request",
                            "payload": {"username": username, "encrypted_private_key": backup_blob}
                        })
        else:
            should_restore = True

        # 2. Geri yükleme (Restore) gerekiyorsa ve yedek varsa yap
        if should_restore and encrypted_backup:
            print("[E2EE] Sunucudaki şifreli yedek indiriliyor ve geri yükleniyor...")
            success = self.encryption_service.restore_private_key(username, encrypted_backup, password)
            if success:
                local_pub_key = self.encryption_service.get_public_key_pem()
            
        # 3. Hala anahtar yoksa (Yeni cihaz ve yedek yok), yeni oluştur ve yedekle
        if not local_pub_key:
            print("[E2EE] Hiç anahtar bulunamadı, yeni anahtar çifti oluşturuluyor...")
            local_pub_key = self.encryption_service.generate_key_pair(username)
            backup_blob = self.encryption_service.backup_private_key(password)
            if backup_blob:
                self.chat_client.send_data({
                    "type": "update_private_key_backup_request",
                    "payload": {"username": username, "encrypted_private_key": backup_blob}
                })

        # Sunucuya her zaman güncel genel anahtarımızı bildir
        if local_pub_key:
            self.encryption_service.send_update_public_key_request(username)

        # UI Sinyallerini tazele (Logout sonrası temizlenenleri geri bağla)
        self.chat_controller.connect_ui_signals()

        self.chat_controller.set_current_user(user_info)
        self.message_controller.set_current_user(user_info)
        self.community_controller.set_current_user(user_info)

        self.stacked_widget.setCurrentIndex(2)
        self.main_page.main_stack.setCurrentIndex(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainApplicationWindow()
    main_window.showMaximized()
    sys.exit(app.exec_())
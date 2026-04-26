import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
import threading
from network import Client
from ui import LoginPageUI, RegisterPageUI, MainPageUI
from services import LogRegService
from services.chat_service import ChatService
from controllers import LogRegController
from controllers.chat_controller import ChatController


class MainApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OnlineChat Uygulaması")
        self.setStyleSheet("QMainWindow { background-color: #f0f2f5; }")

        # 1. Ana widget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 2. UI sayfaları
        self.login_page = LoginPageUI()
        self.register_page = RegisterPageUI()
        self.main_page = MainPageUI()

        self.stacked_widget.addWidget(self.login_page)   # index 0
        self.stacked_widget.addWidget(self.register_page) # index 1
        self.stacked_widget.addWidget(self.main_page)     # index 2

        # 3. Network
        self.chat_client = Client(services={})

        # 4. Servisler
        self.logreg_service = LogRegService(self.chat_client)
        self.chat_service = ChatService(self.chat_client)

        # 5. Servisleri client'a tanıt (tek seferde)
        self.chat_client.register_services({
            'logreg_service': self.logreg_service,
            'chat_service': self.chat_service
        })

        # 6. Controller'lar
        self.auth_controller = LogRegController(
            self.stacked_widget,
            self.login_page,
            self.register_page,
            self.logreg_service
        )
        self.chat_controller = ChatController(self.main_page, self.chat_service)

        # 7. Bağlan ve dinle
        if self.chat_client.connect():
            self.listen_thread = threading.Thread(
                target=self.chat_client.listen_for_messages
            )
            self.listen_thread.daemon = True
            self.listen_thread.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainApplicationWindow()
    main_window.showMaximized()
    sys.exit(app.exec_())
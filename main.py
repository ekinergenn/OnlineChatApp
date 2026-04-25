import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
import threading 
from network import Client
from ui import LoginPageUI,RegisterPageUI,MainPageUI
from services import LogRegService
from controllers import LogRegController



class MainApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OnlineChat Uygulaması")

        self.setStyleSheet("QMainWindow { background-color: #f0f2f5; }")

        # 1. QStackedWidget oluştur
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        # 2. Sayfalarımızdan birer örnek (instance) oluştur
        self.login_page = LoginPageUI()
        self.register_page = RegisterPageUI()

        # 3. Sayfaları desteye ekle
        self.stacked_widget.addWidget(self.login_page)  # Index 0
        self.stacked_widget.addWidget(self.register_page)  # Index 1
        self.chat_client = Client(services={})

        # 2. Servisleri Oluştur ve hepsine bu ORTAK client'ı ver
        self.logreg_service = LogRegService(self.chat_client)
        # self.chat_service = ChatService(self.chat_client) # İleride böyle eklenecek

        # 3. İstemciye (MessageHandler'a) servisleri tanıt ki gelen mesajı iletebilsin
        services_dict = {
            'logreg_service': self.logreg_service,
            # 'chat_service': self.chat_service
        }
        self.chat_client.register_services(services_dict)

        # 4. Controller'ı Oluştur ve SADECE kendi servisini ver
        self.auth_controller = LogRegController(
            self.stacked_widget,
            self.login_page,
            self.register_page,
            self.logreg_service # Controller artık client'ı değil, sadece servisini biliyor!
        )

        self.main_page = MainPageUI()
        self.stacked_widget.addWidget(self.main_page)

        # 5. Ağa Bağlan ve Dinlemeyi Başlat
        if self.chat_client.connect():
            # Uygulama donmasın diye dinlemeyi ayrı Thread'e alıyoruz
            self.listen_thread = threading.Thread(target=self.chat_client.listen_for_messages)
            self.listen_thread.daemon = True
            self.listen_thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_window = MainApplicationWindow()
    main_window.showMaximized()

    sys.exit(app.exec_())
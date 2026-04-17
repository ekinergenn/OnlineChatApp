import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from ui.loginPage import LoginPageUI
from ui.registerPage import RegisterPageUI
from controllers.logReg_controller import LogRegController
from ui.mainPage import MainPageUI


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

        # 4. Controller'ı Başlat
        self.auth_controller = LogRegController(
            self.stacked_widget,
            self.login_page,
            self.register_page
        )
        self.main_page = MainPageUI()
        self.stacked_widget.addWidget(self.main_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_window = MainApplicationWindow()
    main_window.showMaximized()

    sys.exit(app.exec_())
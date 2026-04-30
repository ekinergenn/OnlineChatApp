from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QColor


class LoginPageUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignCenter)

        self.card = QFrame()
        self.card.setFixedSize(450, 550)
        self.card.setStyleSheet("QFrame { background-color: #ffffff; border-radius: 20px; }")

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(40, 50, 40, 50)
        card_layout.setSpacing(20)

        # Başlıklar
        logo_label = QLabel("OnlineChat")
        logo_label.setStyleSheet("font-size: 32px; font-weight: 800; color: #3b82f6; margin-bottom: 10px;")
        logo_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(logo_label)

        welcome_label = QLabel("Sohbete Başlamak için Giriş Yapın")
        welcome_label.setStyleSheet("font-size: 15px; color: #667781; margin-bottom: 20px;")
        welcome_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(welcome_label)

        # İnputlar
        input_style = "QLineEdit { background-color: #f0f2f5; border: 1px solid #d1d7db; border-radius: 8px; padding: 12px 15px; font-size: 14px; color: black;} QLineEdit:focus { border: 2px solid #3b82f6; background-color: #ffffff; color: black;}"

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Kullanıcı Adı")
        self.username_input.setStyleSheet(input_style)
        card_layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Şifre")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(input_style)
        card_layout.addWidget(self.password_input)

        # Şifremi Unuttum
        forgot_password_label = QLabel("Şifrenizi mi unuttunuz?")
        forgot_password_label.setStyleSheet("color: #3b82f6; font-size: 13px; font-weight: 600;")
        forgot_password_label.setAlignment(Qt.AlignRight)
        forgot_password_label.setCursor(QCursor(Qt.PointingHandCursor))
        card_layout.addWidget(forgot_password_label)
        card_layout.addSpacing(10)

        # Giriş Butonu
        self.login_button = QPushButton("Giriş Yap")
        self.login_button.setMinimumHeight(50)
        self.login_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.login_button.setStyleSheet(
            "QPushButton { background-color: #3b82f6; color: white; border-radius: 8px; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #2563eb; } QPushButton:pressed { background-color: #1d4ed8; }")
        card_layout.addWidget(self.login_button)

        # Kayıt Ol Linki
        card_layout.addStretch()
        register_layout = QHBoxLayout()
        no_account_label = QLabel("Hesabınız yok mu?")
        no_account_label.setStyleSheet("color: #667781; font-size: 14px;")

        self.register_label_link = QLabel("Kayıt Ol")
        self.register_label_link.setStyleSheet("color: #3b82f6; font-size: 14px; font-weight: bold;")
        self.register_label_link.setCursor(QCursor(Qt.PointingHandCursor))

        register_layout.addStretch()
        register_layout.addWidget(no_account_label)
        register_layout.addWidget(self.register_label_link)
        register_layout.addStretch()
        card_layout.addLayout(register_layout)

        self.main_layout.addWidget(self.card)

    def clear_fields(self):
        self.username_input.clear()
        self.password_input.clear()
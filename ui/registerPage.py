from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QColor

class RegisterPageUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignCenter)

        self.card = QFrame()
        self.card.setFixedSize(450, 740)
        self.card.setStyleSheet("QFrame { background-color: #ffffff; border-radius: 20px; }")

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(15)

        # Başlıklar
        logo_label = QLabel("Hesap Oluştur")
        logo_label.setStyleSheet("font-size: 28px; font-weight: 800; color: #3b82f6; margin-bottom: 5px;")
        logo_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(logo_label)

        welcome_label = QLabel("Aramıza katılmak için bilgilerinizi girin")
        welcome_label.setStyleSheet("font-size: 14px; color: #667781; margin-bottom: 15px;")
        welcome_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(welcome_label)

        # İnputlar
        input_style = "QLineEdit { background-color: #f0f2f5; border: 1px solid #d1d7db; border-radius: 8px; padding: 12px 15px; font-size: 14px; color: black} QLineEdit:focus { border: 2px solid #3b82f6; background-color: #ffffff; color: black;}"

        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("Adınız ve Soyadınız")
        self.fullname_input.setStyleSheet(input_style)
        card_layout.addWidget(self.fullname_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Kullanıcı Adı")
        self.username_input.setStyleSheet(input_style)
        card_layout.addWidget(self.username_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-posta Adresiniz")
        self.email_input.setStyleSheet(input_style)
        card_layout.addWidget(self.email_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Telefon Numarası (Örn: 05XX...)")
        self.phone_input.setStyleSheet(input_style)
        card_layout.addWidget(self.phone_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Şifre Belirleyin")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(input_style)
        card_layout.addWidget(self.password_input)

        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setPlaceholderText("Şifrenizi Tekrar Girin")
        self.password_confirm_input.setEchoMode(QLineEdit.Password)
        self.password_confirm_input.setStyleSheet(input_style)
        card_layout.addWidget(self.password_confirm_input)

        card_layout.addSpacing(10)

        # Kayıt Ol Butonu
        self.register_button = QPushButton("Kayıt Ol")
        self.register_button.setMinimumHeight(50)
        self.register_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.register_button.setStyleSheet("QPushButton { background-color: #3b82f6; color: white; border-radius: 8px; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #2563eb; } QPushButton:pressed { background-color: #1d4ed8; }")
        card_layout.addWidget(self.register_button)

        # Giriş Yap Linki
        card_layout.addStretch()
        login_layout = QHBoxLayout()
        already_account_label = QLabel("Zaten hesabınız var mı?")
        already_account_label.setStyleSheet("color: #667781; font-size: 14px;")

        self.login_label_link = QLabel("Giriş Yap")
        self.login_label_link.setStyleSheet("color: #3b82f6; font-size: 14px; font-weight: bold;")
        self.login_label_link.setCursor(QCursor(Qt.PointingHandCursor))

        login_layout.addStretch()
        login_layout.addWidget(already_account_label)
        login_layout.addWidget(self.login_label_link)
        login_layout.addStretch()
        card_layout.addLayout(login_layout)

        self.main_layout.addWidget(self.card)
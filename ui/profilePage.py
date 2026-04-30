import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QLineEdit, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QFont


class ProfilePageUI(QWidget):
    logout_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Ana widget arka planı
        self.setStyleSheet("background-color: #f0f2f5;")

        # Ana Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
                QScrollArea { 
                    border: none; 
                    background-color: #f0f2f5; 
                }
                QScrollArea > QWidget > QWidget { 
                    background-color: #f0f2f5; 
                }
            """)
        scroll.viewport().setStyleSheet("background-color: #f0f2f5;")

        container = QWidget()
        container.setStyleSheet("background-color: #f0f2f5;")
        self.container_layout = QVBoxLayout(container)
        self.container_layout.setContentsMargins(100, 40, 100, 40)
        self.container_layout.setSpacing(25)
        self.container_layout.setAlignment(Qt.AlignTop)

        #üst kısım
        profile_header = QVBoxLayout()

        avatar = QLabel("👤")
        avatar.setFixedSize(100, 100)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("""
            background-color: #ffffff; 
            border: 2px solid #d1d7db; 
            border-radius: 50px; 
            font-size: 50px;
        """)

        name_title = QLabel("Profil Bilgileri")
        name_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #000000; margin-top: 10px;")

        profile_header.addWidget(avatar, alignment=Qt.AlignCenter)
        profile_header.addWidget(name_title, alignment=Qt.AlignCenter)
        self.container_layout.addLayout(profile_header)

        #2. KİŞİSEL BİLGİLER
        self.add_section_title("Kişisel Detaylar")

        self.name_input = self.create_input_group("Ad", "Adınızı girin")
        self.surname_input = self.create_input_group("Soyad", "Soyadınızı girin")
        self.phone_input = self.create_input_group("Telefon No", "+90 5XX XXX XX XX")

        # 3. ŞİFRE DEĞİŞTİRME
        self.add_section_title("Güvenlik")
        self.pass_input = self.create_input_group("Yeni Şifre", "••••••••", is_password=True)

        # 4. BAĞLI HESAPLAR
        self.add_section_title("Bağlı Hesaplar")
        self.insta_input = self.create_input_group("Instagram", "@kullaniciadi")
        self.link_input = self.create_input_group("LinkedIn", "linkedin.com/in/profil")

        #5.BUTONLAR
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        save_btn = QPushButton("Değişiklikleri Kaydet")
        save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        save_btn.setFixedHeight(45)
        save_btn.setStyleSheet("""
            QPushButton { background-color: #3b82f6; color: white; border-radius: 8px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #2563eb; }
        """)

        logout_btn = QPushButton("Oturumu Kapat")
        logout_btn.setCursor(QCursor(Qt.PointingHandCursor))
        logout_btn.setFixedHeight(45)
        logout_btn.setStyleSheet("""
            QPushButton { background-color: #ffffff; color: #000000; border: 1px solid #d1d7db; border-radius: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #f5f6f6; }
        """)

        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(logout_btn)
        self.container_layout.addLayout(buttons_layout)

        #sinyaller
        logout_btn.clicked.connect(self.logout_signal.emit)

        #6. HESABI SİL
        delete_btn = QPushButton("Hesabı Kalıcı Olarak Sil")
        delete_btn.setCursor(QCursor(Qt.PointingHandCursor))
        delete_btn.setStyleSheet(
            "color: #d32f2f; border: none; font-size: 13px; text-decoration: underline; margin-top: 20px;")
        self.container_layout.addWidget(delete_btn, alignment=Qt.AlignCenter)

        scroll.setWidget(container)
        self.main_layout.addWidget(scroll)

    def add_section_title(self, text):
        title = QLabel(text)
        title.setStyleSheet("""
            font-size: 16px; font-weight: bold; color: #000000; 
            border-bottom: 2px solid #d1d7db; padding-bottom: 5px; margin-top: 10px;
        """)
        self.container_layout.addWidget(title)

    def create_input_group(self, label_text, placeholder, is_password=False):
        group_layout = QVBoxLayout()
        group_layout.setSpacing(8)

        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #000000; font-weight: 500; font-size: 14px;")

        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        if is_password:
            edit.setEchoMode(QLineEdit.Password)

        edit.setFixedHeight(45)
        edit.setStyleSheet("""
            QLineEdit { 
                border: 1px solid #d1d7db; 
                border-radius: 8px; 
                padding-left: 15px; 
                background-color: #ffffff; 
                color: #000000;
                font-size: 14px;
            }
            QLineEdit:focus { 
                border: 2px solid #3b82f6; 
            }
        """)

        group_layout.addWidget(lbl)
        group_layout.addWidget(edit)
        self.container_layout.addLayout(group_layout)
        return edit


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProfilePageUI()
    window.resize(800, 900)
    window.show()
    sys.exit(app.exec_())
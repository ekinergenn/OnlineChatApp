import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QCursor


class MainPageUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Ana yatay layout (3 Sütun yan yana duracak)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. SÜTUN: İNCE SOL MENÜ (Navigasyon)
        self.create_nav_bar()

        # 2. SÜTUN: SOHBET LİSTESİ VE ARAMA
        self.create_chat_list_panel()

        # 3. SÜTUN: ANA SOHBET EKRANI (Boş/Hoş Geldin Durumu)
        self.create_main_chat_area()

    def create_nav_bar(self):
        nav_frame = QFrame()
        nav_frame.setFixedWidth(65)
        nav_frame.setStyleSheet("background-color: #f0f2f5; border-right: 1px solid #d1d7db;")

        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        nav_layout.setSpacing(25)
        nav_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Menü İkonları (Buton olarak)
        nav_buttons = [
            ("💬", "Sohbetler"),
            ("👥", "Topluluklar"),
            ("📢", "Kanallar")
        ]

        # Üst İkonlar
        for icon_text, tooltip in nav_buttons:
            btn = QPushButton(icon_text)
            btn.setToolTip(tooltip)
            btn.setFixedSize(40, 40)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent; border: none; font-size: 20px; border-radius: 8px;
                }
                QPushButton:hover { background-color: #e4e6eb; }
            """)
            nav_layout.addWidget(btn)

        nav_layout.addStretch()  # Arayı aç

        # Alt İkonlar (Ayarlar ve Profil)
        bottom_buttons = [("⚙️", "Ayarlar"), ("👤", "Profilim")]
        for icon_text, tooltip in bottom_buttons:
            btn = QPushButton(icon_text)
            btn.setToolTip(tooltip)
            btn.setFixedSize(40, 40)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton { background-color: transparent; border: none; font-size: 22px; border-radius: 8px; }
                QPushButton:hover { background-color: #e4e6eb; }
            """)
            nav_layout.addWidget(btn)

        self.main_layout.addWidget(nav_frame)

    def create_chat_list_panel(self):
        chat_list_frame = QFrame()
        chat_list_frame.setFixedWidth(500)
        chat_list_frame.setStyleSheet("background-color: #ffffff; border-right: 1px solid #d1d7db;")

        chat_layout = QVBoxLayout(chat_list_frame)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # --- Üst Başlık Bölümü ---
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 20, 20, 10)

        title_label = QLabel("Sohbetler")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #111b21;")

        add_chat_btn = QPushButton("➕")
        add_chat_btn.setFixedSize(35, 35)
        add_chat_btn.setCursor(QCursor(Qt.PointingHandCursor))
        add_chat_btn.setStyleSheet(
            "QPushButton { border: none; background-color: #f0f2f5; border-radius: 17px; } QPushButton:hover { background-color: #e4e6eb; }")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(add_chat_btn)

        chat_layout.addWidget(header_frame)

        # --- Arama Çubuğu ---
        search_frame = QFrame()
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(15, 5, 15, 15)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Aratın veya yeni sohbet başlatın")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #f0f2f5; color: #111b21; border: none; border-radius: 8px; padding: 8px 12px; font-size: 13px;
            }
            QLineEdit:focus { background-color: #ffffff; border: 1px solid #3b82f6; }
        """)
        search_layout.addWidget(self.search_input)
        chat_layout.addWidget(search_frame)

        # --- Kaydırılabilir Sohbet Listesi ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        # Örnek Sohbet Verileri Ekleyelim
        dummy_chats = [
            ("Ağlar Proje Grubu", "Socket kodunu kim yazıyor?", "13:45", True),
            ("Ahmet Yılmaz", "Tamamdır, akşam bakarız.", "12:10", False),
            ("Ayşe Kaya", "PDF dosyasını gönderdim.", "Dün", False),
            ("Marmara Duyuru", "Vize tarihleri açıklandı.", "Pzt", True),
            ("Python Topluluğu", "PyQt5 mi PyQt6 mı?", "Pzr", False),
            ("Mehmet (Ev)", "Ekmek al gelirken.", "14 Eki", False),
            ("Hoca", "Proje teslimi Cuma günü.", "10 Eki", False)
        ]

        for name, msg, time, unread in dummy_chats:
            chat_item = self.create_chat_item(name, msg, time, unread)
            self.scroll_layout.addWidget(chat_item)

        scroll_area.setWidget(scroll_content)
        chat_layout.addWidget(scroll_area)

        self.main_layout.addWidget(chat_list_frame)

    def create_chat_item(self, name, last_message, time, is_unread):
        # Tek bir sohbet satırı
        item_frame = QFrame()
        item_frame.setFixedHeight(75)
        item_frame.setCursor(QCursor(Qt.PointingHandCursor))
        item_frame.setStyleSheet("""
            QFrame { background-color: #ffffff; border-bottom: 1px solid #f0f2f5; }
            QFrame:hover { background-color: #f5f6f6; }
        """)

        layout = QHBoxLayout(item_frame)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        # Avatar (Yuvarlak Profil Resmi temsili)
        avatar = QLabel("👤")
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("background-color: #dfe5e7; border-radius: 25px; font-size: 24px;")

        # İsim ve Mesaj İçeriği
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignVCenter)

        name_label = QLabel(name)
        name_label.setStyleSheet("font-size: 16px; color: #111b21; font-weight: 500;")

        msg_label = QLabel(last_message)
        if is_unread:
            msg_label.setStyleSheet("font-size: 13px; color: #111b21; font-weight: bold;")
        else:
            msg_label.setStyleSheet("font-size: 13px; color: #667781;")

        text_layout.addWidget(name_label)
        text_layout.addWidget(msg_label)

        # Saat ve Okunmamış Sayısı
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignRight | Qt.AlignTop)

        time_label = QLabel(time)
        if is_unread:
            time_label.setStyleSheet("font-size: 12px; color: #3b82f6; font-weight: bold;")
            badge = QLabel("1")
            badge.setFixedSize(20, 20)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet(
                "background-color: #3b82f6; color: white; border-radius: 10px; font-size: 11px; font-weight: bold;")
            info_layout.addWidget(time_label)
            info_layout.addWidget(badge, alignment=Qt.AlignRight)
        else:
            time_label.setStyleSheet("font-size: 12px; color: #667781;")
            info_layout.addWidget(time_label)

        layout.addWidget(avatar)
        layout.addLayout(text_layout)
        layout.addStretch()
        layout.addLayout(info_layout)

        return item_frame

    def create_main_chat_area(self):
        # Başlangıçta açılan Boş "Hoş Geldiniz" ekranı
        self.chat_area_frame = QFrame()
        self.chat_area_frame.setStyleSheet("background-color: #f0f2f5;")

        layout = QVBoxLayout(self.chat_area_frame)

        # 1. ÜST BOŞLUK (İçeriği aşağı doğru iter)
        layout.addStretch()

        # --- ORTA MERKEZ İÇERİKLERİ ---
        # Büyük Logo / İkon
        big_icon = QLabel("💻")
        big_icon.setStyleSheet("font-size: 80px; color: #667781;")
        big_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(big_icon)

        title = QLabel("OnlineChat Masaüstü")
        title.setStyleSheet("font-size: 28px; color: #111b21; font-weight: 300; margin-top: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(
            "Uçtan uca şifrelenmiş mesajlarınızı gönderin ve alın.<br>Sohbet başlatmak için soldan bir kişiyi seçin.")
        subtitle.setStyleSheet("font-size: 14px; color: #667781; line-height: 1.5; margin-top: 10px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # 2. ALT BOŞLUK (İçeriği yukarı doğru iter ve tam ortada dengeler)
        layout.addStretch()

        # --- EN ALTTAKİ NOT ---
        security_note = QLabel("🔒 Mesajlarınız uçtan uca şifrelenir")
        security_note.setStyleSheet("font-size: 12px; color: #8696a0; margin-bottom: 20px;")
        security_note.setAlignment(Qt.AlignCenter)
        layout.addWidget(security_note)

        self.main_layout.addWidget(self.chat_area_frame)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainPageUI()
    window.setWindowTitle("OnlineChat - Ana Ekran")
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec_())
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QScrollArea, QSizePolicy, QStackedWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QCursor
from ui.communitiesPage import CommunitiesPageUI
from ui.settingsPage import SettingsPageUI
from ui.profilePage import ProfilePageUI

# Tıklanabilir sohbet listesi elemanları için özel QFrame sınıfı
class ClickableFrame(QFrame):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class MainPageUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Ana yatay layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. SÜTUN: İNCE SOL MENÜ (Navigasyon - Sabit kalacak)
        self.create_nav_bar()

        # ANA STACK: Menü butonlarına basınca değişecek olan ana içerik alanı
        self.main_stack = QStackedWidget(self)
        self.main_layout.addWidget(self.main_stack)

        # Sayfa 1: Sohbetler Sayfası (Sohbet listesi + Sohbet Ekranı) index 0
        self.chats_page = QWidget()
        self.chats_page_layout = QHBoxLayout(self.chats_page)
        self.chats_page_layout.setContentsMargins(0, 0, 0, 0)
        self.chats_page_layout.setSpacing(0)
        
        # Sohbetler sayfası için alt elemanları oluştur
        self.create_chat_list_panel()
        self.create_chat_screens_stack()
        
        self.main_stack.addWidget(self.chats_page)

        # Sayfa 2: Topluluklar Sayfası (Örnek Boş Sayfa) index 1
        self.communities_page = CommunitiesPageUI(self)
        
        self.main_stack.addWidget(self.communities_page)

        #sayfa 3: ayarlar index 2
        self.settings_page = SettingsPageUI(self)
        self.main_stack.addWidget(self.settings_page)

        # Sayfa 4: Profil Sayfası index 3
        self.profile_page = ProfilePageUI(self)
        self.main_stack.addWidget(self.profile_page)

    def create_nav_bar(self):
        nav_frame = QFrame()
        nav_frame.setFixedWidth(65)
        nav_frame.setStyleSheet("background-color: #f0f2f5; border-right: 1px solid #d1d7db;")

        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        nav_layout.setSpacing(25)
        nav_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Sohbetler Butonu
        self.btn_chats = QPushButton("💬")
        self.btn_chats.setToolTip("Sohbetler")
        self.setup_nav_button(self.btn_chats)
        self.btn_chats.clicked.connect(lambda: self.main_stack.setCurrentIndex(0))
        nav_layout.addWidget(self.btn_chats)

        # Topluluklar Butonu
        self.btn_communities = QPushButton("👥")
        self.btn_communities.setToolTip("Topluluklar")
        self.setup_nav_button(self.btn_communities)
        self.btn_communities.clicked.connect(lambda: self.main_stack.setCurrentIndex(1))
        nav_layout.addWidget(self.btn_communities)

        nav_layout.addStretch()  # Arayı aç

        # Ayarlar
        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setToolTip("Ayarlar")
        self.setup_nav_button(self.btn_settings)
        self.btn_settings.clicked.connect(lambda: self.main_stack.setCurrentIndex(2))
        nav_layout.addWidget(self.btn_settings)

        # Profil
        self.btn_profile = QPushButton("👤")
        self.btn_profile.setToolTip("Profilim")
        self.setup_nav_button(self.btn_profile)
        self.btn_profile.clicked.connect(lambda: self.main_stack.setCurrentIndex(3))
        nav_layout.addWidget(self.btn_profile)

        self.main_layout.addWidget(nav_frame)

    def setup_nav_button(self, btn):
        btn.setFixedSize(40, 40)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setStyleSheet("""
            QPushButton { background-color: transparent; border: none; font-size: 20px; border-radius: 8px; }
            QPushButton:hover { background-color: #e4e6eb; }
        """)

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

        self.dummy_chats = [
            ("Ağlar Proje Grubu", "Socket kodunu kim yazıyor?", "13:45", True),
            ("Ahmet Yılmaz", "Tamamdır, akşam bakarız.", "12:10", False),
            ("Ayşe Kaya", "PDF dosyasını gönderdim.", "Dün", False),
            ("Marmara Duyuru", "Vize tarihleri açıklandı.", "Pzt", True),
            ("Python Topluluğu", "PyQt5 mi PyQt6 mı?", "Pzr", False),
            ("Mehmet (Ev)", "Ekmek al gelirken.", "14 Eki", False),
            ("Hoca", "Proje teslimi Cuma günü.", "10 Eki", False)
        ]

        # StackWidget'taki indeksler 0 (Hoşgeldin) ile başlayacağı için, 
        # ilk sohbetin indeksi 1, ikincisinin 2 olacak.
        for index, (name, msg, time, unread) in enumerate(self.dummy_chats, start=1):
            chat_item = self.create_chat_item(name, msg, time, unread, index)
            self.scroll_layout.addWidget(chat_item)

        scroll_area.setWidget(scroll_content)
        chat_layout.addWidget(scroll_area)

        self.chats_page_layout.addWidget(chat_list_frame)

    def create_chat_item(self, name, last_message, time, is_unread, stack_index):
        # Tıklanabilir ClickableFrame kullanıyoruz
        item_frame = ClickableFrame()
        item_frame.setFixedHeight(75)
        item_frame.setCursor(QCursor(Qt.PointingHandCursor))
        item_frame.setStyleSheet("""
            QFrame { background-color: #ffffff; border-bottom: 1px solid #f0f2f5; }
            QFrame:hover { background-color: #f5f6f6; }
        """)

        # Tıklama sinyalini StackWidget'ın indeksini değiştirmeye bağlıyoruz
        item_frame.clicked.connect(lambda: self.chat_screens_stack.setCurrentIndex(stack_index))

        layout = QHBoxLayout(item_frame)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        # Avatar
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
            badge.setStyleSheet("background-color: #3b82f6; color: white; border-radius: 10px; font-size: 11px; font-weight: bold;")
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

    def create_chat_screens_stack(self):
        # 3. SÜTUN: KİŞİYE GÖRE DEĞİŞEN SOHBET EKRANI STACK'İ
        self.chat_screens_stack = QStackedWidget()
        
        # İndeks 0: Hoş Geldin Ekranı (Boş Durum)
        welcome_screen = self.create_welcome_screen()
        self.chat_screens_stack.addWidget(welcome_screen)

        # İndeks 1'den itibaren: Listede yer alan her sohbet için özel ekran oluşturuyoruz
        for name, msg, time, unread in self.dummy_chats:
            specific_chat_screen = self.create_individual_chat_screen(name)
            self.chat_screens_stack.addWidget(specific_chat_screen)

        self.chats_page_layout.addWidget(self.chat_screens_stack)

    def create_welcome_screen(self):
        welcome_frame = QFrame()
        welcome_frame.setStyleSheet("background-color: #f0f2f5;")
        layout = QVBoxLayout(welcome_frame)
        layout.addStretch()

        big_icon = QLabel("💻")
        big_icon.setStyleSheet("font-size: 80px; color: #667781;")
        big_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(big_icon)

        title = QLabel("OnlineChat Masaüstü")
        title.setStyleSheet("font-size: 28px; color: #111b21; font-weight: 300; margin-top: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Uçtan uca şifrelenmiş mesajlarınızı gönderin ve alın.<br>Sohbet başlatmak için soldan bir kişiyi seçin.")
        subtitle.setStyleSheet("font-size: 14px; color: #667781; line-height: 1.5; margin-top: 10px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addStretch()

        security_note = QLabel("🔒 Mesajlarınız uçtan uca şifrelenir")
        security_note.setStyleSheet("font-size: 12px; color: #8696a0; margin-bottom: 20px;")
        security_note.setAlignment(Qt.AlignCenter)
        layout.addWidget(security_note)

        return welcome_frame

    def create_individual_chat_screen(self, contact_name):
        # Kişiye veya gruba tıklandığında açılacak basit sohbet arayüzü
        chat_frame = QFrame()
        chat_frame.setStyleSheet("background-color: #efeae2;") # Klasik sohbet arka plan rengi
        
        layout = QVBoxLayout(chat_frame)
        layout.setContentsMargins(0, 0, 0, 0)

        # Üst bar (Kişi bilgisi)
        top_bar = QFrame()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet("background-color: #f0f2f5; border-bottom: 1px solid #d1d7db;")
        top_layout = QHBoxLayout(top_bar)
        
        avatar = QLabel("👤")
        avatar.setFixedSize(40, 40)
        avatar.setStyleSheet("background-color: #dfe5e7; border-radius: 20px; font-size: 20px;")
        
        name_label = QLabel(contact_name)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #111b21;")
        
        top_layout.addWidget(avatar)
        top_layout.addWidget(name_label)
        top_layout.addStretch()

        # Mesajların listeleneceği orta alan
        chat_area = QLabel(f"<b>{contact_name}</b> ile mesajlaşma geçmişiniz burada görünecek.")
        chat_area.setAlignment(Qt.AlignCenter)
        chat_area.setStyleSheet("font-size: 14px; color: #667781;")

        # Alt bar (Mesaj yazma alanı)
        bottom_bar = QFrame()
        bottom_bar.setFixedHeight(60)
        bottom_bar.setStyleSheet("background-color: #f0f2f5;")
        bottom_layout = QHBoxLayout(bottom_bar)
        
        msg_input = QLineEdit()
        msg_input.setPlaceholderText("Bir mesaj yazın")
        msg_input.setStyleSheet("background-color: #ffffff; border: none; border-radius: 8px; padding: 10px; font-size: 14px;")
        
        send_btn = QPushButton("➤")
        send_btn.setStyleSheet("font-size: 20px; border: none; color: #667781;")
        
        bottom_layout.addWidget(msg_input)
        bottom_layout.addWidget(send_btn)

        layout.addWidget(top_bar)
        layout.addWidget(chat_area)
        layout.addWidget(bottom_bar)

        return chat_frame

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainPageUI()
    window.setWindowTitle("OnlineChat - Ana Ekran")
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec_())
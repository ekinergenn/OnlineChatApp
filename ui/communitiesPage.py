import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QScrollArea, QSizePolicy, QStackedWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QCursor


# Tıklanabilir sohbet listesi elemanları için özel QFrame sınıfı
class ClickableFrame(QFrame):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class CommunitiesPageUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Ana yatay layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ANA STACK: Menü butonlarına basınca değişecek olan ana içerik alanı
        self.main_stack = QStackedWidget(self)
        self.main_layout.addWidget(self.main_stack)

        # Topluluklar Sayfası (Topluluk listesi + Topluluk Ekranı)
        self.communities_page = QWidget()
        self.communities_page_layout = QHBoxLayout(self.communities_page)
        self.communities_page_layout.setContentsMargins(0, 0, 0, 0)
        self.communities_page_layout.setSpacing(0)

        # Topluluklar sayfası için alt elemanları oluştur
        self.create_comunities_list_panel()
        self.create_comunities_screens_stack()

        self.main_stack.addWidget(self.communities_page)

    def create_comunities_list_panel(self):
        communities_list_frame = QFrame()
        communities_list_frame.setFixedWidth(500)
        communities_list_frame.setStyleSheet("background-color: #ffffff; border-right: 1px solid #d1d7db;")

        communities_layout = QVBoxLayout(communities_list_frame)
        communities_layout.setContentsMargins(0, 0, 0, 0)
        communities_layout.setSpacing(0)

        # --- Üst Başlık Bölümü ---
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 20, 20, 10)

        title_label = QLabel("Topluluklar")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #111b21;")

        add_communities_btn = QPushButton("➕")
        add_communities_btn.setFixedSize(35, 35)
        add_communities_btn.setCursor(QCursor(Qt.PointingHandCursor))
        add_communities_btn.setStyleSheet(
            "QPushButton { border: none; background-color: #f0f2f5; border-radius: 17px; } QPushButton:hover { background-color: #e4e6eb; }")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(add_communities_btn)
        communities_layout.addWidget(header_frame)

        # --- Arama Çubuğu ---
        search_frame = QFrame()
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(15, 5, 15, 15)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #f0f2f5; color: #111b21; border: none; border-radius: 8px; padding: 8px 12px; font-size: 13px;
            }
            QLineEdit:focus { background-color: #ffffff; border: 1px solid #3b82f6; }
        """)
        search_layout.addWidget(self.search_input)
        communities_layout.addWidget(search_frame)

        # --- Kaydırılabilir Topluluk Listesi ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        self.dummy_communitiess = [
            ("Mitso", "Etkinliğimize bekleriz", "12:10", False),
            ("Marmara Üniversitesi", "PDF dosyasını gönderdim.", "Dün", True)
        ]

        # StackWidget'taki indeksler 0 (Hoşgeldin) ile başlayacağı için, 
        # ilk sohbetin indeksi 1, ikincisinin 2 olacak.
        for index, (name, msg, time, unread) in enumerate(self.dummy_communitiess, start=1):
            communities_item = self.create_communities_item(name, msg, time, unread, index)
            self.scroll_layout.addWidget(communities_item)

        scroll_area.setWidget(scroll_content)
        communities_layout.addWidget(scroll_area)

        self.communities_page_layout.addWidget(communities_list_frame)

    def create_communities_item(self, name, last_message, time, is_unread, stack_index):
        # Tıklanabilir ClickableFrame kullanıyoruz
        item_frame = ClickableFrame()
        item_frame.setFixedHeight(75)
        item_frame.setCursor(QCursor(Qt.PointingHandCursor))
        item_frame.setStyleSheet("""
            QFrame { background-color: #ffffff; border-bottom: 1px solid #f0f2f5; }
            QFrame:hover { background-color: #f5f6f6; }
        """)

        # Tıklama sinyalini StackWidget'ın indeksini değiştirmeye bağlıyoruz
        item_frame.clicked.connect(lambda: self.communities_screens_stack.setCurrentIndex(stack_index))

        layout = QHBoxLayout(item_frame)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        # Avatar
        avatar = QLabel("📣")
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

    def create_comunities_screens_stack(self):
        # 3. SÜTUN: Topluluğa GÖRE DEĞİŞEN SOHBET EKRANI STACK'İ
        self.communities_screens_stack = QStackedWidget()

        # İndeks 0: (Boş Durum)
        welcome_screen = self.create_welcome_screen()
        self.communities_screens_stack.addWidget(welcome_screen)

        # İndeks 1'den itibaren: Listede yer alan her sohbet için özel ekran oluşturuyoruz
        for name, msg, time, unread in self.dummy_communitiess:
            specific_communities_screen = self.create_individual_communities_screen(name)
            self.communities_screens_stack.addWidget(specific_communities_screen)

        self.communities_page_layout.addWidget(self.communities_screens_stack)

    def create_welcome_screen(self):
        welcome_frame = QFrame()
        welcome_frame.setStyleSheet("background-color: #f0f2f5;")
        layout = QVBoxLayout(welcome_frame)
        layout.addStretch()

        big_icon = QLabel("🌐")
        big_icon.setStyleSheet("font-size: 80px; color: #667781;")
        big_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(big_icon)

        title = QLabel("OnlineChat Masaüstü")
        title.setStyleSheet("font-size: 28px; color: #111b21; font-weight: 300; margin-top: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(
            "Topluluk mesajlarınızı görüntüleyin.<br>Görüntülemek için soldan bir topluluk seçin.")
        subtitle.setStyleSheet("font-size: 14px; color: #667781; line-height: 1.5; margin-top: 10px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addStretch()

        security_note = QLabel("🔒 Mesajlarınız uçtan uca şifrelenir")
        security_note.setStyleSheet("font-size: 12px; color: #8696a0; margin-bottom: 20px;")
        security_note.setAlignment(Qt.AlignCenter)
        layout.addWidget(security_note)

        return welcome_frame

    def create_individual_communities_screen(self, contact_name):
        # Topluluğa tıklandığında açılacak basit sohbet arayüzü
        communities_frame = QFrame()
        communities_frame.setStyleSheet("background-color: #efeae2;")  # Klasik sohbet arka plan rengi

        layout = QVBoxLayout(communities_frame)
        layout.setContentsMargins(0, 0, 0, 0)

        # Üst bar (topluluk bilgisi)
        top_bar = QFrame()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet("background-color: #f0f2f5; border-bottom: 1px solid #d1d7db;")
        top_layout = QHBoxLayout(top_bar)

        avatar = QLabel("📣")
        avatar.setFixedSize(40, 40)
        avatar.setStyleSheet("background-color: #dfe5e7; border-radius: 20px; font-size: 20px;")

        name_label = QLabel(contact_name)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #111b21;")

        top_layout.addWidget(avatar)
        top_layout.addWidget(name_label)
        top_layout.addStretch()

        # Mesajların listeleneceği orta alan
        communities_area = QLabel(f"<b>{contact_name}</b> ile mesajlaşma geçmişiniz burada görünecek.")
        communities_area.setAlignment(Qt.AlignCenter)
        communities_area.setStyleSheet("font-size: 14px; color: #667781;")

        layout.addWidget(top_bar)
        layout.addWidget(communities_area)

        return communities_frame


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CommunitiesPageUI()
    window.setWindowTitle("Onlinecommunities - Ana Ekran")
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec_())
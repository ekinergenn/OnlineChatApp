import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QScrollArea, QSizePolicy, QStackedWidget,
    QMenu, QAction, QMessageBox
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
    delete_chat_signal = pyqtSignal(str)
    block_user_signal = pyqtSignal(str)
    send_message_signal = pyqtSignal(str, str)
    load_history_signal = pyqtSignal(str)
    search_query_signal = pyqtSignal(str)
    start_chat_signal = pyqtSignal(str)

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

        self.add_chat_btn = QPushButton("➕")
        self.add_chat_btn.setFixedSize(35, 35)
        self.add_chat_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.add_chat_btn.setStyleSheet(
            "QPushButton { border: none; background-color: #f0f2f5; border-radius: 17px; } QPushButton:hover { background-color: #e4e6eb; }")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_chat_btn)
        chat_layout.addWidget(header_frame)

        # --- Arama Çubuğu ---
        search_frame = QFrame()
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(15, 5, 15, 15)

        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.on_search_changed)
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
        item_frame.contact_name = name
        item_frame.clicked.connect(lambda: self.load_history_signal.emit(name))
        item_frame.setFixedHeight(75)
        item_frame.setCursor(QCursor(Qt.PointingHandCursor))
        item_frame.setStyleSheet("""
            QFrame { background-color: #ffffff; border-bottom: 1px solid #f0f2f5; }
            QFrame:hover { background-color: #f5f6f6; }
        """)

        item_frame.clicked.connect(lambda n=name: self.switch_to_chat(n))

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

    def create_individual_chat_screen(self, contact_name):
        chat_frame = QFrame()
        chat_frame.setStyleSheet("background-color: #efeae2;")
        chat_frame.contact_name = contact_name  # ← arama için etiket

        layout = QVBoxLayout(chat_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── ÜST BAR ──────────────────────────────────────────
        top_bar = QFrame()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet("background-color: #f0f2f5; border-bottom: 1px solid #d1d7db;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 0, 10, 0)

        avatar = QLabel("👤")
        avatar.setFixedSize(40, 40)
        avatar.setStyleSheet("background-color: #dfe5e7; border-radius: 20px; font-size: 20px;")
        avatar.setAlignment(Qt.AlignCenter)

        name_label = QLabel(contact_name)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #111b21;")

        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(35, 35)
        delete_btn.setCursor(QCursor(Qt.PointingHandCursor))
        delete_btn.setStyleSheet("""
            QPushButton { border: none; font-size: 18px; border-radius: 17px; background-color: transparent; }
            QPushButton:hover { background-color: #ffebee; }
        """)
        delete_btn.clicked.connect(lambda: self.confirm_delete_chat(contact_name))

        options_btn = QPushButton("⋮")
        options_btn.setFixedSize(35, 35)
        options_btn.setCursor(QCursor(Qt.PointingHandCursor))
        options_btn.setStyleSheet("""
            QPushButton { border: none; font-size: 22px; font-weight: bold; border-radius: 17px; background-color: transparent; }
            QPushButton:hover { background-color: #e4e6eb; }
            QPushButton::menu-indicator { image: none; }
        """)
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background-color: #ffffff; border: 1px solid #d1d7db; border-radius: 5px; }
            QMenu::item { padding: 10px 20px; font-size: 14px; color: #111b21; }
            QMenu::item:selected { background-color: #f0f2f5; }
        """)
        block_action = QAction("🚫 Kişiyi Engelle", chat_frame)
        block_action.triggered.connect(lambda: self.block_user_signal.emit(contact_name))
        menu.addAction(block_action)
        options_btn.setMenu(menu)

        top_layout.addWidget(avatar)
        top_layout.addWidget(name_label)
        top_layout.addStretch()
        top_layout.addWidget(delete_btn)
        top_layout.addWidget(options_btn)

        # ── MESAJ ALANI (kaydırılabilir) ─────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        msg_container = QWidget()
        msg_container.setStyleSheet("background-color: #efeae2;")

        msg_layout = QVBoxLayout(msg_container)
        msg_layout.setContentsMargins(10, 10, 10, 10)
        msg_layout.setSpacing(6)
        msg_layout.addStretch()  # mesajları aşağıdan yukarı iter

        scroll.setWidget(msg_container)

        # referansları frame'e göm — sonra add_message_to_ui bulacak
        chat_frame.msg_layout = msg_layout
        chat_frame.scroll = scroll

        # ── ALT BAR ──────────────────────────────────────────
        bottom_bar = QFrame()
        bottom_bar.setFixedHeight(60)
        bottom_bar.setStyleSheet("background-color: #f0f2f5;")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(10, 10, 10, 10)

        msg_input = QLineEdit()
        msg_input.setPlaceholderText("Bir mesaj yazın")
        msg_input.setStyleSheet("""
            background-color: #ffffff; border: none;
            border-radius: 8px; padding: 10px; font-size: 14px;
        """)

        send_btn = QPushButton("➤")
        send_btn.setFixedSize(40, 40)
        send_btn.setCursor(QCursor(Qt.PointingHandCursor))
        send_btn.setStyleSheet("font-size: 20px; border: none; color: #3b82f6; background: transparent;")

        send_btn.clicked.connect(lambda: self.on_send_clicked(contact_name, msg_input))
        msg_input.returnPressed.connect(lambda: self.on_send_clicked(contact_name, msg_input))

        bottom_layout.addWidget(msg_input)
        bottom_layout.addWidget(send_btn)

        # ── HEPSİNİ ANA LAYOUT'A EKLE ────────────────────────
        layout.addWidget(top_bar)
        layout.addWidget(scroll)  # scroll genişler, stretch alır
        layout.addWidget(bottom_bar)

        return chat_frame

    def confirm_delete_chat(self, chat_name):
        """Çöp kutusuna basıldığında sohbeti silme onayı ister."""
        reply = QMessageBox.question(
            self,
            'Sohbeti Sil',
            f"'{chat_name}' ile olan sohbeti silmek istediğinize emin misiniz?\nBu işlem geri alınamaz.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            print(f"[{chat_name}] sohbeti silindi!")
            self.delete_chat_signal.emit(chat_name)

    def add_new_chat_to_ui(self, chat_name, last_message=""):
        new_stack_index = self.chat_screens_stack.count()
        new_chat_item = self.create_chat_item(
            name=chat_name,
            last_message=last_message,  # ← boş bırak
            time="",
            is_unread=False,
            stack_index=new_stack_index
        )
        self.scroll_layout.insertWidget(0, new_chat_item)
        new_chat_screen = self.create_individual_chat_screen(chat_name)
        self.chat_screens_stack.addWidget(new_chat_screen)
        self.chat_screens_stack.setCurrentIndex(new_stack_index)

    def on_send_clicked(self, chat_name, input_field):
        text = input_field.text().strip()
        if text:  # Boş mesaj gitmesin
            self.send_message_signal.emit(chat_name, text)
            input_field.clear()  # Gönderdikten sonra kutuyu temizle

    def add_message_to_ui(self, chat_name, content, is_mine=True, status="delivered"):
        for i in range(self.chat_screens_stack.count()):
            widget = self.chat_screens_stack.widget(i)
            if hasattr(widget, 'contact_name') and widget.contact_name == chat_name:
                msg_layout = widget.msg_layout
                scroll = widget.scroll

                # Son stretch'i geçici kaldır
                stretch_item = msg_layout.takeAt(msg_layout.count() - 1)

                # Baloncuğu ekle
                bubble = self._create_message_bubble(content, is_mine, status)
                msg_layout.addWidget(bubble)

                # Stretch'i geri koy
                msg_layout.addStretch()

                # En alta kaydır
                QApplication.processEvents()
                scroll.verticalScrollBar().setValue(
                    scroll.verticalScrollBar().maximum()
                )
                break
        self.update_chat_last_message(chat_name, content, is_mine)

    def _create_message_bubble(self, content, is_mine, status="delivered"):
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        w_layout = QHBoxLayout(wrapper)
        w_layout.setContentsMargins(0, 0, 0, 0)
        w_layout.setSpacing(0)

        # Balon + durum ikonu için dikey container
        bubble_container = QWidget()
        bubble_container.setStyleSheet("background: transparent;")
        b_layout = QVBoxLayout(bubble_container)
        b_layout.setContentsMargins(0, 0, 0, 0)
        b_layout.setSpacing(2)

        bubble = QLabel(content)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(400)
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)

        if is_mine:
            bubble.setStyleSheet("""
                background-color: #dcf8c6; color: #111b21;
                border-radius: 8px; padding: 8px 12px; font-size: 14px;
            """)

            # Durum ikonu (sadece kendi mesajlarımızda)
            status_label = QLabel()
            if status == "sent":
                status_label.setText("✓")
                status_label.setStyleSheet("color: #667781; font-size: 11px;")
            elif status == "delivered":
                status_label.setText("✓✓")
                status_label.setStyleSheet("color: #667781; font-size: 11px;")
            elif status == "read":
                status_label.setText("✓✓")
                status_label.setStyleSheet("color: #3b82f6; font-size: 11px; font-weight: bold;")

            status_label.setAlignment(Qt.AlignRight)

            b_layout.addWidget(bubble)
            b_layout.addWidget(status_label)

            w_layout.addStretch()
            w_layout.addWidget(bubble_container)
        else:
            bubble.setStyleSheet("""
                background-color: #ffffff; color: #111b21;
                border-radius: 8px; padding: 8px 12px; font-size: 14px;
            """)
            b_layout.addWidget(bubble)

            w_layout.addWidget(bubble_container)
            w_layout.addStretch()

        return wrapper

    def create_chat_screens_stack(self):
        self.chat_screens_stack = QStackedWidget()

        # İndeks 0: Hoş Geldin Ekranı
        welcome_screen = self.create_welcome_screen()
        self.chat_screens_stack.addWidget(welcome_screen)

        # İndeks 1'den itibaren: Her sohbet için ekran
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

        subtitle = QLabel(
            "Uçtan uca şifrelenmiş mesajlarınızı gönderin ve alın.<br>Sohbet başlatmak için soldan bir kişiyi seçin.")
        subtitle.setStyleSheet("font-size: 14px; color: #667781; line-height: 1.5; margin-top: 10px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addStretch()

        security_note = QLabel("🔒 Mesajlarınız uçtan uca şifrelenir")
        security_note.setStyleSheet("font-size: 12px; color: #8696a0; margin-bottom: 20px;")
        security_note.setAlignment(Qt.AlignCenter)
        layout.addWidget(security_note)

        return welcome_frame

    def remove_chat_from_ui(self, chat_name):
        # 1. Sol listedeki chat item'ı bul ve kaldır
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'contact_name') and widget.contact_name == chat_name:
                    self.scroll_layout.removeWidget(widget)
                    widget.deleteLater()
                    break

        # 2. Sağ stack'teki ekranı bul ve kaldır
        for i in range(self.chat_screens_stack.count()):
            widget = self.chat_screens_stack.widget(i)
            if hasattr(widget, 'contact_name') and widget.contact_name == chat_name:
                self.chat_screens_stack.removeWidget(widget)
                widget.deleteLater()
                break

        # 3. Hoş geldin ekranına dön
        self.chat_screens_stack.setCurrentIndex(0)

    def on_search_changed(self, text):
        print(f"[DEBUG] Arama kutusu değişti: {text}")
        if text.strip():
            self.search_query_signal.emit(text.strip())
        else:
            self.clear_search_results()

    def show_search_results(self, users: list):
        self.clear_search_results()
        for user in users:
            result_item = self.create_search_result_item(user)
            self.scroll_layout.insertWidget(0, result_item)

    def clear_search_results(self):
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'is_search_result') and widget.is_search_result:
                    self.scroll_layout.removeWidget(widget)
                    widget.deleteLater()

    def create_search_result_item(self, user: dict):
        item_frame = ClickableFrame()
        item_frame.is_search_result = True
        item_frame.setFixedHeight(75)
        item_frame.setCursor(QCursor(Qt.PointingHandCursor))
        item_frame.setStyleSheet("""
            QFrame { background-color: #f0f8ff; border-bottom: 1px solid #d1d7db; }
            QFrame:hover { background-color: #e0f0ff; }
        """)

        layout = QHBoxLayout(item_frame)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        avatar = QLabel("👤")
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("background-color: #dfe5e7; border-radius: 25px; font-size: 24px;")

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        name_label = QLabel(user.get("fullname", ""))
        name_label.setStyleSheet("font-size: 16px; color: #111b21; font-weight: 500;")

        info_label = QLabel(f"@{user.get('username')} • {user.get('tel', '')}")
        info_label.setStyleSheet("font-size: 13px; color: #667781;")

        text_layout.addWidget(name_label)
        text_layout.addWidget(info_label)

        layout.addWidget(avatar)
        layout.addLayout(text_layout)
        layout.addStretch()

        username = user.get("username")
        item_frame.clicked.connect(lambda: self.start_chat_signal.emit(username))

        return item_frame

    def update_chat_last_message(self, chat_name, content, is_mine):
        prefix = "Sen: " if is_mine else ""
        display_text = f"{prefix}{content}"

        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'contact_name') and widget.contact_name == chat_name:
                    # msg_label widget'ı bul (layout içinde 2. label)
                    layout = widget.layout()
                    for j in range(layout.count()):
                        inner = layout.itemAt(j)
                        if inner and inner.layout():
                            text_layout = inner.layout()
                            if text_layout.count() >= 2:
                                msg_label = text_layout.itemAt(1).widget()
                                if isinstance(msg_label, QLabel):
                                    msg_label.setText(display_text)
                                    msg_label.setStyleSheet("font-size: 13px; color: #667781;")
                                    # Chat'i listenin en üstüne taşı
                                    self.scroll_layout.removeWidget(widget)
                                    self.scroll_layout.insertWidget(0, widget)
                                break
                    break

    def switch_to_chat(self, chat_name):
        for i in range(self.chat_screens_stack.count()):
            widget = self.chat_screens_stack.widget(i)
            if hasattr(widget, 'contact_name') and widget.contact_name == chat_name:
                self.chat_screens_stack.setCurrentIndex(i)
                self.load_history_signal.emit(chat_name)
                break



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainPageUI()
    window.setWindowTitle("OnlineChat - Ana Ekran")
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec_())
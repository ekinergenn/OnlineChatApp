import datetime
import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QScrollArea, QSizePolicy, QStackedWidget,
    QMenu, QAction, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QByteArray
from PyQt5.QtGui import QFont, QCursor, QPixmap, QImage
from ui.communitiesPage import CommunitiesPageUI
from ui.settingsPage import SettingsPageUI
from ui.profilePage import ProfilePageUI
from ui.groupMembersDialog import GroupMembersDialog


# Tıklanabilir sohbet listesi elemanları için özel QFrame sınıfı
class ClickableFrame(QFrame):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class MainPageUI(QWidget):
    send_chatbot_message_signal = pyqtSignal(str)
    reset_chatbot_signal = pyqtSignal()
    delete_chat_signal = pyqtSignal(str)
    block_user_signal = pyqtSignal(str)
    send_message_signal = pyqtSignal(str, str)
    request_group_info_signal = pyqtSignal(str) # Yeni: (chat_id)
    send_image_signal = pyqtSignal(str, str)  # ← YENİ: (chat_name, image_path)
    load_history_signal = pyqtSignal(str)
    search_query_signal = pyqtSignal(str)
    start_chat_signal = pyqtSignal(str)
    create_group_signal = pyqtSignal(str, list)  # (group_name, [members])
    request_all_users_signal = pyqtSignal()  # + butonuna basınca sunucudan kullanıcı listesi iste
    typing_signal = pyqtSignal(str, bool)  # ← YENİ: (chat_name, is_typing)
    star_message_signal = pyqtSignal(dict)
    get_starred_messages_signal = pyqtSignal(str)
    unstar_from_settings_signal = pyqtSignal(dict)
    update_privacy_settings_signal = pyqtSignal(dict)
    get_privacy_settings_signal = pyqtSignal(str)
    request_blocked_users_signal = pyqtSignal()
    unblock_user_from_settings_signal = pyqtSignal(str)
    leave_group_signal = pyqtSignal(str)
    mark_messages_read_signal = pyqtSignal(str, list)  # (chat_id, [message_ids])

    def __init__(self):
        super().__init__()
        self.current_username = None
        self._typing_timers = {}
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

        # sayfa 3: ayarlar index 2
        self.settings_page = SettingsPageUI(main_page=self)
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
        self.btn_settings.clicked.connect(self.switch_to_settings_reset)
        nav_layout.addWidget(self.btn_settings)

        # Profil
        self.btn_profile = QPushButton("👤")
        self.btn_profile.setToolTip("Profilim")
        self.setup_nav_button(self.btn_profile)
        self.btn_profile.clicked.connect(lambda: self.main_stack.setCurrentIndex(3))
        nav_layout.addWidget(self.btn_profile)

        self.main_layout.addWidget(nav_frame)

    def switch_to_settings_reset(self):
        # ayarlar sayfasına geçer ve detay panelini sıfırlar
        self.main_stack.setCurrentIndex(2)  # Ayarlar sayfası indeksi
        if hasattr(self, 'settings_page'):
            self.settings_page.details_stack.setCurrentIndex(0)

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
        self.add_chat_btn.clicked.connect(self.request_all_users_signal.emit)
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

        self.chatbot_item = self.create_chatbot_item()
        chat_layout.addWidget(self.chatbot_item)

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

    def create_chat_item(self, name, last_message, time, unread_count, stack_index, is_group=False):
        # Tıklanabilir ClickableFrame kullanıyoruz
        item_frame = ClickableFrame()
        item_frame.contact_name = name
        item_frame.unread_count = unread_count
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
        avatar = QLabel("👥" if is_group else "👤")
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
        if unread_count > 0:
            msg_label.setStyleSheet("font-size: 13px; color: #111b21; font-weight: bold;")
        else:
            msg_label.setStyleSheet("font-size: 13px; color: #667781;")

        text_layout.addWidget(name_label)
        text_layout.addWidget(msg_label)

        # Saat ve Okunmamış Sayısı
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignRight | Qt.AlignTop)

        time_label = QLabel(time)
        if unread_count > 0:
            time_label.setStyleSheet("font-size: 12px; color: #3b82f6; font-weight: bold;")
            badge = QLabel(str(unread_count))
            badge.setFixedSize(20, 20)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet(
                "background-color: #3b82f6; color: white; border-radius: 10px; font-size: 11px; font-weight: bold;")
            info_layout.addWidget(time_label)
            info_layout.addWidget(badge, alignment=Qt.AlignRight)
            item_frame.badge_label = badge
        else:
            time_label.setStyleSheet("font-size: 12px; color: #667781;")
            info_layout.addWidget(time_label)
            item_frame.badge_label = None

        layout.addWidget(avatar)
        layout.addLayout(text_layout)
        layout.addStretch()
        layout.addLayout(info_layout)

        item_frame.msg_label = msg_label
        item_frame.time_label = time_label
        item_frame.info_layout = info_layout

        return item_frame

    def create_individual_chat_screen(self, contact_name, is_group=False):
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

        avatar = QLabel("👥" if is_group else "👤")
        avatar.setFixedSize(40, 40)
        avatar.setStyleSheet("background-color: #dfe5e7; border-radius: 20px; font-size: 20px;")
        avatar.setAlignment(Qt.AlignCenter)
        
        if is_group:
            avatar.setCursor(QCursor(Qt.PointingHandCursor))
            # Sadece ismi gönderiyoruz, controller chat_id'yi bulup sunucuya soracak
            avatar.mousePressEvent = lambda e: self.show_group_members(contact_name)

        name_col = QVBoxLayout()
        name_col.setSpacing(1)
        name_col.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel(contact_name)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #111b21;")

        # Durum etiketi — grup değilse göster
        status_label = QLabel("")
        status_label.setStyleSheet("font-size: 11px; color: #667781;")
        status_label.setVisible(not is_group)

        name_col.addWidget(name_label)
        name_col.addWidget(status_label)

        # Frame'e referans göm (sonradan güncellemek için)
        chat_frame.status_label = status_label

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
        if is_group:
            # grup kısmı
            leave_action = QAction("🚪 Gruptan Ayrıl", chat_frame)
            leave_action.triggered.connect(lambda _: self.confirm_delete_chat(contact_name, is_group=True))
            menu.addAction(leave_action)
            chat_frame.block_action = leave_action
        else:
            # ikili chat kısmı
            block_action = QAction("🚫 Kişiyi Engelle", chat_frame)
            block_action.triggered.connect(lambda: self.block_user_signal.emit(contact_name))
            menu.addAction(block_action)
            chat_frame.block_action = block_action

        options_btn.setMenu(menu)

        top_layout.addWidget(avatar)
        top_layout.addSpacing(8)
        top_layout.addLayout(name_col)
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

        chat_frame.message_status_labels = {}
        chat_frame.displayed_message_ids = set()  # Duplicate mesajı önlemek için

        # ── YAZMA GÖSTERGESİ ALANI (YENİ) ───────────────────────────────────
        self._typing_label_frame = None  # her frame için ayrı referans aşağıda atanıyor

        typing_bar = QFrame()
        typing_bar.setFixedHeight(22)
        typing_bar.setStyleSheet("background-color: transparent;")
        typing_layout = QHBoxLayout(typing_bar)
        typing_layout.setContentsMargins(14, 0, 0, 0)

        typing_lbl = QLabel("")
        typing_lbl.setStyleSheet("font-size: 12px; color: #667781; font-style: italic;")
        typing_layout.addWidget(typing_lbl)
        typing_layout.addStretch()

        chat_frame.typing_label = typing_lbl  # referans sakla
        chat_frame.typing_dots = 0  # animasyon sayacı
        chat_frame.typing_timer = QTimer()  # nokta animasyon timer'ı
        chat_frame.typing_timer.setInterval(400)
        chat_frame.typing_timer.timeout.connect(
            lambda f=chat_frame: self._animate_typing_dots(f)
        )

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

        attach_btn = QPushButton("📎")
        attach_btn.setFixedSize(40, 40)
        attach_btn.setCursor(QCursor(Qt.PointingHandCursor))
        attach_btn.setStyleSheet("font-size: 20px; border: none; color: #667781; background: transparent;")
        attach_btn.clicked.connect(lambda: self.on_attach_clicked(contact_name))

        send_btn.clicked.connect(lambda: self.on_send_clicked(contact_name, msg_input))
        msg_input.returnPressed.connect(lambda: self.on_send_clicked(contact_name, msg_input))

        # ← YENİ: yazma sinyali — debounce ile
        msg_input.textChanged.connect(
            lambda text, cn=contact_name: self._on_input_changed(cn, text)
        )

        bottom_layout.addWidget(attach_btn)
        bottom_layout.addWidget(msg_input)
        bottom_layout.addWidget(send_btn)

        # Referansları sakla (Controller tarafından engelleme durumunda kapatılabilmesi için)
        chat_frame.msg_input = msg_input
        chat_frame.send_btn = send_btn
        chat_frame.attach_btn = attach_btn
        chat_frame.bottom_bar = bottom_bar

        # ── HEPSİNİ ANA LAYOUT'A EKLE ────────────────────────
        layout.addWidget(top_bar)
        layout.addWidget(scroll)  # scroll genişler, stretch alır
        layout.addWidget(typing_bar)
        layout.addWidget(bottom_bar)

        return chat_frame

    def _on_input_changed(self, chat_name: str, text: str):
        """Kullanıcı yazıyor — 1.5 sn duraklayınca yazmayı bıraktı sinyali gönder."""
        if chat_name not in self._typing_timers:
            # İlk karakter: yazıyor sinyali gönder
            self.typing_signal.emit(chat_name, True)
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda cn=chat_name: self._on_typing_stopped(cn))
            timer.start(1500)
            self._typing_timers[chat_name] = timer
        else:
            # Yeni karakter geldi, zamanlayıcıyı sıfırla
            self._typing_timers[chat_name].stop()
            self._typing_timers[chat_name].start(1500)

        # Input boşaldıysa hemen durdur
        if not text.strip():
            self._on_typing_stopped(chat_name)

    def _on_typing_stopped(self, chat_name: str):
        self.typing_signal.emit(chat_name, False)
        if chat_name in self._typing_timers:
            self._typing_timers[chat_name].stop()
            del self._typing_timers[chat_name]

    # ─── YENİ: YAZMA GÖSTERGESİ ANİMASYONU ──────────────────────────────────
    def _animate_typing_dots(self, chat_frame):
        chat_frame.typing_dots = (chat_frame.typing_dots + 1) % 4
        dots = "." * chat_frame.typing_dots
        sender = getattr(chat_frame, '_typing_sender', '')
        is_group = getattr(chat_frame, 'is_group', False)
        if is_group and sender:
            chat_frame.typing_label.setText(f"{sender} yazıyor{dots}")
        else:
            chat_frame.typing_label.setText(f"yazıyor{dots}")

    # ─── YENİ: YAZMA GÖSTERGESİNİ GÖSTER / GİZLE ────────────────────────────
    def show_typing_indicator(self, chat_name: str, sender: str):
        for i in range(self.chat_screens_stack.count()):
            widget = self.chat_screens_stack.widget(i)
            if getattr(widget, 'contact_name', None) == chat_name:
                widget._typing_sender = sender
                widget.typing_label.setText("yazıyor.")
                if not widget.typing_timer.isActive():
                    widget.typing_timer.start()
                break

    def hide_typing_indicator(self, chat_name: str):
        for i in range(self.chat_screens_stack.count()):
            widget = self.chat_screens_stack.widget(i)
            if getattr(widget, 'contact_name', None) == chat_name:
                widget.typing_timer.stop()
                widget.typing_label.setText("")
                widget.typing_dots = 0
                break

    # ─── YENİ: DURUM ÇUBUĞUNU GÜNCELLE ──────────────────────────────────────
    def update_chat_status_bar(self, username: str, status: str, last_seen_ts=None):
        """Sohbet ekranının üst barındaki durum etiketini günceller."""
        for i in range(self.chat_screens_stack.count()):
            widget = self.chat_screens_stack.widget(i)
            if getattr(widget, 'contact_name', None) == username:
                label = getattr(widget, 'status_label', None)
                if label is None:
                    break

                if status == "online":
                    label.setText("● Çevrimiçi")
                    label.setStyleSheet("font-size: 11px; color: #22c55e; font-weight: 600;")
                else:
                    # Son görülme zamanı
                    if last_seen_ts:
                        try:
                            dt = datetime.datetime.fromtimestamp(float(last_seen_ts))
                            now = datetime.datetime.now()
                            diff = now - dt

                            if diff.total_seconds() < 60:
                                time_str = "az önce"
                            elif diff.total_seconds() < 3600:
                                mins = int(diff.total_seconds() // 60)
                                time_str = f"{mins} dakika önce"
                            elif diff.days == 0:
                                time_str = dt.strftime("bugün %H:%M")
                            elif diff.days == 1:
                                time_str = dt.strftime("dün %H:%M")
                            else:
                                time_str = dt.strftime("%d.%m.%Y %H:%M")

                            label.setText(f"Son görülme: {time_str}")
                        except Exception:
                            label.setText("Çevrimdışı")
                    else:
                        label.setText("Çevrimdışı")

                    label.setStyleSheet("font-size: 11px; color: #667781;")
                label.setVisible(True)
                break

    def confirm_delete_chat(self, chat_name, is_group=False):
        title = 'Gruptan Ayrıl' if is_group else 'Sohbeti Sil'
        message = (f"'{chat_name}' grubundan ayrılmak istediğinize emin misiniz?" if is_group else
                   f"'{chat_name}' ile olan sohbeti silmek istediğinize emin misiniz?\nBu işlem geri alınamaz.")

        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if is_group:
                # Burası kritik! handle_leave_group'u tetikleyecek olan sinyal:
                self.leave_group_signal.emit(chat_name)
            else:
                self.delete_chat_signal.emit(chat_name)

    def _add_existing_group_back(self, group_data):
        chat_name = group_data.get("chat_name")
        chat_id = group_data.get("chat_id")
        members = group_data.get("members", [])

        # 1. Eğer arayüzde sol listede zaten varsa, silip yeniden ekleyelim (UI Tazeleme garantisi)
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if getattr(w, 'contact_name', None) == chat_name:
                    self.scroll_layout.removeWidget(w)
                    w.deleteLater()
                    break

        # 2. Sağ taraftaki stack'te (mesaj ekranı) varsa onu da temizleyelim ki sıfırdan yüklensin
        for i in range(self.chat_screens_stack.count()):
            widget = self.chat_screens_stack.widget(i)
            if getattr(widget, 'contact_name', None) == chat_name:
                self.chat_screens_stack.removeWidget(widget)
                widget.deleteLater()
                break

        # 3. Şimdi temiz bir şekilde yeniden ekle
        self.add_new_chat_to_ui(chat_name, is_group=True)

        # 4. Yeni oluşturulan widget'ı bul ve verileri enjekte et
        for i in range(self.chat_screens_stack.count()):
            widget = self.chat_screens_stack.widget(i)
            if getattr(widget, 'contact_name', None) == chat_name:
                widget.current_chat_id = chat_id
                widget.is_group = True
                widget.members = members

                # Ekranı bu gruba odakla
                self.chat_screens_stack.setCurrentIndex(i)
                break

        # 5. KRİTİK: Arama kutusunu kapatmadan ÖNCE geçmişi yükle sinyalini gönder
        # Bu sinyal ChatController -> ChatService -> Server yolunu izleyip mesajları getirir
        self.load_history_signal.emit(chat_name)

        self.clear_search_results()
        self.search_input.clear()

    def add_new_chat_to_ui(self, chat_name, last_message="", is_group=False, unread_count=0):
        # Mükerrer kontrolü: Zaten bu isimde bir chat varsa ekleme
        for i in range(self.chat_screens_stack.count()):
            widget = self.chat_screens_stack.widget(i)
            if hasattr(widget, 'contact_name') and widget.contact_name == chat_name:
                self.chat_screens_stack.setCurrentIndex(i)
                return

        new_stack_index = self.chat_screens_stack.count()
        new_chat_item = self.create_chat_item(
            name=chat_name,
            last_message=last_message,
            time="",
            unread_count=unread_count,
            stack_index=new_stack_index,
            is_group=is_group
        )
        self.scroll_layout.insertWidget(0, new_chat_item)
        new_chat_screen = self.create_individual_chat_screen(chat_name, is_group=is_group)
        self.chat_screens_stack.addWidget(new_chat_screen)

    def on_attach_clicked(self, chat_name):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Resim Seç", "", "Resim Dosyaları (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if file_path:
            self.send_image_signal.emit(chat_name, file_path)

    def on_send_clicked(self, chat_name, input_field):
        text = input_field.text().strip()
        if text:  # Boş mesaj gitmesin
            self.send_message_signal.emit(chat_name, text)
            input_field.clear()  # Gönderdikten sonra kutuyu temizle
            # Gönderince yazmayı durdur
            self._on_typing_stopped(chat_name)

    def add_message_to_ui(self, chat_name, content, is_mine=True, status="delivered", read_by=None, message_id=None,
                          timestamp=None, sender_name=None, is_starred=False, msg_type="text"):
        if read_by is None:
            read_by = []

        for i in range(self.chat_screens_stack.count()):
            widget = self.chat_screens_stack.widget(i)
            if hasattr(widget, 'contact_name') and widget.contact_name == chat_name:

                # Duplicate mesaj kontrolü
                if message_id and message_id in getattr(widget, 'displayed_message_ids', set()):
                    break  # Zaten eklendi, tekrar ekleme

                msg_layout = widget.msg_layout
                scroll = widget.scroll

                stretch_item = msg_layout.takeAt(msg_layout.count() - 1)
                
                is_group = getattr(widget, 'is_group', False)

                if is_mine:
                    # Mesaj benimse: JSON'a gidecek isim kendi ismim, arayüzde görünecek isim None
                    data_sender = self.current_username
                    display_sender = None
                else:
                    # JSON'a gidecek isim: Eğer grup değilse chat_name, grup ise gelen sender_name
                    data_sender = sender_name if (is_group and sender_name) else chat_name
                    # Arayüzde görünecek isim: Sadece gruplarda isim yazsın
                    display_sender = data_sender if is_group else None

                bubble, status_label = self._create_message_bubble(
                    content, is_mine, status, read_by, timestamp,
                    sender_name=display_sender,  # Sadece görsel için
                    message_id=message_id,
                    is_starred=is_starred,
                    real_data_sender=data_sender,
                    msg_type=msg_type,
                    is_group=is_group,
                    member_count=len(getattr(widget, 'members', [])) if is_group else 2
                )
                msg_layout.addWidget(bubble)

                msg_layout.addStretch()

                if message_id:
                    widget.displayed_message_ids.add(message_id)

                if is_mine and message_id and status_label:
                    widget.message_status_labels[message_id] = status_label

                QApplication.processEvents()
                scroll.verticalScrollBar().setValue(
                    scroll.verticalScrollBar().maximum()
                )

                # --- YENİ: Okundu Bilgisi Gönder (Eğer mesaj benim değilse ve ekran açıksa) ---
                if not is_mine and message_id:
                    current_idx = self.chat_screens_stack.currentIndex()
                    if current_idx == i: # Şu an bu sohbet ekranı mı açık?
                        chat_id = getattr(widget, 'current_chat_id', chat_name)
                        self.mark_messages_read_signal.emit(str(chat_id), [message_id])
                break

        self.update_chat_last_message(chat_name, content, is_mine, msg_type=msg_type)

    def _create_message_bubble(self, content, is_mine, status="delivered", read_by=None, timestamp=None,
                               sender_name=None, real_data_sender=None, message_id=None, is_starred=False,
                               msg_type="text", is_group=False, member_count=2):
        if read_by is None:
            read_by = []

        import datetime

        time_str = ""
        if timestamp:
            try:
                dt = datetime.datetime.fromtimestamp(float(timestamp))
                time_str = dt.strftime("%H:%M")
            except (ValueError, OSError, OverflowError, TypeError):
                time_str = ""

        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")

        w_layout = QHBoxLayout(wrapper)
        w_layout.setContentsMargins(8, 3, 8, 3)
        w_layout.setSpacing(0)

        bubble_frame = QFrame()
        bubble_frame.setMinimumWidth(60)
        bubble_frame.setMaximumWidth(420)
        bubble_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        bubble_layout = QVBoxLayout(bubble_frame)
        bubble_layout.setContentsMargins(10, 6, 10, 5)
        bubble_layout.setSpacing(3)

        if sender_name and not is_mine:
            sender_label = QLabel(sender_name)
            sender_label.setStyleSheet("""
                QLabel {
                    background: transparent;
                    color: #3b82f6;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 0px;
                }
            """)
            sender_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
            bubble_layout.addWidget(sender_label)

        text_label = QLabel(content)
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        text_label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #111b21;
                font-size: 14px;
                padding: 0px;
            }
        """)
        text_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        text_label.setMinimumHeight(0)

        image_label = None
        if msg_type == "image":
            import base64
            try:
                image_label = QLabel()
                image_label.setAlignment(Qt.AlignCenter)

                # Base64 -> QPixmap
                img_data = base64.b64decode(content)
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)

                # Boyutu sınırla
                scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_label.setPixmap(scaled_pixmap)
                image_label.setStyleSheet("border-radius: 4px; background: transparent;")

                # Eğer şifreli değilse (veya çözülmüşse) ve content Base64 ise text_label'ı gizle
                # Ancak [Şifreli Resim] gibi placeholder'ları göstermek isteyebiliriz.
                if content.startswith("[") and content.endswith("]"):
                    pass  # Placeholder'ı göster
                else:
                    text_label.setVisible(False)
            except Exception as e:
                print(f"[UI HATA] Resim yüklenemedi: {e}")
                image_label = None

        time_label = QLabel(time_str)
        time_label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #667781;
                font-size: 11px;
                padding: 0px;
            }
        """)
        time_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        status_label = None

        if is_mine:
            bubble_frame.setStyleSheet("""
                QFrame {
                    background-color: #dcf8c6;
                    border-radius: 8px;
                }
            """)

            others_read = [u for u in read_by if u]

            if len(others_read) >= 1 or status == "read":
                tick_text = "✓✓"
                tick_color = "#3b82f6"
                tick_weight = "bold"
            else:
                tick_text = "✓✓"
                tick_color = "#667781"
                tick_weight = "normal"

            status_label = QLabel(tick_text)
            status_label.setStyleSheet(f"""
                QLabel {{
                    background: transparent;
                    color: {tick_color};
                    font-size: 11px;
                    font-weight: {tick_weight};
                    padding: 0px;
                }}
            """)
            status_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        else:
            bubble_frame.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border-radius: 8px;
                }
            """)

        fm = text_label.fontMetrics()
        text_width = fm.horizontalAdvance(content)

        max_text_width = 330

        if text_width > max_text_width:
            text_label.setFixedWidth(max_text_width)
            bubble_frame.setFixedWidth(360)
        else:
            extra_width = 75 if is_mine else 55
            bubble_width = text_width + extra_width + 20

            if bubble_width < 70:
                bubble_width = 70

            if bubble_width > 360:
                bubble_width = 360

            text_label.setMaximumWidth(bubble_width - 20)
            bubble_frame.setFixedWidth(bubble_width)

        if image_label:
            bubble_layout.addWidget(image_label)
        bubble_layout.addWidget(text_label)

        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(3)

        bottom_row.addStretch()

        initial_text = "⭐" if is_starred else "☆"
        initial_color = "#eab308" if is_starred else "#8696a0"

        star_btn = QPushButton(initial_text)
        star_btn.message_id = str(message_id)
        star_btn.setFixedSize(16, 16)
        star_btn.setCursor(QCursor(Qt.PointingHandCursor))
        star_btn.setStyleSheet(
            f"QPushButton {{ border: none; background: transparent; color: {initial_color}; font-size: 14px; }}")
        star_btn.setVisible(True)

        star_btn.clicked.connect(
            lambda checked=False, mid=message_id, cont=content, sdr=real_data_sender, btn=star_btn:
            self._handle_star_click(mid, cont, sdr, btn)
        )

        bottom_row.addWidget(star_btn)
        if is_mine and status_label is not None:
            bottom_row.addWidget(status_label)
        bottom_row.addWidget(time_label)

        bubble_layout.addLayout(bottom_row)

        if is_mine:
            w_layout.addStretch()
            w_layout.addWidget(bubble_frame)
        else:
            w_layout.addWidget(bubble_frame)
            w_layout.addStretch()

        return wrapper, status_label

    def _handle_star_click(self, message_id, content, sender, button_widget):
        if not message_id: return

        try:
            # Eğer zaten yıldızlıysa hiçbir şey yapma
            if button_widget.text() == "⭐":
                return

            # Sadece yıldızlama yap (tek yönlü)
            button_widget.setText("⭐")
            button_widget.setStyleSheet("color: #eab308; border: none; background: transparent; font-size: 16px;")
            action = "star"

            # 2. Giriş yapan asıl kullanıcıyı bul (starred_by için)
            current_user = self.current_username

            main_win = self.window()

            # 3. Mesajı gönderen ismini belirle
            if sender == "Siz" or not sender:
                real_sender = current_user
            else:
                real_sender = sender

            # 4. Veriyi paketle
            star_data = {
                "message_id": str(message_id),
                "content": content,
                "sender": real_sender,
                "chat_name": getattr(self.chat_screens_stack.currentWidget(), 'contact_name', 'Bilinmiyor'),
                "action": action,
                "timestamp": int(time.time()),
                "starred_by": current_user
            }

            print(f"[DEBUG] Sunucuya giden veri: Sender={real_sender}, StarredBy={current_user}")

            # 5. Debug ve Emit
            print(f"[DEBUG] Sinyal gönderiliyor: {star_data}")
            self.star_message_signal.emit(star_data)

        except Exception as e:
            print(f"[HATA] Yıldızlama sırasında bir sorun oluştu: {e}")

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

    def show_group_members(self, group_name):
        # chat_id'yi bul ve sinyal fırlat
        chat_id = None
        for i in range(self.chat_screens_stack.count()):
            w = self.chat_screens_stack.widget(i)
            if getattr(w, 'contact_name', None) == group_name:
                chat_id = getattr(w, 'current_chat_id', None)
                break
        
        if chat_id:
            self.request_group_info_signal.emit(chat_id)

    def open_group_members_dialog(self, payload):
        status = payload.get("status")
        if status == "success":
            group_name = payload.get("chat_name")
            members = payload.get("members", [])
            dialog = GroupMembersDialog(group_name, members, self)
            dialog.exec_()
        else:
            QMessageBox.warning(self, "Hata", payload.get("message", "Grup bilgisi alınamadı."))

    def on_search_changed(self, text):
        print(f"[DEBUG] Arama kutusu değişti: {text}")
        if text.strip():
            self.search_query_signal.emit(text.strip())
        else:
            self.clear_search_results()

    def show_search_results(self, results: list):
        self.clear_search_results()
        for item in results:
            result_item = self.create_search_result_item(item)
            self.scroll_layout.insertWidget(0, result_item)

    def clear_search_results(self):
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'is_search_result') and widget.is_search_result:
                    self.scroll_layout.removeWidget(widget)
                    widget.deleteLater()

    def create_search_result_item(self, item_data: dict):
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

        is_group = item_data.get("is_group", False)

        avatar_char = "👥" if is_group else "👤"
        display_name = item_data.get("chat_name") if is_group else item_data.get("fullname")
        sub_info = "Grup Sohbeti" if is_group else f"@{item_data.get('username')}"

        avatar = QLabel(avatar_char)
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("background-color: #dfe5e7; border-radius: 25px; font-size: 24px;")

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        name_label = QLabel(display_name)
        name_label.setStyleSheet("font-size: 16px; color: #111b21; font-weight: 500;")

        info_label = QLabel(sub_info)
        info_label.setStyleSheet("font-size: 13px; color: #667781;")

        text_layout.addWidget(name_label)
        text_layout.addWidget(info_label)

        layout.addWidget(avatar)
        layout.addLayout(text_layout)
        layout.addStretch()

        # Tıklama olayı
        if is_group:
            # Gruba tıklandığında sol listeye geri ekle
            item_frame.clicked.connect(lambda: self._add_existing_group_back(item_data))
        else:
            # Kullanıcıya tıklandığında sohbet başlat
            username = item_data.get("username")
            item_frame.clicked.connect(lambda: self.start_chat_signal.emit(username))

        return item_frame

    def _add_existing_group_back(self, group_data):
        chat_name = group_data.get("chat_name")
        chat_id = group_data.get("chat_id")

        # 1. Eğer arayüzde (sohbetlerde) zaten varsa sadece ona geç
        for i in range(self.chat_screens_stack.count()):
            widget = self.chat_screens_stack.widget(i)
            if getattr(widget, 'contact_name', None) == chat_name:
                self.switch_to_chat(chat_name)
                return

        # 2. Arayüzde yoksa (silinmiş/gizlenmişse) yeniymiş gibi ekle
        self.add_new_chat_to_ui(chat_name, is_group=True)

        # 3. Son eklenen widget'a chat_id'yi geri ver
        last_widget = self.chat_screens_stack.widget(self.chat_screens_stack.count() - 1)
        last_widget.current_chat_id = chat_id

        # 4. Arama kutusunu temizle ve o sohbete odaklan
        self.clear_search_results()
        self.search_input.clear()
        self.switch_to_chat(chat_name)

    def update_chat_last_message(self, chat_name, content, is_mine, msg_type="text"):
        prefix = "Sen: " if is_mine else ""
        if msg_type == "image":
            display_text = f"{prefix}📷 Fotoğraf"
        else:
            display_text = f"{prefix}{content}"

        import datetime
        time_str = datetime.datetime.now().strftime("%H:%M")

        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'contact_name') and widget.contact_name == chat_name:
                    # Metni ve zamanı güncelle
                    if hasattr(widget, 'msg_label'):
                        widget.msg_label.setText(display_text)
                    if hasattr(widget, 'time_label'):
                        widget.time_label.setText(time_str)
                    
                    # Stil güncelleme (Okunmamışsa kalın kalsın)
                    unread = getattr(widget, 'unread_count', 0) > 0
                    if unread:
                        widget.msg_label.setStyleSheet("font-size: 13px; color: #111b21; font-weight: bold;")
                        widget.time_label.setStyleSheet("font-size: 12px; color: #3b82f6; font-weight: bold;")
                    else:
                        widget.msg_label.setStyleSheet("font-size: 13px; color: #667781;")
                        widget.time_label.setStyleSheet("font-size: 12px; color: #667781;")

                    # Chat'i listenin en üstüne taşı
                    self.scroll_layout.removeWidget(widget)
                    self.scroll_layout.insertWidget(0, widget)
                    break

    def update_chat_unread_count(self, chat_name, count):
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'contact_name') and widget.contact_name == chat_name:
                    widget.unread_count = count
                    if widget.badge_label:
                        widget.info_layout.removeWidget(widget.badge_label)
                        widget.badge_label.deleteLater()
                        widget.badge_label = None

                    if count > 0:
                        widget.msg_label.setStyleSheet("font-size: 13px; color: #111b21; font-weight: bold;")
                        widget.time_label.setStyleSheet("font-size: 12px; color: #3b82f6; font-weight: bold;")
                        badge = QLabel(str(count))
                        badge.setFixedSize(20, 20)
                        badge.setAlignment(Qt.AlignCenter)
                        badge.setStyleSheet(
                            "background-color: #3b82f6; color: white; border-radius: 10px; font-size: 11px; font-weight: bold;")
                        widget.info_layout.addWidget(badge, alignment=Qt.AlignRight)
                        widget.badge_label = badge
                    else:
                        widget.msg_label.setStyleSheet("font-size: 13px; color: #667781;")
                        widget.time_label.setStyleSheet("font-size: 12px; color: #667781;")
                    break

    def switch_to_chat(self, chat_name):
        for i in range(self.chat_screens_stack.count()):
            widget = self.chat_screens_stack.widget(i)
            if hasattr(widget, 'contact_name') and widget.contact_name == chat_name:
                self.chat_screens_stack.setCurrentIndex(i)
                self.load_history_signal.emit(chat_name)
                
                # --- YENİ: Sohbet açıldığında tüm mesajları okundu işaretle ---
                chat_id = getattr(widget, 'current_chat_id', None)
                if chat_id:
                    # widget.displayed_message_ids içindeki tüm ID'leri gönder (veya son 50'yi)
                    ids = list(widget.displayed_message_ids)
                    if ids:
                        self.mark_messages_read_signal.emit(str(chat_id), ids)
                
                # Okunmamış mesaj sayısını sıfırla
                self.update_chat_unread_count(chat_name, 0)
                break

    def create_chatbot_item(self):
        item_frame = ClickableFrame()
        item_frame.contact_name = "__chatbot__"
        item_frame.setFixedHeight(75)
        item_frame.setCursor(QCursor(Qt.PointingHandCursor))
        # ESKİ: mavi border ve açık mavi arka plan
        # YENİ: daha soft, zarif görünüm
        item_frame.setStyleSheet("""
            QFrame { background-color: #f8f9fa; border-bottom: 1px solid #e9ecef; }
            QFrame:hover { background-color: #f0f2f5; }
        """)
        item_frame.clicked.connect(self.switch_to_chatbot)

        layout = QHBoxLayout(item_frame)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        avatar = QLabel("🤖")
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignCenter)
        # ESKİ: düz mavi daire
        # YENİ: gradient efektli mor-mavi
        avatar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #667eea, stop:1 #764ba2);
            border-radius: 25px;
            font-size: 24px;
        """)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignVCenter)

        name_label = QLabel("AI Asistan")
        name_label.setStyleSheet("font-size: 15px; color: #111b21; font-weight: 700;")

        sub_label = QLabel("✨ Gemini destekli")
        sub_label.setStyleSheet("font-size: 12px; color: #667781;")

        text_layout.addWidget(name_label)
        text_layout.addWidget(sub_label)

        layout.addWidget(avatar)
        layout.addLayout(text_layout)
        layout.addStretch()

        return item_frame

    def switch_to_chatbot(self):
        """Chatbot ekranına geçer, yoksa oluşturur."""
        # Daha önce oluşturulduysa bul ve göster
        for i in range(self.chat_screens_stack.count()):
            widget = self.chat_screens_stack.widget(i)
            if getattr(widget, 'contact_name', None) == "__chatbot__":
                self.chat_screens_stack.setCurrentIndex(i)
                return

        # İlk kez açılıyorsa oluştur
        chatbot_screen = self.create_chatbot_screen()
        self.chat_screens_stack.addWidget(chatbot_screen)
        self.chat_screens_stack.setCurrentIndex(self.chat_screens_stack.count() - 1)

    def create_chatbot_screen(self):
        """Sağ tarafta açılacak chatbot sohbet ekranı."""
        from PyQt5.QtWidgets import QSizePolicy

        chat_frame = QFrame()
        chat_frame.setStyleSheet("background-color: #efeae2;")
        chat_frame.contact_name = "__chatbot__"

        layout = QVBoxLayout(chat_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── ÜST BAR ──────────────────────────────────────────
        top_bar = QFrame()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet("background-color: #f0f2f5; border-bottom: 1px solid #d1d7db;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 0, 10, 0)

        avatar = QLabel("🤖")
        avatar.setFixedSize(40, 40)
        avatar.setStyleSheet("background-color: #3b82f6; border-radius: 20px; font-size: 20px;")
        avatar.setAlignment(Qt.AlignCenter)

        name_label = QLabel("AI Asistan")
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #111b21;")

        sub_label = QLabel("Gemini 1.5 Flash")
        sub_label.setStyleSheet("font-size: 12px; color: #667781;")

        name_layout = QVBoxLayout()
        name_layout.setSpacing(0)
        name_layout.addWidget(name_label)
        name_layout.addWidget(sub_label)

        reset_btn = QPushButton("🔄")
        reset_btn.setFixedSize(35, 35)
        reset_btn.setToolTip("Sohbeti Sıfırla")
        reset_btn.setCursor(QCursor(Qt.PointingHandCursor))
        reset_btn.setStyleSheet("""
            QPushButton { border: none; font-size: 18px; border-radius: 17px; background-color: transparent; }
            QPushButton:hover { background-color: #e4e6eb; }
        """)
        reset_btn.clicked.connect(self.reset_chatbot_conversation)

        top_layout.addWidget(avatar)
        top_layout.addSpacing(8)
        top_layout.addLayout(name_layout)
        top_layout.addStretch()
        top_layout.addWidget(reset_btn)

        # ── MESAJ ALANI ──────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        msg_container = QWidget()
        msg_container.setStyleSheet("background-color: #efeae2;")

        msg_layout = QVBoxLayout(msg_container)
        msg_layout.setContentsMargins(10, 10, 10, 10)
        msg_layout.setSpacing(6)
        msg_layout.addStretch()

        scroll.setWidget(msg_container)

        chat_frame.msg_layout = msg_layout
        chat_frame.scroll = scroll
        chat_frame.typing_bubble = None  # "Yazıyor..." balonunu takip etmek için

        # ── ALT BAR ──────────────────────────────────────────
        bottom_bar = QFrame()
        bottom_bar.setFixedHeight(60)
        bottom_bar.setStyleSheet("background-color: #f0f2f5;")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(10, 10, 10, 10)

        msg_input = QLineEdit()
        msg_input.setPlaceholderText("AI Asistana bir şey sorun...")
        msg_input.setStyleSheet("""
            background-color: #ffffff; border: none;
            border-radius: 8px; padding: 10px; font-size: 14px;
        """)

        send_btn = QPushButton("➤")
        send_btn.setFixedSize(40, 40)
        send_btn.setCursor(QCursor(Qt.PointingHandCursor))
        send_btn.setStyleSheet("font-size: 20px; border: none; color: #3b82f6; background: transparent;")

        def on_send():
            text = msg_input.text().strip()
            if text:
                self.send_chatbot_message_signal.emit(text)
                msg_input.clear()

        send_btn.clicked.connect(on_send)
        msg_input.returnPressed.connect(on_send)

        bottom_layout.addWidget(msg_input)
        bottom_layout.addWidget(send_btn)

        layout.addWidget(top_bar)
        layout.addWidget(scroll)
        layout.addWidget(bottom_bar)

        return chat_frame

    def add_chatbot_message_to_ui(self, content: str, is_mine: bool, is_typing: bool = False):
        """Chatbot ekranına mesaj balonu ekler."""
        for i in range(self.chat_screens_stack.count()):
            widget = self.chat_screens_stack.widget(i)
            if getattr(widget, 'contact_name', None) == "__chatbot__":
                msg_layout = widget.msg_layout
                scroll = widget.scroll

                msg_layout.takeAt(msg_layout.count() - 1)  # stretch'i kaldır
                bubble, _ = self._create_message_bubble(
                    content, is_mine,
                    status="read",
                    read_by=["bot"] if is_mine else [],
                    timestamp=None
                )

                msg_layout.addWidget(bubble)

                if is_typing:
                    widget.typing_bubble = bubble  # referansı sakla

                msg_layout.addStretch()

                QApplication.processEvents()
                scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
                break

    def remove_chatbot_typing_indicator(self):
        """'Yazıyor...' balonunu kaldırır."""
        for i in range(self.chat_screens_stack.count()):
            widget = self.chat_screens_stack.widget(i)
            if getattr(widget, 'contact_name', None) == "__chatbot__":
                if widget.typing_bubble:
                    widget.msg_layout.removeWidget(widget.typing_bubble)
                    widget.typing_bubble.deleteLater()
                    widget.typing_bubble = None
                break

    def reset_chatbot_conversation(self):
        """🔄 butonuna basınca sohbet geçmişini temizler."""
        # Sinyal yoluyla servise ulaşmak yerine direkt controller üzerinden çağrılır
        # Bu yüzden bu sinyali de tanımlıyoruz:
        self.reset_chatbot_signal.emit()

        # UI'daki mesajları temizle
        for i in range(self.chat_screens_stack.count()):
            widget = self.chat_screens_stack.widget(i)
            if getattr(widget, 'contact_name', None) == "__chatbot__":
                msg_layout = widget.msg_layout
                # Stretch hariç tüm widget'ları sil
                while msg_layout.count() > 1:
                    item = msg_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                break

    def update_message_read_status(self, chat_id, message_ids, read_by, all_read=False):
        """Sunucudan gelen okundu bilgisini UI'daki ilgili mesajlara yansıtır."""
        for i in range(self.chat_screens_stack.count()):
            widget = self.chat_screens_stack.widget(i)
            # chat_id kontrolü (community_id veya chat_id olabilir)
            current_id = getattr(widget, 'current_chat_id', None)
            if current_id == chat_id or f"community_{current_id}" == chat_id:
                for msg_id in message_ids:
                    if msg_id in widget.message_status_labels:
                        label = widget.message_status_labels[msg_id]
                        is_group = getattr(widget, 'is_group', False)
                        
                        # MAVİ TIK ŞARTI:
                        # Eğer gruptaysak sadece 'all_read' geldiğinde mavi yap.
                        # Eğer grupta değilsek her zaman mavi yap (çünkü zaten tek kişi okuyabilir).
                        should_be_blue = all_read or not is_group
                        
                        if should_be_blue:
                            label.setText("✓✓")
                            label.setStyleSheet("color: #34b7f1; font-weight: bold; font-size: 14px;")
                        else:
                            # Grup ama henüz herkes okumadıysa gri çift tık kalabilir
                            label.setText("✓✓")
                            label.setStyleSheet("color: #667781; font-weight: normal; font-size: 14px;")
                break

    def reset_ui(self):
        # sol taraftaki sohbet listesini temizle
        # Stretch (en alttaki boşluk) hariç tüm sohbet kartlarını siler
        while self.scroll_layout.count() > 0:
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # sağ taraftaki mesaj ekranlarını temizle (StackedWidget)
        # sadece 0. indeksteki Hoş Geldin ekranını bırak, diğerlerini sil
        while self.chat_screens_stack.count() > 1:
            widget = self.chat_screens_stack.widget(1)
            self.chat_screens_stack.removeWidget(widget)
            widget.deleteLater()

        # hoş geldin ekranına geri dön
        self.main_stack.setCurrentIndex(0)
        self.chat_screens_stack.setCurrentIndex(0)

        # arama kutusunu temizle
        if hasattr(self, 'search_input'):
            self.search_input.clear()

        if hasattr(self, 'settings_page'):
            self.settings_page.clear_all_data()

        print("[UI] Tüm arayüz bileşenleri sıfırlandı.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainPageUI()
    window.setWindowTitle("OnlineChat - Ana Ekran")
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec_())
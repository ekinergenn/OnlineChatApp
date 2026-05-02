import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QStackedWidget, QApplication
)
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QAbstractButton
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt


class ModernSwitch(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(50, 26)
        self.checked_color = QColor("#3b82f6")
        self.unchecked_color = QColor("#b1b3b5")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Arka plan rengini belirle
        bg_color = self.checked_color if self.isChecked() else self.unchecked_color

        # Dış kapsül
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 13, 13)

        # beyaz yuvarlak
        painter.setBrush(QColor("white"))
        # Eğer açıksa sağa, kapalıysa sola çiz
        dot_x = 26 if self.isChecked() else 4
        painter.drawEllipse(dot_x, 3, 20, 20)

        painter.end()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.update()  # Rengi ve konumu güncellemek için


class SettingsPageUI(QWidget):
    def __init__(self, main_page, parent=None):
        super().__init__(parent)
        self.main_page_ref = main_page
        self.init_ui()

    def init_ui(self):
        # Ana yatay layout (Sütun 2 + Sütun 3)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # 2. SÜTUN: AYAR LİSTESİ
        self.settings_list_panel = QFrame()
        self.settings_list_panel.setFixedWidth(500)  # MainPage'deki sohbet listesiyle aynı genişlik
        self.settings_list_panel.setStyleSheet("background-color: #ffffff; border-right: 1px solid #d1d7db;")

        list_layout = QVBoxLayout(self.settings_list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)

        # Başlık
        header = QLabel("Ayarlar")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #111b21; padding: 25px 20px 15px 20px;")
        list_layout.addWidget(header)

        # scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(15, 0, 15, 0)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        # butonlar
        self.yildiz_btn = self.create_setting_button("🌟", "Yıldızlı Mesajlar",
                                                     "Yıldızladığın mesajlarını görüntüle, düzenle.", 1)
        self.scroll_layout.addWidget(self.yildiz_btn)
        self.gizlilik_btn = self.create_setting_button("🔐", "Gizlilik", "Engellenen kişiler, çevrimiçi bilgisi...", 2)
        self.scroll_layout.addWidget(self.gizlilik_btn)
        self.bildirimler_btn = self.create_setting_button("🔔", "Bildirimler", "Mesaj sesleri ve grup uyarıları", 3)
        self.scroll_layout.addWidget(self.bildirimler_btn)
        self.tema = self.create_theme_toggle("🌓", "Karanlık Mod", "Gözlerinizi dinlendirin")  # indexi 4
        self.scroll_layout.addWidget(self.tema)
        self.yardim_btn = self.create_setting_button("❓", "Yardım", "Yardım merkezi, bize ulaşın", 5)
        self.scroll_layout.addWidget(self.yardim_btn)

        scroll.setWidget(scroll_content)
        list_layout.addWidget(scroll)
        self.layout.addWidget(self.settings_list_panel)

        # --- 3. SÜTUN: AYAR DETAYLARI (StackedWidget) ---
        self.details_stack = QStackedWidget()

        # İndeks 0: Hoş Geldin
        self.details_stack.addWidget(self.create_welcome_page())

        # İndeks 1: YILDIZLI MESAJLAR (Asıl sayfa)
        self.starred_page = self.create_starred_page()
        self.details_stack.addWidget(self.starred_page)

        # Diğer boş sayfalar (2, 3, 4, 5)
        self.privacy_page = self.create_privacy_page()
        self.details_stack.addWidget(self.privacy_page)
        self.details_stack.addWidget(self.create_empty_detail_page("Bildirimler", "Bildirim ayarları yakında burada."))
        self.details_stack.addWidget(self.create_empty_detail_page("Görünüm", "Karanlık mod ayarları aktif."))
        self.details_stack.addWidget(self.create_empty_detail_page("Yardım", "Yardım merkezi yakında burada."))

        self.layout.addWidget(self.details_stack)

    def create_welcome_page(self):
        page = QFrame()
        page.setStyleSheet("background-color: #f0f2f5;")
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        icon = QLabel("⚙️")
        icon.setStyleSheet("font-size: 80px; color: #667781;")
        title = QLabel("Uygulama Ayarları")
        title.setStyleSheet("font-size: 24px; color: #111b21; font-weight: 300;")
        layout.addStretch()
        layout.addWidget(icon, alignment=Qt.AlignCenter)
        layout.addWidget(title, alignment=Qt.AlignCenter)
        layout.addStretch()
        return page

    def create_starred_page(self):
        # yıldızlı mesajların listeleneceği sayfa
        page = QFrame()
        page.setStyleSheet("background-color: #f0f2f5;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        # Üst Bilgi
        header = QFrame()
        header.setFixedHeight(65)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #d1d7db;")
        h_layout = QHBoxLayout(header)
        h_layout.addWidget(
            QLabel("Yıldızlı Mesajlar", styleSheet="font-size: 18px; font-weight: bold; color: #111b21;"))
        layout.addWidget(header)

        # Liste Alanı
        self.starred_scroll = QScrollArea()
        self.starred_scroll.setWidgetResizable(True)
        self.starred_scroll.setStyleSheet("border: none; background: transparent;")

        self.starred_container = QWidget()
        self.starred_list_layout = QVBoxLayout(self.starred_container)
        self.starred_list_layout.setContentsMargins(20, 20, 20, 20)
        self.starred_list_layout.setSpacing(12)
        self.starred_list_layout.setAlignment(Qt.AlignTop)

        self.starred_scroll.setWidget(self.starred_container)
        layout.addWidget(self.starred_scroll)
        return page

    def create_privacy_toggle(self, icon, title, subtitle):
        frame = QFrame()
        frame.setFixedHeight(85)
        frame.setStyleSheet("""
            QFrame { background-color: #ffffff; border: 1px solid #f0f2f5; border-radius: 12px; }
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 0, 15, 0)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 20px; border: none; background: transparent;")

        text_container = QWidget()
        text_container.setStyleSheet("background: transparent; border: none;")
        v_layout = QVBoxLayout(text_container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(2)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 16px; font-weight: 500; color: #111b21; border: none;")
        st_lbl = QLabel(subtitle)
        st_lbl.setStyleSheet("font-size: 13px; color: #667781; border: none;")

        v_layout.addWidget(t_lbl)
        v_layout.addWidget(st_lbl)

        switch = ModernSwitch()

        layout.addWidget(icon_lbl)
        layout.addWidget(text_container)
        layout.addStretch()
        layout.addWidget(switch)

        return frame, switch

    def create_privacy_page(self):
        page = QFrame()
        page.setStyleSheet("background-color: #f0f2f5;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QFrame()
        header.setFixedHeight(65)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #d1d7db;")
        h_layout = QHBoxLayout(header)
        h_layout.addWidget(
            QLabel("Gizlilik Ayarları", styleSheet="font-size: 18px; font-weight: bold; color: #111b21;"))
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        container = QWidget()
        v_layout = QVBoxLayout(container)
        v_layout.setContentsMargins(20, 20, 20, 20)
        v_layout.setSpacing(12)
        v_layout.setAlignment(Qt.AlignTop)

        frame1, self.switch_online = self.create_privacy_toggle("🟢", "Çevrimiçi Görünürlüğü",
                                                                "Çevrimiçi olduğunuzu diğer kullanıcılar görebilir.")
        frame2, self.switch_last_seen = self.create_privacy_toggle("🕒", "Son Görülme",
                                                                   "Son görülme zamanınızı diğer kullanıcılar görebilir.")
        frame3, self.switch_read_receipts = self.create_privacy_toggle("✔", "Okundu Bilgisi",
                                                                       "Mesajları okuduğunuzda karşı tarafa mavi tik gider.")

        self.switch_online.setChecked(True)
        self.switch_last_seen.setChecked(True)
        self.switch_read_receipts.setChecked(True)

        self.switch_online.toggled.connect(self._on_privacy_changed)
        self.switch_last_seen.toggled.connect(self._on_privacy_changed)
        self.switch_read_receipts.toggled.connect(self._on_privacy_changed)

        v_layout.addWidget(frame1)
        v_layout.addWidget(frame2)
        v_layout.addWidget(frame3)

        blocked_header = QLabel("Engellenen Kişiler")
        blocked_header.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #111b21; margin-top: 15px; margin-bottom: 5px;")
        v_layout.addWidget(blocked_header)

        self.blocked_list_layout = QVBoxLayout()
        self.blocked_list_layout.setContentsMargins(0, 0, 0, 0)
        self.blocked_list_layout.setSpacing(5)
        v_layout.addLayout(self.blocked_list_layout)

        scroll.setWidget(container)
        layout.addWidget(scroll)
        return page

    def _on_privacy_changed(self, checked=None):
        settings = {
            "online_status": self.switch_online.isChecked(),
            "last_seen": self.switch_last_seen.isChecked(),
            "read_receipts": self.switch_read_receipts.isChecked()
        }
        if hasattr(self.main_page_ref, 'update_privacy_settings_signal'):
            self.main_page_ref.update_privacy_settings_signal.emit(settings)

    def load_blocked_users(self, blocked_users_list):
        while self.blocked_list_layout.count() > 0:
            item = self.blocked_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not blocked_users_list:
            lbl = QLabel("Engellenen kişi bulunmuyor.")
            lbl.setStyleSheet("color: #667781; font-size: 13px; background: transparent; border: none;")
            self.blocked_list_layout.addWidget(lbl)
            return

        for user_data in blocked_users_list:
            card = QFrame()
            card.setFixedHeight(60)
            card.setStyleSheet("background-color: #ffffff; border: 1px solid #f0f2f5; border-radius: 8px;")
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(15, 0, 15, 0)

            name_lbl = QLabel(user_data.get('blocked_username', 'Bilinmeyen'))
            name_lbl.setStyleSheet("font-size: 15px; font-weight: 500; color: #111b21; border: none;")

            unblock_btn = QPushButton("Engellemeyi Kaldır")
            unblock_btn.setCursor(QCursor(Qt.PointingHandCursor))
            unblock_btn.setStyleSheet("""
                QPushButton { background-color: #f0f2f5; color: #ef4444; border: none; border-radius: 6px; padding: 5px 10px; font-weight: bold; }
                QPushButton:hover { background-color: #fee2e2; }
            """)

            def make_unblock_handler(b_id):
                return lambda: self.unblock_user_action(b_id)

            unblock_btn.clicked.connect(make_unblock_handler(user_data.get('blocked_id')))

            card_layout.addWidget(name_lbl)
            card_layout.addStretch()
            card_layout.addWidget(unblock_btn)

            self.blocked_list_layout.addWidget(card)

    def unblock_user_action(self, blocked_id):
        if hasattr(self.main_page_ref, 'unblock_user_from_settings_signal'):
            self.main_page_ref.unblock_user_from_settings_signal.emit(str(blocked_id))

    def load_privacy_settings(self, settings):
        self.switch_online.blockSignals(True)
        self.switch_last_seen.blockSignals(True)
        self.switch_read_receipts.blockSignals(True)

        self.switch_online.setChecked(settings.get("online_status", True))
        self.switch_last_seen.setChecked(settings.get("last_seen", True))
        self.switch_read_receipts.setChecked(settings.get("read_receipts", True))

        self.switch_online.blockSignals(False)
        self.switch_last_seen.blockSignals(False)
        self.switch_read_receipts.blockSignals(False)

    def create_setting_button(self, icon, title, subtitle, index):
        btn = QPushButton()
        btn.setFixedHeight(85)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setStyleSheet("""
            QPushButton { background-color: #ffffff; border: 1px solid #f0f2f5; border-radius: 12px; text-align: left; }
            QPushButton:hover { background-color: #f5f6f6; border: 1px solid #d1d7db; }
            QPushButton:pressed { background-color: #e9edef; }
        """)

        btn_layout = QHBoxLayout(btn)
        btn_layout.setContentsMargins(15, 0, 15, 0)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 20px; border: none; background: transparent;")

        text_container = QWidget()
        text_container.setStyleSheet("background: transparent; border: none;")
        v_layout = QVBoxLayout(text_container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(2)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 16px; font-weight: 500; color: #111b21; border: none;")
        st_lbl = QLabel(subtitle)
        st_lbl.setStyleSheet("font-size: 13px; color: #667781; border: none;")

        v_layout.addWidget(t_lbl)
        v_layout.addWidget(st_lbl)

        btn_layout.addWidget(icon_lbl)
        btn_layout.addWidget(text_container)
        btn_layout.addStretch()

        def on_click():
            self.details_stack.setCurrentIndex(index)
            if index == 1:
                username = getattr(self.main_page_ref, 'current_username', None)

                print(f">>> UI: Yıldızlı mesajlar isteği. Kullanıcı: {username}")
                if not username:
                    main_win = self.window()
                    if hasattr(main_win, 'current_user') and main_win.current_user:
                        username = main_win.current_user.get("username")
                        # Bulduysan main_page'e geri yaz ki bir daha uğraşma
                        self.main_page_ref.current_username = username

                print(f">>> UI: Yıldızlı mesajlar isteği. Kullanıcı: {username}")

                if username and hasattr(self.main_page_ref, 'get_starred_messages_signal'):
                    print(">>> UI: Sinyal fırlatılıyor...")
                    self.main_page_ref.get_starred_messages_signal.emit(username)
                else:
                    print(">>> HATA: Kullanıcı adı (None) veya Sinyal bulunamadı!")
            elif index == 2:
                if hasattr(self.main_page_ref, 'request_blocked_users_signal'):
                    self.main_page_ref.request_blocked_users_signal.emit()

        btn.clicked.connect(on_click)
        return btn

    def create_theme_toggle(self, icon, title, subtitle):
        frame = QFrame()
        frame.setFixedHeight(85)
        frame.setStyleSheet("""
            QFrame { background-color: #ffffff; border: 1px solid #f0f2f5; border-radius: 12px; }
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 0, 15, 0)

        # İkon ve Metinler (Sol Taraf)
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 20px; border: none; background: transparent;")

        text_container = QWidget()
        text_container.setStyleSheet("background: transparent; border: none;")
        v_layout = QVBoxLayout(text_container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(2)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 16px; font-weight: 500; color: #111b21; border: none;")
        st_lbl = QLabel(subtitle)
        st_lbl.setStyleSheet("font-size: 13px; color: #667781; border: none;")

        v_layout.addWidget(t_lbl)
        v_layout.addWidget(st_lbl)

        # Switch Butonu (Sağ Taraf)
        self.theme_switch = ModernSwitch()
        # Tıklandığında yapılacak işlem (Karanlık mod mantığı buraya gelecek)
        self.theme_switch.toggled.connect(self.toggle_dark_mode)

        layout.addWidget(icon_lbl)
        layout.addWidget(text_container)
        layout.addStretch()
        layout.addWidget(self.theme_switch)

        return frame

    def toggle_dark_mode(self, checked):
        if checked:
            print("Karanlık Mod Aktif!")
            # Burada tüm uygulamanın stylesheet'ini değiştirebilirsin
        else:
            print("Aydınlık Mod Aktif!")

    def create_empty_detail_page(self, title_text, desc_text):
        page = QFrame()
        page.setStyleSheet("background-color: #f0f2f5;")
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel(title_text)
        title.setStyleSheet("font-size: 24px; color: #111b21; font-weight: bold;")

        desc = QLabel(desc_text)
        desc.setStyleSheet("font-size: 14px; color: #667781; margin-top: 10px;")

        layout.addWidget(title, alignment=Qt.AlignCenter)
        layout.addWidget(desc, alignment=Qt.AlignCenter)
        return page

    def add_starred_message_card(self, star_data):
        # listeye kart ekler
        card = QFrame()
        card.setMinimumHeight(80)
        card.setStyleSheet("""
            QFrame { 
                background-color: #ffffff; 
                border-radius: 8px; 
                border: 1px solid #e9edef; 
            }
            QFrame:hover { border: 1px solid #3b82f6; }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)

        # Üst Satır
        top = QHBoxLayout()
        sender_name = star_data.get('sender', 'Bilinmiyor')
        sender_lbl = QLabel(f"👤 {sender_name}")
        sender_lbl.setStyleSheet("font-weight: bold; color: #3b82f6; border: none;")

        # silme butonu
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(30, 30)
        delete_btn.setCursor(QCursor(Qt.PointingHandCursor))
        delete_btn.setStyleSheet("""
                QPushButton { border: none; background: transparent; font-size: 16px; color: #667781; }
                QPushButton:hover { color: #ef4444; background-color: #fee2e2; border-radius: 15px; }
            """)

        delete_btn.clicked.connect(lambda: self.main_page_ref.unstar_from_settings_signal.emit(star_data))

        chat_lbl = QLabel(f"📍 {star_data.get('chat_name', 'Sohbet')}")
        chat_lbl.setStyleSheet("font-size: 11px; color: #8696a0; border: none;")

        top.addWidget(sender_lbl)
        top.addStretch()
        top.addWidget(chat_lbl)
        top.addWidget(delete_btn)

        # Mesaj İçeriği
        content_lbl = QLabel(star_data.get('content', ''))
        content_lbl.setWordWrap(True)
        content_lbl.setStyleSheet("color: #111b21; font-size: 13px; border: none; background: transparent;")

        bottom = QHBoxLayout()
        bottom.addStretch()

        layout.addLayout(top)
        layout.addWidget(content_lbl)
        layout.addLayout(bottom)

        # Container'a (starred_list_layout) ekle
        self.starred_list_layout.insertWidget(0, card)
        card.show()
        self.starred_container.adjustSize()

    def clear_starred_list(self):
        # yıldızlı mesajlar listesindeki tüm kartları temizle
        while self.starred_list_layout.count() > 0:
            item = self.starred_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.starred_container.adjustSize()

    def clear_all_data(self):
        # oturum kapatıldığında tüm yıldızlı mesaj kartlarını temizle
        while self.starred_list_layout.count() > 0:
            item = self.starred_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.details_stack.setCurrentIndex(0)
        print("[UI] SettingsPage verileri temizlendi.")
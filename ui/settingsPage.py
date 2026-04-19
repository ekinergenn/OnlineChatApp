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
    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.yildiz_btn = self.create_setting_button("🌟", "Yıldızlı Mesajlar", "Yıldızladığın mesajlarını görüntüle, düzenle.", 1)
        self.scroll_layout.addWidget(self.yildiz_btn)
        self.gizlilik_btn = self.create_setting_button("🔐", "Gizlilik", "Engellenen kişiler, çevrimiçi bilgisi...", 2)
        self.scroll_layout.addWidget(self.gizlilik_btn)
        self.bildirimler_btn = self.create_setting_button("🔔", "Bildirimler", "Mesaj sesleri ve grup uyarıları", 3)
        self.scroll_layout.addWidget(self.bildirimler_btn)
        self.tema = self.create_theme_toggle("🌓", "Karanlık Mod", "Gözlerinizi dinlendirin") #indexi 4
        self.scroll_layout.addWidget(self.tema)
        self.yardim_btn = self.create_setting_button("❓", "Yardım", "Yardım merkezi, bize ulaşın", 5)
        self.scroll_layout.addWidget(self.yardim_btn)

        scroll.setWidget(scroll_content)
        list_layout.addWidget(scroll)
        self.layout.addWidget(self.settings_list_panel)

        # --- 3. SÜTUN: AYAR DETAYLARI (StackedWidget) ---
        self.details_stack = QStackedWidget()

        # İNDEKS 0: AYARLAR HOŞ GELDİN EKRANI (Fonksiyon kullanmadan doğrudan oluşturma)
        settings_welcome = QFrame()
        settings_welcome.setStyleSheet("background-color: #f0f2f5;")  # Sağ panel arka planı
        welcome_layout = QVBoxLayout(settings_welcome)
        welcome_layout.addStretch()

        # İkon
        big_settings_icon = QLabel("⚙️")
        big_settings_icon.setStyleSheet("font-size: 80px; color: #667781;")
        big_settings_icon.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(big_settings_icon)

        # Başlık
        s_title = QLabel("Uygulama Ayarları")
        s_title.setStyleSheet("font-size: 28px; color: #111b21; font-weight: 300; margin-top: 20px;")
        s_title.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(s_title)

        # Alt Başlık
        s_subtitle = QLabel("Hesabınızı, bildirimlerinizi ve görünüm<br>tercihlerinizi buradan yönetebilirsiniz.")
        s_subtitle.setStyleSheet("font-size: 14px; color: #667781; line-height: 1.5; margin-top: 10px;")
        s_subtitle.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(s_subtitle)

        welcome_layout.addStretch()

        # Alt Not
        s_info_note = QLabel("🛠️ Değişiklikler otomatik olarak kaydedilir")
        s_info_note.setStyleSheet("font-size: 12px; color: #8696a0; margin-bottom: 20px;")
        s_info_note.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(s_info_note)

        # Stack'e ilk sayfa olarak ekle
        self.details_stack.addWidget(settings_welcome)

        # (Bundan sonra diğer detay sayfalarını eklemeye devam edebilirsin)
        self.layout.addWidget(self.details_stack)

        # Diğer detay sayfaları (Örnek olarak boş sayfalar ekliyoruz)
        for i in range(5):
            self.details_stack.addWidget(self.create_empty_detail_page("Ayar Detayı", f"Bu bölüm yakında eklenecek..."))

        self.layout.addWidget(self.details_stack)

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

        # Tıklama aksiyonu: Sağdaki stack'i değiştir
        btn.clicked.connect(lambda: self.details_stack.setCurrentIndex(index))

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SettingsPageUI()
    window.resize(1100, 800)
    window.show()
    sys.exit(app.exec_())
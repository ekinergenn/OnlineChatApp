import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QScrollArea, QSizePolicy, QStackedWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QCursor
from ui.communityDialog import CommunityDialog

class ClickableFrame(QFrame):
    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

class CommunitiesPageUI(QWidget):
    create_community_signal = pyqtSignal(str)
    join_community_signal = pyqtSignal(int)
    search_query_signal = pyqtSignal(str)
    send_community_message_signal = pyqtSignal(int, str)
    send_community_image_signal = pyqtSignal(int, str) # Yeni: (comm_id, image_path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_username = None
        self.active_communities = {} # {id: widget}
        self.init_ui()

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.communities_page = QWidget()
        self.communities_page_layout = QHBoxLayout(self.communities_page)
        self.communities_page_layout.setContentsMargins(0, 0, 0, 0)
        self.communities_page_layout.setSpacing(0)

        self.create_comunities_list_panel()
        self.create_comunities_screens_stack()

        self.main_layout.addWidget(self.communities_page)

    def create_comunities_list_panel(self):
        communities_list_frame = QFrame()
        communities_list_frame.setFixedWidth(400)
        communities_list_frame.setStyleSheet("background-color: #ffffff; border-right: 1px solid #d1d7db;")

        communities_layout = QVBoxLayout(communities_list_frame)
        communities_layout.setContentsMargins(0, 0, 0, 0)
        communities_layout.setSpacing(0)

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
        add_communities_btn.clicked.connect(self.open_community_dialog)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(add_communities_btn)
        communities_layout.addWidget(header_frame)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        scroll_area.setWidget(scroll_content)
        communities_layout.addWidget(scroll_area)

        self.communities_page_layout.addWidget(communities_list_frame)

    def create_comunities_screens_stack(self):
        self.communities_screens_stack = QStackedWidget()
        welcome_screen = self.create_welcome_screen()
        self.communities_screens_stack.addWidget(welcome_screen)
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

        subtitle = QLabel("Topluluk mesajlarını görüntüleyin.<br>Görüntülemek için soldan bir topluluk seçin.")
        subtitle.setStyleSheet("font-size: 14px; color: #667781; line-height: 1.5; margin-top: 10px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addStretch()
        return welcome_frame

    def open_community_dialog(self):
        self.dialog = CommunityDialog(self)
        self.dialog.create_signal.connect(self.create_community_signal.emit)
        self.dialog.join_signal.connect(self.join_community_signal.emit)
        self.dialog.search_signal.connect(self.search_query_signal.emit)
        self.dialog.exec_()

    def show_search_results(self, results):
        if hasattr(self, 'dialog') and self.dialog.isVisible():
            self.dialog.show_results(results)

    def load_communities(self, communities, current_username):
        self.current_username = current_username
        
        # Temizle
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Stack temizle (welcome hariç)
        while self.communities_screens_stack.count() > 1:
            widget = self.communities_screens_stack.widget(1)
            self.communities_screens_stack.removeWidget(widget)
            widget.deleteLater()

        for comm in communities:
            comm_id = comm["community_id"]
            name = comm["name"]
            creator = comm["creator"]
            messages = comm.get("messages", [])
            
            stack_index = self.communities_screens_stack.count()
            
            # Sol liste öğesi
            last_msg = messages[-1]["content"] if messages else "Henüz mesaj yok"
            item = self.create_communities_item(name, last_msg, "", stack_index)
            self.scroll_layout.addWidget(item)
            
            # Sağ ekran
            screen = self.create_individual_communities_screen(comm_id, name, creator, messages)
            self.communities_screens_stack.addWidget(screen)

    def create_communities_item(self, name, last_message, time, stack_index):
        item_frame = ClickableFrame()
        item_frame.setFixedHeight(75)
        item_frame.setCursor(QCursor(Qt.PointingHandCursor))
        item_frame.setStyleSheet("QFrame { background-color: #ffffff; border-bottom: 1px solid #f0f2f5; } QFrame:hover { background-color: #f5f6f6; }")
        item_frame.clicked.connect(lambda: self.communities_screens_stack.setCurrentIndex(stack_index))

        layout = QHBoxLayout(item_frame)
        avatar = QLabel("📣")
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("background-color: #dfe5e7; border-radius: 25px; font-size: 24px;")

        text_layout = QVBoxLayout()
        name_label = QLabel(name)
        name_label.setStyleSheet("font-size: 16px; color: #111b21; font-weight: 500;")
        msg_label = QLabel(last_message)
        msg_label.setStyleSheet("font-size: 13px; color: #667781;")
        text_layout.addWidget(name_label)
        text_layout.addWidget(msg_label)

        layout.addWidget(avatar)
        layout.addLayout(text_layout)
        layout.addStretch()
        return item_frame

    def create_individual_communities_screen(self, comm_id, name, creator, messages):
        frame = QFrame()
        frame.setStyleSheet("background-color: #efeae2;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        # Üst bar
        top_bar = QFrame()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet("background-color: #f0f2f5; border-bottom: 1px solid #d1d7db;")
        top_layout = QHBoxLayout(top_bar)
        
        avatar = QLabel("📣")
        avatar.setFixedSize(40, 40)
        avatar.setStyleSheet("background-color: #dfe5e7; border-radius: 20px; font-size: 20px;")
        avatar.setAlignment(Qt.AlignCenter)
        
        name_label = QLabel(f"{name} (Kurucu: {creator})")
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #111b21;")
        
        top_layout.addWidget(avatar)
        top_layout.addWidget(name_label)
        top_layout.addStretch()
        layout.addWidget(top_bar)

        # Mesaj alanı
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content_widget = QWidget()
        msg_layout = QVBoxLayout(content_widget)
        msg_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        frame.msg_layout = msg_layout # Referans sakla
        frame.comm_id = comm_id

        # Geçmiş mesajları ekle
        for msg in messages:
            self.add_message_bubble(msg_layout, msg["sender"], msg["content"], msg.get("timestamp"))

        # Giriş alanı (Sadece kurucu görebilir)
        if self.current_username == creator:
            input_frame = QFrame()
            input_frame.setFixedHeight(60)
            input_frame.setStyleSheet("background-color: #f0f2f5; border-top: 1px solid #d1d7db;")
            input_layout = QHBoxLayout(input_frame)

            attach_btn = QPushButton("📎")
            attach_btn.setFixedSize(40, 40)
            attach_btn.setCursor(QCursor(Qt.PointingHandCursor))
            attach_btn.setStyleSheet("border: none; font-size: 20px; color: #667781;")
            attach_btn.clicked.connect(lambda: self.on_attach_clicked(comm_id))
            
            msg_input = QLineEdit()
            msg_input.setPlaceholderText("Duyuru yayınlayın...")
            msg_input.setStyleSheet("border: none; border-radius: 8px; padding: 8px 15px; background: white;")
            
            send_btn = QPushButton("✈️")
            send_btn.setFixedSize(40, 40)
            send_btn.setStyleSheet("border: none; color: #3b82f6; font-size: 20px;")
            send_btn.clicked.connect(lambda: self.on_send_clicked(comm_id, msg_input))
            msg_input.returnPressed.connect(lambda: self.on_send_clicked(comm_id, msg_input))

            input_layout.addWidget(attach_btn)
            input_layout.addWidget(msg_input)
            input_layout.addWidget(send_btn)
            layout.addWidget(input_frame)
        else:
            read_only_label = QLabel("Sadece topluluk kurucusu mesaj gönderebilir.")
            read_only_label.setAlignment(Qt.AlignCenter)
            read_only_label.setStyleSheet("padding: 15px; background: #f0f2f5; color: #667781; border-top: 1px solid #d1d7db;")
            layout.addWidget(read_only_label)

        return frame

    def on_send_clicked(self, comm_id, input_field):
        text = input_field.text().strip()
        if text:
            self.send_community_message_signal.emit(comm_id, text)
            input_field.clear()

    def on_attach_clicked(self, comm_id):
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Resim Seç", "", "Resimler (*.png *.jpg *.jpeg *.gif *.bmp)")
        if file_path:
            self.send_community_image_signal.emit(comm_id, file_path)

    def add_message_to_ui(self, comm_id, sender, content, timestamp=None):
        for i in range(self.communities_screens_stack.count()):
            widget = self.communities_screens_stack.widget(i)
            if hasattr(widget, 'comm_id') and widget.comm_id == comm_id:
                self.add_message_bubble(widget.msg_layout, sender, content, timestamp)
                break

    def add_message_bubble(self, layout, sender, content, timestamp):
        bubble_frame = QFrame()
        bubble_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e9ecef;
                margin-bottom: 8px;
            }
        """)
        
        bubble_layout = QVBoxLayout(bubble_frame)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(4)

        header_layout = QHBoxLayout()
        sender_lbl = QLabel(sender)
        sender_lbl.setStyleSheet("font-weight: bold; color: #3b82f6; font-size: 13px;")
        
        time_str = time.strftime("%H:%M", time.localtime(timestamp)) if timestamp else ""
        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet("font-size: 11px; color: #8696a0;")
        time_lbl.setAlignment(Qt.AlignRight)
        
        header_layout.addWidget(sender_lbl)
        header_layout.addStretch()
        header_layout.addWidget(time_lbl)
        bubble_layout.addLayout(header_layout)

        # Görsel mi kontrol et
        if content.startswith("[IMAGE]"):
            try:
                img_data_b64 = content.replace("[IMAGE]", "")
                from PyQt5.QtCore import QByteArray
                from PyQt5.QtGui import QImage, QPixmap
                img_data = QByteArray.fromBase64(img_data_b64.encode())
                image = QImage.fromData(img_data)
                
                img_lbl = QLabel()
                pixmap = QPixmap.fromImage(image)
                # Maksimum genişlik sınırlaması
                scaled_pixmap = pixmap.scaledToWidth(300, Qt.SmoothTransformation)
                img_lbl.setPixmap(scaled_pixmap)
                bubble_layout.addWidget(img_lbl)
            except Exception as e:
                print(f"Görsel yükleme hatası: {e}")
                bubble_layout.addWidget(QLabel("[Görsel yüklenemedi]"))
        else:
            content_lbl = QLabel(content)
            content_lbl.setWordWrap(True)
            content_lbl.setStyleSheet("font-size: 14px; color: #111b21; line-height: 1.4;")
            bubble_layout.addWidget(content_lbl)

        # Baloncuk genişliğini sınırla
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(15, 0, 100, 0) # Sağa doğru boşluk bırak (kanal görünümü)
        container_layout.addWidget(bubble_frame)
        
        layout.addWidget(container)
        
        # Otomatik scroll için timer (UI işlendikten sonra)
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(50, lambda: self.scroll_to_bottom(layout))

    def scroll_to_bottom(self, layout):
        # Scroll area'yı en alta kaydır
        parent_scroll = layout.parent().parent()
        if isinstance(parent_scroll, QScrollArea):
            parent_scroll.verticalScrollBar().setValue(
                parent_scroll.verticalScrollBar().maximum()
            )
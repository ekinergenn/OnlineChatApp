from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QScrollArea, QWidget, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor

class CommunityDialog(QDialog):
    create_signal = pyqtSignal(str)
    join_signal = pyqtSignal(int)
    search_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Topluluk Bul veya Oluştur")
        self.setFixedSize(450, 600)
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; border-radius: 12px; }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # --- Başlık ---
        title = QLabel("🌐  Topluluklar")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #111b21;")
        layout.addWidget(title)

        # --- Topluluk Oluştur Bölümü ---
        create_container = QFrame()
        create_container.setStyleSheet("background-color: #f8f9fa; border-radius: 10px; padding: 10px;")
        create_vbox = QVBoxLayout(create_container)
        
        create_label = QLabel("Yeni Topluluk Oluştur")
        create_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #111b21;")
        create_vbox.addWidget(create_label)

        create_row = QHBoxLayout()
        self.create_input = QLineEdit()
        self.create_input.setPlaceholderText("Topluluk adı...")
        self.create_input.setFixedHeight(40)
        self.create_input.setStyleSheet("""
            QLineEdit { border: 1px solid #d1d7db; border-radius: 8px; padding-left: 12px; background: white; }
            QLineEdit:focus { border: 2px solid #3b82f6; }
        """)
        
        create_btn = QPushButton("Oluştur")
        create_btn.setFixedHeight(40)
        create_btn.setCursor(QCursor(Qt.PointingHandCursor))
        create_btn.setStyleSheet("""
            QPushButton { background-color: #3b82f6; color: white; border-radius: 8px; padding: 0 20px; font-weight: bold; }
            QPushButton:hover { background-color: #2563eb; }
        """)
        create_btn.clicked.connect(self.on_create_clicked)
        
        create_row.addWidget(self.create_input)
        create_row.addWidget(create_btn)
        create_vbox.addLayout(create_row)
        layout.addWidget(create_container)

        # --- Arama Bölümü ---
        search_label = QLabel("Topluluk Ara")
        search_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #111b21;")
        layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  İsim ile topluluk ara...")
        self.search_input.setFixedHeight(40)
        self.search_input.setStyleSheet("""
            QLineEdit { background-color: #f0f2f5; border: none; border-radius: 8px; padding-left: 15px; font-size: 14px; }
            QLineEdit:focus { background-color: #ffffff; border: 1px solid #3b82f6; }
        """)
        self.search_input.textChanged.connect(self.search_signal.emit)
        layout.addWidget(self.search_input)

        # --- Sonuç Listesi (Scroll Area) ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #f0f2f5; border-radius: 10px; background: white; }")
        
        self.results_widget = QWidget()
        self.results_widget.setStyleSheet("background-color: #ffffff;")
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(0)
        self.results_layout.setAlignment(Qt.AlignTop)
        
        scroll.setWidget(self.results_widget)
        layout.addWidget(scroll)

    def on_create_clicked(self):
        name = self.create_input.text().strip()
        if name:
            self.create_signal.emit(name)
            self.accept()

    def show_results(self, results):
        # Önceki sonuçları temizle
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not results:
            empty = QLabel("Topluluk bulunamadı.")
            empty.setStyleSheet("color: #667781; padding: 20px;")
            empty.setAlignment(Qt.AlignCenter)
            self.results_layout.addWidget(empty)
            return

        for res in results:
            item_frame = QFrame()
            item_frame.setFixedHeight(70)
            item_frame.setStyleSheet("""
                QFrame { border-bottom: 1px solid #f0f2f5; background-color: white; }
                QFrame:hover { background-color: #f8f9fa; }
            """)
            
            row_layout = QHBoxLayout(item_frame)
            row_layout.setContentsMargins(15, 0, 15, 0)
            row_layout.setSpacing(15)

            # Avatar
            av = QLabel("📣")
            av.setFixedSize(40, 40)
            av.setAlignment(Qt.AlignCenter)
            av.setStyleSheet("background-color: #dfe5e7; border-radius: 20px; font-size: 20px;")

            # Bilgiler
            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)
            info_layout.setAlignment(Qt.AlignVCenter)
            
            name_lbl = QLabel(res['name'])
            name_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #111b21;")
            
            creator_lbl = QLabel(f"Kurucu: {res['creator']}")
            creator_lbl.setStyleSheet("font-size: 12px; color: #667781;")
            
            info_layout.addWidget(name_lbl)
            info_layout.addWidget(creator_lbl)

            # Katıl Butonu
            join_btn = QPushButton("Katıl")
            join_btn.setFixedSize(70, 32)
            join_btn.setCursor(QCursor(Qt.PointingHandCursor))
            join_btn.setStyleSheet("""
                QPushButton { background-color: #3b82f6; color: white; border-radius: 6px; font-size: 12px; font-weight: bold; }
                QPushButton:hover { background-color: #2563eb; }
            """)
            join_btn.clicked.connect(lambda checked, cid=res['community_id']: self.on_item_join_clicked(cid))

            row_layout.addWidget(av)
            row_layout.addLayout(info_layout)
            row_layout.addStretch()
            row_layout.addWidget(join_btn)

            self.results_layout.addWidget(item_frame)

    def on_item_join_clicked(self, community_id):
        self.join_signal.emit(community_id)
        self.accept()

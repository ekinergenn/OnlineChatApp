"""
ui/groupMembersDialog.py
Grup üyelerini gösteren dialog penceresi
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QWidget, QFrame, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor


class GroupMembersDialog(QDialog):
    """
    Gruptaki kişileri listeleyen dialog penceresi.
    """
    def __init__(self, group_name: str, members: list, parent=None):
        """
        group_name: Grubun adı
        members: ["username1", "username2", ...]
        """
        super().__init__(parent)
        self.group_name = group_name
        self.members = members

        self.setWindowTitle(f"{group_name} Üyeleri")
        self.setFixedSize(380, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 12px;
            }
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── Başlık ──────────────────────────────────────
        header_layout = QHBoxLayout()
        title = QLabel(f"👥  {self.group_name}")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #111b21;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        count_label = QLabel(f"{len(self.members)} Üye")
        count_label.setStyleSheet("font-size: 13px; color: #667781; font-weight: 500;")
        layout.addWidget(count_label)

        # ── Üye Listesi ────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #e9ecef; border-radius: 8px; }")
        
        self.list_widget = QWidget()
        self.list_widget.setStyleSheet("background-color: #ffffff;")
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 4, 0, 4)
        self.list_layout.setSpacing(0)
        self.list_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.list_widget)
        layout.addWidget(scroll)

        self._populate_members()

        # ── Kapat Butonu ─────────────────────────────────
        close_btn = QPushButton("Kapat")
        close_btn.setFixedHeight(40)
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f2f5;
                color: #111b21;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #e4e6eb; }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _populate_members(self):
        for username in self.members:
            row = QFrame()
            row.setFixedHeight(56)
            row.setStyleSheet("""
                QFrame { background-color: #ffffff; border-bottom: 1px solid #f0f2f5; }
                QFrame:hover { background-color: #f8f9fa; }
            """)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 0, 12, 0)
            row_layout.setSpacing(12)

            # Avatar
            av = QLabel("👤")
            av.setFixedSize(36, 36)
            av.setAlignment(Qt.AlignCenter)
            av.setStyleSheet("background-color: #dfe5e7; border-radius: 18px; font-size: 18px;")

            # İsim (Şu an sadece username elimizde olduğu için onu gösteriyoruz)
            name_lbl = QLabel(f"{username}")
            name_lbl.setStyleSheet("font-size: 14px; color: #111b21; font-weight: 500;")
            
            row_layout.addWidget(av)
            row_layout.addWidget(name_lbl)
            row_layout.addStretch()

            self.list_layout.addWidget(row)

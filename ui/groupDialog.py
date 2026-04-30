"""
ui/groupDialog.py
Grup oluşturma dialog penceresi
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QWidget, QCheckBox, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor


class GroupCreationDialog(QDialog):
    """
    Kullanıcı listesinden kişi seçip grup oluşturmak için dialog.
    Kabul edilince create_group_signal(group_name, [username1, username2, ...]) sinyali yayar.
    """
    create_group_signal = pyqtSignal(str, list)  # (group_name, members_list)

    def __init__(self, users: list, current_username: str, parent=None):
        """
        users: [{"username": "...", "fullname": "...", "user_id": ...}, ...]
        current_username: giriş yapan kullanıcının adı (listeye eklenmeyecek)
        """
        super().__init__(parent)
        self.users = [u for u in users if u.get("username") != current_username]
        self.current_username = current_username
        self.checked_users = {}  # {username: QCheckBox}

        self.setWindowTitle("Yeni Grup Oluştur")
        self.setFixedSize(420, 560)
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
        title = QLabel("👥  Yeni Grup")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #111b21;")
        layout.addWidget(title)

        # ── Grup Adı ────────────────────────────────────
        name_label = QLabel("Grup Adı")
        name_label.setStyleSheet("font-size: 13px; color: #667781; font-weight: 500;")
        layout.addWidget(name_label)

        self.group_name_input = QLineEdit()
        self.group_name_input.setPlaceholderText("Gruba bir isim verin...")
        self.group_name_input.setFixedHeight(42)
        self.group_name_input.setStyleSheet("""
            QLineEdit {
                background-color: #f0f2f5;
                border: 1px solid #d1d7db;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 14px;
                color: #111b21;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
                background-color: #ffffff;
            }
        """)
        layout.addWidget(self.group_name_input)

        # ── Kişi Seç Başlığı ────────────────────────────
        members_label = QLabel("Katılımcılar")
        members_label.setStyleSheet("font-size: 13px; color: #667781; font-weight: 500;")
        layout.addWidget(members_label)

        # ── Arama ───────────────────────────────────────
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Kullanıcı ara...")
        self.search_input.setFixedHeight(38)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #f0f2f5;
                border: none;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 13px;
                color: #111b21;
            }
            QLineEdit:focus { background-color: #e8eaed; }
        """)
        self.search_input.textChanged.connect(self._filter_users)
        layout.addWidget(self.search_input)

        # ── Kullanıcı Listesi ────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #e9ecef; border-radius: 8px; }")
        scroll.setFixedHeight(220)

        self.list_widget = QWidget()
        self.list_widget.setStyleSheet("background-color: #ffffff;")
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 4, 0, 4)
        self.list_layout.setSpacing(0)
        self.list_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.list_widget)
        layout.addWidget(scroll)

        self._populate_users(self.users)

        # ── Seçilen Sayısı ───────────────────────────────
        self.selected_label = QLabel("0 kişi seçildi")
        self.selected_label.setStyleSheet("font-size: 12px; color: #667781;")
        layout.addWidget(self.selected_label)

        # ── Butonlar ─────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel_btn = QPushButton("İptal")
        cancel_btn.setFixedHeight(42)
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.setStyleSheet("""
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
        cancel_btn.clicked.connect(self.reject)

        self.create_btn = QPushButton("Grup Oluştur")
        self.create_btn.setFixedHeight(42)
        self.create_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2563eb; }
            QPushButton:disabled { background-color: #b1c9f3; }
        """)
        self.create_btn.clicked.connect(self._on_create)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.create_btn)
        layout.addLayout(btn_row)

    # ── Yardımcı Metodlar ────────────────────────────────────

    def _populate_users(self, users: list):
        """Listedeki widget'ları temizle ve yeniden doldur."""
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not users:
            empty = QLabel("  Kullanıcı bulunamadı")
            empty.setStyleSheet("color: #667781; font-size: 13px; padding: 12px;")
            self.list_layout.addWidget(empty)
            return

        for user in users:
            username = user.get("username", "")
            fullname = user.get("fullname", username)

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

            # İsim
            name_lbl = QLabel(f"{fullname}")
            name_lbl.setStyleSheet("font-size: 14px; color: #111b21; font-weight: 500;")
            uname_lbl = QLabel(f"@{username}")
            uname_lbl.setStyleSheet("font-size: 12px; color: #667781;")

            text_v = QVBoxLayout()
            text_v.setSpacing(0)
            text_v.addWidget(name_lbl)
            text_v.addWidget(uname_lbl)

            # Checkbox
            cb = QCheckBox()
            cb.setStyleSheet("""
                QCheckBox::indicator { width: 20px; height: 20px; border-radius: 10px; border: 2px solid #d1d7db; }
                QCheckBox::indicator:checked { background-color: #3b82f6; border: 2px solid #3b82f6; }
            """)
            cb.stateChanged.connect(lambda state, u=username: self._on_check_changed(u, state))
            self.checked_users[username] = cb

            row_layout.addWidget(av)
            row_layout.addLayout(text_v)
            row_layout.addStretch()
            row_layout.addWidget(cb)

            # Satıra tıklayınca checkbox toggle
            row.mousePressEvent = lambda e, c=cb: c.setChecked(not c.isChecked())

            self.list_layout.addWidget(row)

    def _filter_users(self, text: str):
        query = text.strip().lower()
        filtered = [
            u for u in self.users
            if query in u.get("username", "").lower()
            or query in u.get("fullname", "").lower()
        ] if query else self.users

        # Mevcut checkbox durumlarını koru
        old_states = {u: cb.isChecked() for u, cb in self.checked_users.items()}
        self.checked_users.clear()
        self._populate_users(filtered)

        # Durumları geri yükle
        for u, cb in self.checked_users.items():
            if old_states.get(u, False):
                cb.blockSignals(True)
                cb.setChecked(True)
                cb.blockSignals(False)

        self._update_selected_label()

    def _on_check_changed(self, username: str, state: int):
        self._update_selected_label()

    def _update_selected_label(self):
        count = sum(1 for cb in self.checked_users.values() if cb.isChecked())
        self.selected_label.setText(f"{count} kişi seçildi")

    def _on_create(self):
        group_name = self.group_name_input.text().strip()
        selected = [u for u, cb in self.checked_users.items() if cb.isChecked()]

        if not group_name:
            QMessageBox.warning(self, "Hata", "Lütfen bir grup adı girin.")
            return
        if len(selected) < 2:
            QMessageBox.warning(self, "Hata", "Grup için en az 2 kişi seçin.")
            return

        self.create_group_signal.emit(group_name, selected)
        self.accept()
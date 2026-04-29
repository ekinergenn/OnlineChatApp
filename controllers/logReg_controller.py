from PyQt5.QtWidgets import QMessageBox

class LogRegController:
    def __init__(self, stacked_widget, login_page, register_page, logreg_service, on_login_success=None):
        self.stacked_widget = stacked_widget
        self.login_page = login_page
        self.register_page = register_page
        self.logreg_service = logreg_service

        self.on_login_success = on_login_success

        # Sinyal bağlantıları
        self.logreg_service.login_response_signal.connect(self.on_login_response_received)
        self.logreg_service.register_response_signal.connect(self.on_register_response_received)

        # Sayfa geçişleri
        self.login_page.register_label_link.mousePressEvent = self.go_to_register
        self.register_page.login_label_link.mousePressEvent = self.go_to_login

        # Buton bağlantıları
        self.login_page.login_button.clicked.connect(self.handle_login)
        self.register_page.register_button.clicked.connect(self.handle_register)

    def go_to_register(self, event):
        self.stacked_widget.setCurrentIndex(1)

    def go_to_login(self, event):
        self.stacked_widget.setCurrentIndex(0)

    def handle_login(self):
        username = self.login_page.username_input.text()
        password = self.login_page.password_input.text()
        if not username or not password:
            QMessageBox.warning(self.login_page, "Hata", "Alanlar boş bırakılamaz!")
            return
        self.logreg_service.send_login_request(username, password)

    def handle_register(self):
        fullname = self.register_page.fullname_input.text()
        email = self.register_page.email_input.text()
        username = self.register_page.username_input.text()  # bunu ekleyeceğiz
        password = self.register_page.password_input.text()
        confirm = self.register_page.password_confirm_input.text()
        tel = self.register_page.phone_input.text()

        print(
            f"[DEBUG] fullname={fullname}, email={email}, username={username}, password={password}, confirm={confirm}")

        if not fullname or not email or not username or not password:
            QMessageBox.warning(self.register_page, "Hata", "Tüm alanları doldurun!")
            return

        if password != confirm:
            QMessageBox.warning(self.register_page, "Hata", "Şifreler uyuşmuyor!")
            return

        print("[DEBUG] send_register_request çağrılıyor...")


        self.logreg_service.send_register_request(username, password, fullname, email, tel)

    def on_login_response_received(self, server_payload):
        status = server_payload.get("status")
        if status == "success":
            QMessageBox.information(self.login_page, "Başarılı", "Sohbet ekranına yönlendiriliyorsunuz...")
            self.stacked_widget.setCurrentIndex(2)
            # ← ekle
            if self.on_login_success:
                self.on_login_success(server_payload.get("profile"))
        else:
            hata_mesaji = server_payload.get("message", "Bilinmeyen bir hata oluştu.")
            QMessageBox.warning(self.login_page, "Giriş Başarısız", hata_mesaji)

    def on_register_response_received(self, server_payload):
        status = server_payload.get("status")
        if status == "success":
            QMessageBox.information(self.register_page, "Başarılı", "Kayıt olundu! Giriş yapabilirsiniz.")
            self.stacked_widget.setCurrentIndex(0)  # login sayfasına dön
        else:
            hata_mesaji = server_payload.get("message", "Kayıt sırasında hata oluştu.")
            QMessageBox.warning(self.register_page, "Kayıt Başarısız", hata_mesaji)
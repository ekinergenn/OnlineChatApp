from PyQt5.QtWidgets import QMessageBox
class LogRegController:
    def __init__(self, stacked_widget, login_page, register_page,logreg_service):
        self.stacked_widget = stacked_widget
        self.login_page = login_page
        self.register_page = register_page
        self.logreg_service = logreg_service

        
        self.logreg_service.login_response_signal.connect(self.on_login_response_received)
        # --- YÖNLENDİRME OLAYLARINI BAĞLAMA ---
        # Login sayfasındaki "Kayıt Ol" yazısına tıklanınca
        self.login_page.register_label_link.mousePressEvent = self.go_to_register

        # Register sayfasındaki "Giriş Yap" yazısına tıklanınca
        self.register_page.login_label_link.mousePressEvent = self.go_to_login

        # --- BUTON OLAYLARINI BAĞLAMA ---
        self.login_page.login_button.clicked.connect(self.handle_login)
        self.register_page.register_button.clicked.connect(self.handle_register)

    def go_to_register(self, event):
        self.stacked_widget.setCurrentIndex(1)

    def go_to_login(self, event):
        self.stacked_widget.setCurrentIndex(0)

    # --- İŞ MANTIĞI FONKSİYONLARI ---
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
        password = self.register_page.password_input.text()
        confirm = self.register_page.password_confirm_input.text()

        if password != confirm:
            QMessageBox.warning(self.register_page, "Hata", "Şifreler uyuşmuyor!")
        else:
            QMessageBox.information(self.register_page, "Başarılı", f"Kayıt oldunuz: {fullname}")


    def on_login_response_received(self, server_payload):
            """Sunucudan yanıt geldiğinde (Servis sinyal fırlattığında) otomatik çalışır."""
            status = server_payload.get("status")
            
            if status == "success":
                QMessageBox.information(self.login_page, "Başarılı", "Sohbet ekranına yönlendiriliyorsunuz...")
                self.stacked_widget.setCurrentIndex(2) # MainPage'e geç
            else:
                hata_mesaji = server_payload.get("message", "Bilinmeyen bir hata oluştu.")
                QMessageBox.warning(self.login_page, "Giriş Başarısız", hata_mesaji)
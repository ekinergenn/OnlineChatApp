import os
import base64
import warnings
from cryptography.utils import CryptographyDeprecationWarning
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from PyQt5.QtCore import QObject, pyqtSignal


class EncryptionService(QObject):
    """
    Uçtan Uca Şifreleme (E2EE) servisi.
    RSA-2048 + AES-256-CFB hibrit şifreleme kullanır.
    Özel anahtarlar yalnızca istemci cihazında saklanır; sunucu içeriği okuyamaz.
    """
    public_key_fetched_signal = pyqtSignal(dict)  # {"username": "...", "public_key": "..."}

    def __init__(self, client, keys_dir="keys"):
        super().__init__()
        self.client = client
        self.keys_dir = keys_dir
        if not os.path.exists(self.keys_dir):
            os.makedirs(self.keys_dir)
        self.private_key = None
        self.public_key = None
        self.public_keys = {}  # Önbellek: {username: public_key_pem_str}

    # ─────────────────────────── ANAHTAR YÖNETİMİ ────────────────────────────

    def generate_key_pair(self, username: str) -> str | None:
        """RSA anahtar çifti oluşturur veya varsa diskten yükler. Genel anahtarı PEM olarak döndürür."""
        priv_path = os.path.join(self.keys_dir, f"private_{username}.pem")

        if os.path.exists(priv_path):
            # Zaten oluşturulmuş, yükle
            return self.load_private_key(username)

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.private_key = private_key
        self.public_key = private_key.public_key()

        # Özel anahtarı diske kaydet
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        with open(priv_path, "wb") as f:
            f.write(pem)

        print(f"[ŞİFRELEME] {username} için yeni RSA anahtar çifti oluşturuldu.")
        return self.get_public_key_pem()

    def load_private_key(self, username: str) -> str | None:
        """Diskten özel anahtarı yükler ve bellekte tutar."""
        priv_path = os.path.join(self.keys_dir, f"private_{username}.pem")
        if not os.path.exists(priv_path):
            print(f"[ŞİFRELEME] {username} için disk üzerinde özel anahtar bulunamadı.")
            return None

        with open(priv_path, "rb") as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )
        self.public_key = self.private_key.public_key()
        print(f"[ŞİFRELEME] {username} için özel anahtar diskten yüklendi.")
        return self.get_public_key_pem()

    def get_public_key_pem(self) -> str | None:
        """Genel anahtarı PEM string olarak döndürür."""
        if not self.public_key:
            return None
        pem_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem_bytes.decode("utf-8")

    def reset(self):
        """Oturum kapatıldığında tüm anahtar state'ini temizler."""
        self.private_key = None
        self.public_key = None
        self.public_keys = {}
        print("[ŞİFRELEME] Servis sıfırlandı.")

    # ─────────────────────────── ŞİFRELEME / ÇÖZME ───────────────────────────

    def encrypt_message(self, plaintext: str, recipient_keys: dict) -> dict | None:
        """
        Mesajı şifreler.
        recipient_keys: {username: public_key_pem_str}
        Returns: {ciphertext, iv, keys: {username: encrypted_aes_key}} veya None
        """
        if not recipient_keys:
            print("[ŞİFRELEME] Alıcı anahtarları boş, şifreleme yapılamadı.")
            return None

        # 1. Rastgele AES anahtarı ve IV oluştur
        aes_key = os.urandom(32)  # 256-bit
        iv = os.urandom(16)

        # 2. Mesajı AES-256-CFB ile şifrele
        cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext.encode("utf-8")) + encryptor.finalize()

        # 3. AES anahtarını her alıcının RSA genel anahtarıyla ayrı ayrı şifrele
        encrypted_keys = {}
        for username, pem_str in recipient_keys.items():
            if not pem_str:
                print(f"[ŞİFRELEME] {username} için PEM anahtarı yok, atlanıyor.")
                continue
            try:
                pub_key = serialization.load_pem_public_key(
                    pem_str.encode("utf-8"), backend=default_backend()
                )
                enc_key = pub_key.encrypt(
                    aes_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                encrypted_keys[username] = base64.b64encode(enc_key).decode("utf-8")
            except Exception as e:
                print(f"[ŞİFRELEME HATASI] {username} anahtarı işlenemedi: {e}")

        if not encrypted_keys:
            print("[ŞİFRELEME] Hiçbir alıcı için anahtar şifrelenemedi, mesaj gönderilmiyor.")
            return None

        return {
            "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
            "iv": base64.b64encode(iv).decode("utf-8"),
            "keys": encrypted_keys  # {username: base64_encrypted_aes_key}
        }

    def decrypt_message(self, encrypted_data: dict, my_username: str) -> str | None:
        """Şifrelenmiş mesajı kendi özel anahtarıyla çözer."""
        if not self.private_key:
            print("[ŞİFRE ÇÖZME] Özel anahtar yüklü değil!")
            return None
        if not encrypted_data:
            return None

        try:
            encrypted_keys = encrypted_data.get("keys", {})
            enc_aes_key_b64 = encrypted_keys.get(my_username)

            if not enc_aes_key_b64:
                print(
                    f"[ŞİFRE ÇÖZME] '{my_username}' için anahtar pakette yok. "
                    f"Paketteki kullanıcılar: {list(encrypted_keys.keys())}"
                )
                return None

            # 1. AES anahtarını kendi RSA özel anahtarımızla çöz
            encrypted_aes_key = base64.b64decode(enc_aes_key_b64)
            aes_key = self.private_key.decrypt(
                encrypted_aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            # 2. Mesajı AES ile çöz
            ciphertext = base64.b64decode(encrypted_data["ciphertext"])
            iv = base64.b64decode(encrypted_data["iv"])
            cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            return plaintext.decode("utf-8")
        except Exception as e:
            print(f"[ŞİFRE ÇÖZME HATASI] {e}")
            return None

    # ────────────────────── GRUP ANAHTAR YÖNETİMİ ───────────────────────────

    def all_group_keys_ready(self, members: list) -> bool:
        """Verilen tüm üyelerin genel anahtarları önbellekte mi kontrol eder."""
        return all(m in self.public_keys for m in members)

    def fetch_missing_group_keys(self, members: list):
        """Önbellekte olmayan üyelerin genel anahtarlarını sunucudan ister."""
        for member in members:
            if member not in self.public_keys:
                print(f"[GRUP E2EE] {member} için anahtar eksik, isteniyor...")
                self.send_get_public_key_request(member)

    # ────────────────────────── AĞ İŞLEMLERİ ────────────────────────────────

    def send_update_public_key_request(self, username: str):
        """Kendi genel anahtarımızı sunucuya gönderir (kayıt için)."""
        pem = self.get_public_key_pem()
        if not pem:
            print("[ŞİFRELEME] Genel anahtar henüz hazır değil, gönderilemedi.")
            return
        self.client.send_data({
            "type": "update_public_key_request",
            "payload": {"username": username, "public_key": pem}
        })
        print(f"[ŞİFRELEME] {username} için genel anahtar sunucuya gönderildi.")

    def send_get_public_key_request(self, username: str):
        """Bir kullanıcının genel anahtarını sunucudan ister."""
        print(f"[ŞİFRELEME] {username} için genel anahtar isteniyor...")
        self.client.send_data({
            "type": "get_public_key_request",
            "payload": {"username": username}
        })

    def handle_get_public_key_response(self, payload: dict):
        """Sunucudan gelen genel anahtar yanıtını işler ve önbelleğe alır."""
        status = payload.get("status")
        username = payload.get("username")
        public_key = payload.get("public_key")

        if status == "success" and username and public_key:
            self.public_keys[username] = public_key
            print(f"[ŞİFRELEME] {username} için genel anahtar alındı ve önbelleğe eklendi.")
            self.public_key_fetched_signal.emit({"username": username, "public_key": public_key})
        else:
            print(f"[ŞİFRELEME UYARI] {username} için genel anahtar alınamadı: {payload.get('message')}")

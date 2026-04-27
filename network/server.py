import socket
import threading
import json
from database.user_repository import find_user, create_user
from database.message_repository import save_message, get_messages

from database.user_repository import find_user
from database.chat_repository import create_chat, get_user_chats
from database.user_repository import find_user, create_user, search_users
# server.py'ın EN ÜSTÜNE bu importları ekle (fonksiyon içinde değil!)
from database.message_repository import save_message, get_messages, delete_chat_messages
from database.chat_repository import create_chat, get_user_chats, delete_chat


class ChatServer:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"[SUNUCU] {self.host}:{self.port} üzerinde çalışıyor...")

        while True:
            client_sock, addr = self.server_socket.accept()
            print(f"[BAĞLANTI] {addr} bağlandı.")
            self.clients.append(client_sock)
            
            thread = threading.Thread(target=self.handle_client, args=(client_sock, addr))
            thread.start()

    def handle_client(self, conn, addr):
        while True:
            try:
                # 1. Ham veriyi al
                raw_data = conn.recv(4096)
                if not raw_data:
                    break

                # 2. Protokolüne uygun olarak veriyi parçala (<END> ayırıcısını kontrol et)
                decoded_data = raw_data.decode('utf-8')
                messages = decoded_data.split("<END>")

                for msg in messages:
                    if not msg: continue
                    
                    packet = json.loads(msg)
                    print(f"[GELEN PAKET] {addr}: {packet}")

                    # 3. Gelen paketi işle ve cevap hazırla
                    self.process_request(conn, packet)

            except Exception as e:
                print(f"[HATA] {addr} hatası: {e}")
                break

        print(f"[AYRILDI] {addr} bağlantısı kesildi.")
        self.clients.remove(conn)
        conn.close()

    def process_request(self, conn, packet):
        """İstemcinin gönderdiği 'type' değerine göre cevap üretir."""
        msg_type = packet.get("type")
        
        # Senin logReg_service içindeki paket yapına uygun kontrol
        if msg_type == "login_request":
            payload = packet.get("payload", {})
            username = payload.get("name")
            password = payload.get("password")

            user=find_user(username)
            if user and user["password"] == password:
                user_chats = get_user_chats(username)
                response = {
                    "type": "login_response",
                    "payload": {
                        "status": "success",
                        "message": f"Hoş geldin {user['fullname']}!",
                        "user_id": user["user_id"],
                        "username": username,
                        "chats": user_chats
                    }
                }
            else:
                response = {
                    "type": "login_response",
                    "payload": {
                        "status": "fail",
                        "message": "Kullanıcı adı veya şifre hatalı!"
                    }
                }
            self.send_packet(conn, response)

        elif msg_type == "register_request":
            payload = packet.get("payload", {})
            success = create_user(
                username=payload.get("username"),
                password=payload.get("password"),
                fullname=payload.get("fullname"),
                tel=payload.get("tel", ""),
                email=payload.get("email")
            )
            response = {
                "type": "register_response",
                "payload": {
                    "status": "success" if success else "fail",
                    "message": "Kayıt başarılı!" if success else "Bu kullanıcı adı zaten alınmış."
                }
            }
            self.send_packet(conn, response)

        elif msg_type == "chat_message":
            payload = packet.get("payload", {})
            saved = save_message(
                chat_name=payload.get("chat_name"),
                sender=payload.get("sender"),
                content=payload.get("content"),
                sender_id=payload.get("sender_id")
            )
            response = {
                "type": "chat_message",
                "payload": saved  # kaydedilen mesajı geri dön (message_id ve status ile)
            }
            self.send_packet(conn, response)

        elif msg_type == "create_group_request":
            payload = packet.get("payload", {})
            group_name = payload.get("group_name")
            members = payload.get("members", [])
            creator_id = payload.get("creator_id")

            # Terminalde görmek için ekrana yazdırıyoruz (İleride DB'ye eklenecek)
            print(f"[YENİ GRUP İSTEĞİ] Grup Adı: '{group_name}' | Seçilen Kişiler: {members}")
            create_chat(group_name, members, is_group=True)

            # Burada veritabanına kayıt işlemi yapılabilir
            response = {
                "type": "create_group_response",
                "payload": {
                    "status": "success",
                    "group_name": group_name
                }
            }
            self.send_packet(conn, response)

        elif msg_type == "delete_chat_request":
            payload = packet.get("payload", {})
            chat_name = payload.get("chat_name")
            print(f"[SİLME] '{chat_name}' siliniyor...")

            delete_chat_messages(chat_name)  # messages.json'dan sil
            delete_chat(chat_name)  # chats.json'dan sil

            print(f"[SİLME] '{chat_name}' silindi.")
            response = {
                "type": "delete_chat_response",
                "payload": {"status": "success", "chat_name": chat_name}
            }
            self.send_packet(conn, response)

        elif msg_type == "search_users_request":
            payload = packet.get("payload", {})
            query = payload.get("query", "")
            requester = payload.get("username", "")

            results = search_users(query, exclude_username=requester)

            response = {
                "type": "search_users_response",
                "payload": {
                    "status": "success",
                    "results": results
                }
            }
            self.send_packet(conn, response)

        elif msg_type == "create_chat_request":
            payload = packet.get("payload", {})
            chat_name = payload.get("chat_name")
            members = payload.get("members", [])
            is_group = payload.get("is_group", False)

            try:
                create_chat(chat_name, members, is_group=is_group)
                print(f"[SOHBET] '{chat_name}' oluşturuldu, üyeler: {members}")
                response = {
                    "type": "create_chat_response",
                    "payload": {"status": "success", "chat_name": chat_name}
                }
            except Exception as e:
                print(f"[SOHBET HATA] {e}")
                response = {
                    "type": "create_chat_response",
                    "payload": {"status": "fail", "chat_name": chat_name}
                }
            self.send_packet(conn, response)

    def send_packet(self, conn, packet_dict):
        """Senin Protocol.py yapına uygun şekilde gönderim yapar."""
        json_data = json.dumps(packet_dict) + "<END>"
        conn.sendall(json_data.encode('utf-8'))


if __name__ == "__main__":
    server = ChatServer()
    server.start()
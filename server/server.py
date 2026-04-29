import socket
import threading
import json
from database.user_repository import find_user, create_user
from database.message_repository import save_message, get_messages

from database.user_repository import *
from database.chat_repository import *
from database.user_repository import find_user, create_user
# server.py'ın EN ÜSTÜNE bu importları ekle (fonksiyon içinde değil!)
from database.message_repository import save_message, get_messages
from database.chat_repository import create_chat, get_user_chats, delete_chat


class ChatServer:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []
        self.online_users = {}

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
                self.online_users[user["username"]] = conn
                print(self.online_users)
                response = {
                    "type": "login_response",
                    "payload": {
                        "status": "success",
                        "profile":{
                        "username":user["username"],
                        "fullname": user["fullname"],
                        "email": user["email"],
                        "tel": user["tel"],
                        "user_id": user["user_id"]
                        }
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
            chat_id = payload.get("chat_id")
            sender = payload.get("sender")
            
            all_chats = get_all_chats()
            active_chat = get_chat_(all_chats, chat_id)
            
            # SECURITY CHECK
            if active_chat and (sender in active_chat["members"]):
                saved_message = save_message(payload)
                
                # Forward to online members
                for member in active_chat["members"]:
                    if member in self.online_users:
                        member_socket = self.online_users[member]
                        response_packet = {
                            "type": "chat_message",
                            "payload": saved_message
                        }
                        self.send_packet(member_socket, response_packet)

        elif msg_type == "get_user_chats_request":
            payload = packet.get("payload", {})
            username = payload.get("username")

            user_chats = get_user_chats(username)
            packet_data = []
            
            for chat_id in user_chats:
                chat_messages = get_messages(chat_id)
                packet_data.append({
                    "chat_id": chat_id,
                    "messages": chat_messages
                })

            response = {
                "type": "get_user_chats_response",
                "payload": {
                    "status": "success",
                    "chats": packet_data
                }
            }
            self.send_packet(conn, response)

        elif msg_type == "create_chat_request":
            payload = packet.get("payload", {})
            members = payload.get("members", [])
            
            import time
            new_chat_id = f"chat_{int(time.time())}"

            try:
                # 1. Sohbet listesine (chats.json) ekle[cite: 6]
                create_chat(new_chat_id, members, is_group=False)
                
                # 2. KRİTİK ADIM: Mesaj dosyasını (messages/chat_id.json) o an oluştur
                # Boş bir liste yazarak dosyanın varlığını garantiliyoruz
                from database.db import write_json
                write_json(f"messages/{new_chat_id}.json", [])
                
                # 3. Yanıtı gönder
                response = {
                    "type": "create_chat_response",
                    "payload": {
                        "status": "success",
                        "chat_id": new_chat_id,
                        "target_username": members[1] if len(members) > 1 else ""
                    }
                }
                self.send_packet(conn, response)
            except Exception as e:
                print(f"[HATA] Sohbet dosyası oluşturulamadı: {e}")

        elif msg_type == "delete_chat_request":
            payload = packet.get("payload", {})
            chat_id = payload.get("chat_id")
            print(f"[SİLME] '{chat_id}' siliniyor...")

            # delete_chat_messages(chat_id)  # messages.json'dan sil
            delete_chat(chat_id)  # chats.json'dan sil

            print(f"[SİLME] '{chat_id}' silindi.")
            response = {
                "type": "delete_chat_response",
                "payload": {"status": "success", "chat_id": chat_id}
            }
            self.send_packet(conn, response)

        elif msg_type == "search_users_request":
            payload = packet.get("payload", {})
            query = payload.get("query", "")
            requester = payload.get("username", "")

            results = search_users(query, exclude_username=requester)
            # burası hatalı aranan bir kullanıcın tüm bilegilerini client e gönderiyoruz
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
            members = payload.get("members", []) # [gönderen, alıcı]
            
            # 1. Benzersiz bir Chat ID üret (Örn: chat_17123456)
            import time
            new_chat_id = f"chat_{int(time.time())}"

            try:
                # 2. Veritabanına (chats.json) kaydet[cite: 6]
                # is_group=False çünkü bu bir birebir sohbet
                create_chat(new_chat_id, members, is_group=False)
                
                # 3. İsteği gönderen kişiye yanıt dön
                response = {
                    "type": "create_chat_response",
                    "payload": {
                        "status": "success",
                        "chat_id": new_chat_id,
                        "target_username": members[1] # Kiminle sohbet açıldıysa o
                    }
                }
                self.send_packet(conn, response)
                print(f"[SOHBET] '{new_chat_id}' oluşturuldu, üyeler: {members}")
            except Exception as e:
                print(f"[SOHBET HATA] {e}")

    def send_packet(self, conn, packet_dict):
        """Senin Protocol.py yapına uygun şekilde gönderim yapar."""
        json_data = json.dumps(packet_dict) + "<END>"
        conn.sendall(json_data.encode('utf-8'))
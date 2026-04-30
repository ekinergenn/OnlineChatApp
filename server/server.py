import socket
import threading
import json
import time
import os
from database.user_repository import find_user, create_user, search_users
from database.message_repository import save_message, get_messages, mark_messages_as_read
from database.chat_repository import create_chat, get_all_chats, get_chat_, get_user_chats, delete_chat
from database import block_repository


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
        buffer = ""
        while True:
            try:
                # 1. Ham veriyi al
                raw_data = conn.recv(4096)
                if not raw_data:
                    break

                # 2. Protokolüne uygun olarak veriyi tamponda biriktir ve parçala
                buffer += raw_data.decode('utf-8')
                
                while "<END>" in buffer:
                    msg, buffer = buffer.split("<END>", 1)
                    if not msg: continue
                    
                    try:
                        packet = json.loads(msg)
                        print(f"[GELEN PAKET] {addr}: {packet}")
                        # 3. Gelen paketi işle ve cevap hazırla
                        self.process_request(conn, packet)
                    except json.JSONDecodeError as e:
                        print(f"[HATA] {addr} için JSON çözümleme hatası: {e} - Mesaj: {msg}")

            except Exception as e:
                print(f"[HATA] {addr} bağlantı hatası: {e}")
                break

        print(f"[AYRILDI] {addr} bağlantısı kesildi.")
        
        # Online kullanıcılardan temizle
        user_to_remove = None
        for username, socket in self.online_users.items():
            if socket == conn:
                user_to_remove = username
                break
        if user_to_remove:
            del self.online_users[user_to_remove]
            print(f"[SİSTEM] {user_to_remove} online listesinden çıkarıldı.")

        if conn in self.clients:
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
            sender_name = payload.get("sender")
            
            all_chats = get_all_chats()
            active_chat = get_chat_(all_chats, chat_id)
            
            # SECURITY CHECK
            if active_chat and (sender_name in active_chat["members"]):
                # BLOCK CHECK
                # Find receiver(s)
                receivers = [m for m in active_chat["members"] if m != sender_name]
                sender_user = find_user(sender_name)
                
                can_send = True
                if sender_user:
                    sender_id = sender_user.get("user_id")
                    for r_name in receivers:
                        receiver_user = find_user(r_name)
                        if receiver_user:
                            receiver_id = receiver_user.get("user_id")
                            status = block_repository.check_block_status(sender_id, receiver_id)
                            if status != "none":
                                can_send = False
                                break
                
                if not can_send:
                    response = {
                        "type": "error",
                        "payload": {"message": "Bu kullanıcıya mesaj gönderemezsiniz (Engelleme mevcut)."}
                    }
                    self.send_packet(conn, response)
                    return

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

        elif msg_type == "mark_messages_read":
            payload = packet.get("payload", {})
            chat_id = payload.get("chat_id")
            message_ids = payload.get("message_ids", [])
            username = payload.get("username")

            if chat_id and message_ids and username:
                mark_messages_as_read(chat_id, message_ids, username)
                
                # İsteğe bağlı olarak diğer üyelere ilet (Okundu bilgisinin canlı güncellenmesi için)
                all_chats = get_all_chats()
                active_chat = get_chat_(all_chats, chat_id)
                if active_chat:
                    for member in active_chat["members"]:
                        if member != username and member in self.online_users:
                            member_socket = self.online_users[member]
                            response_packet = {
                                "type": "messages_read_receipt",
                                "payload": {
                                    "chat_id": chat_id,
                                    "message_ids": message_ids,
                                    "read_by": username
                                }
                            }
                            self.send_packet(member_socket, response_packet)

        elif msg_type == "get_user_chats_request":
            payload = packet.get("payload", {})
            username = payload.get("username")

            user_chats = get_user_chats(username)
            all_chats = get_all_chats()
            packet_data = []
            
            for chat_id in user_chats:
                chat_messages = get_messages(chat_id)
                chat_obj = get_chat_(all_chats, chat_id)
                display_name = chat_id
                
                if chat_obj:
                    if chat_obj.get("chat_name"):
                        display_name = chat_obj.get("chat_name")
                other_user_id = None
                if chat_obj and len(chat_obj.get("members", [])) == 2:
                    other_members = [m for m in chat_obj.get("members", []) if m != username]
                    if other_members:
                        display_name = other_members[0]
                        ou = find_user(display_name)
                        if ou:
                            other_user_id = ou.get("user_id")

                sender_user = find_user(username)
                block_status = "none"
                if sender_user and chat_obj and len(chat_obj.get("members", [])) == 2:
                    other_member_name = [m for m in chat_obj.get("members", []) if m != username][0]
                    other_user = find_user(other_member_name)
                    if other_user:
                        block_status = block_repository.check_block_status(sender_user.get("user_id"), other_user.get("user_id"))

                packet_data.append({
                    "chat_id": chat_id,
                    "chat_name": display_name,
                    "other_user_id": other_user_id,
                    "messages": chat_messages,
                    "block_status": block_status
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

            delete_chat(chat_id)

            import os
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            msg_file = os.path.join(BASE_DIR, "database", "data", "messages", f"{chat_id}.json")
            print(f"[DEBUG] Aranan path: {msg_file}")
            if os.path.exists(msg_file):
                os.remove(msg_file)
                print(f"[SİLME] '{chat_id}.json' mesaj dosyası silindi.")
            else:
                print(f"[UYARI] Dosya bulunamadı: {msg_file}")

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
            # Sanitize results (remove passwords)
            sanitized_results = []
            for u in results:
                sanitized_results.append({
                    "username": u.get("username"),
                    "fullname": u.get("fullname"),
                    "user_id": u.get("user_id")
                })

            response = {
                "type": "search_users_response",
                "payload": {
                    "status": "success",
                    "results": sanitized_results
                }
            }
            self.send_packet(conn, response)

        elif msg_type == "block_user_request":
            payload = packet.get("payload", {})
            blocker_id = payload.get("blocker_id")
            blocked_id = payload.get("blocked_id")
            
            block_repository.add_or_update_block(blocker_id, blocked_id, status=True)
            
            response = {
                "type": "block_user_response",
                "payload": {"status": "success", "blocker_id": blocker_id, "blocked_id": blocked_id, "is_blocked": True}
            }
            self.send_packet(conn, response)

        elif msg_type == "unblock_user_request":
            payload = packet.get("payload", {})
            blocker_id = payload.get("blocker_id")
            blocked_id = payload.get("blocked_id")
            
            block_repository.add_or_update_block(blocker_id, blocked_id, status=False)
            
            response = {
                "type": "block_user_response",
                "payload": {"status": "success", "blocker_id": blocker_id, "blocked_id": blocked_id, "is_blocked": False}
            }
            self.send_packet(conn, response)

        elif msg_type == "get_block_list_request":
            payload = packet.get("payload", {})
            user_id = payload.get("user_id")
            
            all_blocks = block_repository.get_all_blocks()
            user_blocks = [b for b in all_blocks if str(b.get("blocker_id")) == str(user_id) and b.get("isBlocked")]
            
            response = {
                "type": "get_block_list_response",
                "payload": {"status": "success", "blocks": user_blocks}
            }
            self.send_packet(conn, response)

        # elif msg_type == "create_chat_request":
        #     payload = packet.get("payload", {})
        #     members = payload.get("members", []) # [gönderen, alıcı]
            
        #     # 1. Benzersiz bir Chat ID üret (Örn: chat_17123456)
        #     import time
        #     new_chat_id = f"chat_{int(time.time())}"

        #     try:
        #         # 2. Veritabanına (chats.json) kaydet[cite: 6]
        #         # is_group=False çünkü bu bir birebir sohbet
        #         create_chat(new_chat_id, members, is_group=False)
                
        #         # 3. İsteği gönderen kişiye yanıt dön
        #         response = {
        #             "type": "create_chat_response",
        #             "payload": {
        #                 "status": "success",
        #                 "chat_id": new_chat_id,
        #                 "target_username": members[1] # Kiminle sohbet açıldıysa o
        #             }
        #         }
        #         self.send_packet(conn, response)
        #         print(f"[SOHBET] '{new_chat_id}' oluşturuldu, üyeler: {members}")
        #     except Exception as e:
        #         print(f"[SOHBET HATA] {e}")

    def send_packet(self, conn, packet_dict):
        """Senin Protocol.py yapına uygun şekilde gönderim yapar."""
        json_data = json.dumps(packet_dict) + "<END>"
        conn.sendall(json_data.encode('utf-8'))
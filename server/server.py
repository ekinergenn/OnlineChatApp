import socket
import threading
import json
import time
import os
from database.user_repository import find_user, create_user, search_users, delete_user
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
        self.last_seen = {}

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
            self.last_seen[user_to_remove] = int(time.time())  # ← YENİ
            del self.online_users[user_to_remove]
            print(f"[SİSTEM] {user_to_remove} online listesinden çıkarıldı.")

            # ← YENİ: diğer kullanıcılara offline bildirimi gönder
            self._broadcast_status(user_to_remove, "offline", self.last_seen[user_to_remove])

        if conn in self.clients:
            self.clients.remove(conn)
        conn.close()

    def _broadcast_status(self, username, status, last_seen_ts=None):
        """İlgili kullanıcının durumunu sohbet ettiği herkese bildirir."""
        all_chats = get_all_chats()
        notified = set()

        for chat in all_chats:
            if username in chat.get("members", []):
                for member in chat["members"]:
                    if member != username and member in self.online_users and member not in notified:
                        packet = {
                            "type": "user_status_update",
                            "payload": {
                                "username": username,
                                "status": status,
                                "last_seen": last_seen_ts
                            }
                        }
                        self.send_packet(self.online_users[member], packet)
                        notified.add(member)

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
                self._broadcast_status(user["username"], "online")
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
        elif msg_type == "typing_indicator":
            payload = packet.get("payload", {})
            chat_id = payload.get("chat_id")
            sender_name = payload.get("sender")
            is_typing = payload.get("is_typing", False)

            all_chats = get_all_chats()
            active_chat = get_chat_(all_chats, chat_id)

            if active_chat:
                for member in active_chat["members"]:
                    if member != sender_name and member in self.online_users:
                        self.send_packet(self.online_users[member], {
                            "type": "typing_indicator",
                            "payload": {
                                "chat_id": chat_id,
                                "sender": sender_name,
                                "is_typing": is_typing
                            }
                        })

        elif msg_type == "get_user_status_request":
            payload = packet.get("payload", {})
            target_username = payload.get("username")

            is_online = target_username in self.online_users
            last_seen_ts = self.last_seen.get(target_username)

            self.send_packet(conn, {
                "type": "get_user_status_response",
                "payload": {
                    "username": target_username,
                    "status": "online" if is_online else "offline",
                    "last_seen": last_seen_ts
                }
            })


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

                other_user_id = None
                if chat_obj and chat_obj.get("is_group"):
                    display_name = chat_obj.get("chat_name") or chat_id
                elif chat_obj and len(chat_obj.get("members", [])) == 2:
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
                    "block_status": block_status,
                    "is_group": chat_obj.get("is_group", False) if chat_obj else False
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
            username = payload.get("username", "")
            print(f"[SİLME] '{chat_id}' — '{username}' için siliniyor...")

            all_chats = get_all_chats()
            chat_obj = get_chat_(all_chats, chat_id)

            if chat_obj and chat_obj.get("is_group"):
                # Grup sohbeti: sadece üyeden çıkar, dosyayı silme
                members = chat_obj.get("members", [])
                if username in members:
                    members.remove(username)
                    chat_obj["members"] = members
                    from database.db import write_json
                    write_json("chats.json", all_chats)
                    print(f"[SİLME] '{username}' gruptan çıkarıldı, grup devam ediyor.")

                # Eğer grupta kimse kalmadıysa tamamen sil
                if not members:
                    delete_chat(chat_id)
                    import os
                    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    msg_file = os.path.join(BASE_DIR, "database", "data", "messages", f"{chat_id}.json")
                    if os.path.exists(msg_file):
                        os.remove(msg_file)
            else:
                # Birebir sohbet: tamamen sil
                delete_chat(chat_id)
                import os
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                msg_file = os.path.join(BASE_DIR, "database", "data", "messages", f"{chat_id}.json")
                if os.path.exists(msg_file):
                    os.remove(msg_file)
                    print(f"[SİLME] '{chat_id}.json' mesaj dosyası silindi.")

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

        elif msg_type == "get_all_users_request":
            payload = packet.get("payload", {})
            requester = payload.get("username", "")

            from database.user_repository import get_all_users
            all_users = get_all_users()

            sanitized = []
            for u in all_users:
                if u.get("username") != requester:
                    sanitized.append({
                        "username": u.get("username"),
                        "fullname": u.get("fullname"),
                        "user_id": u.get("user_id")
                    })

            response = {
                "type": "get_all_users_response",
                "payload": {"status": "success", "users": sanitized}
            }
            self.send_packet(conn, response)

        elif msg_type == "create_group_request":
            payload = packet.get("payload", {})
            group_name = payload.get("group_name", "")
            members = payload.get("members", [])

            import time
            new_chat_id = f"group_{int(time.time())}"

            try:
                create_chat(new_chat_id, members, is_group=True, chat_name=group_name)

                from database.db import write_json
                write_json(f"messages/{new_chat_id}.json", [])

                response = {
                    "type": "create_group_response",
                    "payload": {
                        "status": "success",
                        "chat_id": new_chat_id,
                        "group_name": group_name,
                        "members": members
                    }
                }
                self.send_packet(conn, response)

                for member in members:
                    if member in self.online_users and self.online_users[member] != conn:
                        self.send_packet(self.online_users[member], response)

            except Exception as e:
                print(f"[HATA] Grup oluşturulamadı: {e}")
                response = {
                    "type": "create_group_response",
                    "payload": {"status": "fail", "message": str(e)}
                }
                self.send_packet(conn, response)

        elif msg_type == "delete_account_request":
            payload = packet.get("payload", {})
            username = payload.get("username")
            print(f"[DEBUG] Silme isteği geldi. Kullanıcı: '{username}'")

            # user chatleri temizlenir
            from database.chat_repository import cleanup_user_chats
            cleanup_user_chats(username)

            # Repository fonksiyonunu çağır
            from database.user_repository import delete_user
            success = delete_user(username)
            if success:
                print(f"[DEBUG] Silme BAŞARILI.")
                response = {"type": "delete_account_response", "payload": {"status": "success"}}
            else:
                print(f"[DEBUG] Silme BAŞARISIZ. Kullanıcı bulunamadı veya dosya yazılamadı.")
                response = {"type": "delete_account_response", "payload": {"status": "fail"}}

            self.send_packet(conn, response)

        elif msg_type == "update_profile_request":
            payload = packet.get("payload", {})
            username = payload.get("username")

            from database.user_repository import update_user_info
            success = update_user_info(
                username=username,
                fullname=payload.get("fullname"),
                email=payload.get("email"),
                tel=payload.get("tel")
            )

            response = {
                "type": "update_profile_response",
                "payload": {"status": "success" if success else "fail"}
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
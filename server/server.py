import socket
import threading
import json
import time
import os
from database.user_repository import (
    find_user, create_user, search_users, delete_user, update_public_key, 
    get_public_key, get_privacy_settings, update_privacy_settings, update_private_key_backup,
    update_user_info, get_all_users
)
from database.message_repository import save_message, get_messages, mark_messages_as_read
from database.chat_repository import create_chat, get_all_chats, get_chat_, get_user_chats, delete_chat, hide_group_chat, leave_group_chat
from database import block_repository, community_repository
from database.db import write_json
from database.starred_repository import add_starred_message, remove_starred_message, get_user_starred_messages

class ChatServer:
    def __init__(self, host='0.0.0.0', port=12345):
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
                raw_data = conn.recv(4096)
                if not raw_data: break
                
                buffer += raw_data.decode('utf-8')
                while "<END>" in buffer:
                    msg, buffer = buffer.split("<END>", 1)
                    if not msg: continue
                    try:
                        packet = json.loads(msg)
                        self.process_request(conn, packet)
                    except json.JSONDecodeError as e:
                        print(f"[HATA] JSON Decode Hatası: {e}")
            except Exception as e:
                print(f"[HATA] {addr} bağlantı hatası: {e}")
                break

        # Ayrılma işlemleri
        user_to_remove = next((u for u, s in self.online_users.items() if s == conn), None)
        if user_to_remove:
            self.last_seen[user_to_remove] = int(time.time())
            del self.online_users[user_to_remove]
            self._broadcast_status(user_to_remove, "offline", self.last_seen[user_to_remove])
        
        if conn in self.clients: self.clients.remove(conn)
        conn.close()

    def _broadcast_status(self, username, status, last_seen_ts=None):
        privacy = get_privacy_settings(username)
        if not privacy.get("online_status", True): status = "offline"
        if not privacy.get("last_seen", True): last_seen_ts = None

        all_chats = get_all_chats()
        notified = set()
        for chat in all_chats:
            if username in chat.get("members", []):
                for member in chat["members"]:
                    if member != username and member in self.online_users and member not in notified:
                        packet = {
                            "type": "user_status_update",
                            "payload": {"username": username, "status": status, "last_seen": last_seen_ts}
                        }
                        self.send_packet(self.online_users[member], packet)
                        notified.add(member)

    def process_request(self, conn, packet):
        msg_type = packet.get("type")
        payload = packet.get("payload", {})

        if msg_type == "login_request": self.handle_login(conn, payload)
        elif msg_type == "register_request": self.handle_register(conn, payload)
        elif msg_type == "chat_message": self.handle_chat_message(conn, payload)
        elif msg_type == "typing_indicator": self.handle_typing_indicator(payload)
        elif msg_type == "get_user_status_request": self.handle_get_user_status(conn, payload)
        elif msg_type == "mark_messages_read": self.handle_mark_read(payload)
        elif msg_type == "get_privacy_settings_request": self.handle_get_privacy(conn, payload)
        elif msg_type == "update_privacy_settings_request": self.handle_update_privacy(conn, payload)
        elif msg_type == "get_user_chats_request": self.handle_get_user_chats(conn, payload)
        elif msg_type == "create_chat_request": self.handle_create_chat(conn, payload)
        elif msg_type == "create_group_request": self.handle_create_group(conn, payload)
        elif msg_type == "delete_chat_request": self.handle_delete_chat(conn, payload)
        elif msg_type == "search_users_request": self.handle_search_users(conn, payload)
        elif msg_type == "get_all_users_request": self.handle_get_all_users(conn, payload)
        elif msg_type == "block_user_request": self.handle_block(conn, payload, True)
        elif msg_type == "unblock_user_request": self.handle_block(conn, payload, False)
        elif msg_type == "get_block_list_request": self.handle_get_block_list(conn, payload)
        elif msg_type == "delete_account_request": self.handle_delete_account(conn, payload)
        elif msg_type == "update_profile_request": self.handle_update_profile(conn, payload)
        elif msg_type == "update_public_key_request": self.handle_update_public_key(conn, payload)
        elif msg_type == "get_public_key_request": self.handle_get_public_key(conn, payload)
        elif msg_type == "update_private_key_backup_request": self.handle_update_private_key_backup(conn, payload)
        elif msg_type == "star_message_request": self.handle_star_message(conn, payload)
        elif msg_type == "get_starred_messages_request": self.handle_get_starred_messages(conn, payload)
        elif msg_type == "unstar_request": self.handle_unstar(conn, payload)
        elif msg_type == "community_message": self.handle_community_message(payload)
        elif msg_type == "create_community_request": self.handle_create_community(conn, payload)
        elif msg_type == "join_community_request": self.handle_join_community(conn, payload)
        elif msg_type == "search_communities_request": self.handle_search_communities(conn, payload)
        elif msg_type == "get_user_communities_request": self.handle_get_user_communities(conn, payload)
        elif msg_type == "logout_request": self.handle_logout(conn, payload)

    def send_packet(self, conn, packet_dict):
        try:
            json_data = json.dumps(packet_dict) + "<END>"
            conn.sendall(json_data.encode('utf-8'))
        except Exception as e:
            print(f"[AĞ HATASI] Paket gönderilemedi: {e}")

    # --- Handlers ---
    def handle_login(self, conn, payload):
        username = payload.get("name")
        password = payload.get("password")

        # 1. Zaten giriş yapmış mı kontrol et (Eşzamanlı girişi engelle)
        if username in self.online_users:
            response = {
                "type": "login_response", 
                "payload": {
                    "status": "fail", 
                    "message": "Bu hesap şu an başka bir cihazda aktif!"
                }
            }
            self.send_packet(conn, response)
            return

        user = find_user(username)
        if user and user["password"] == password:
            self.online_users[username] = conn
            self._broadcast_status(username, "online")
            response = {
                "type": "login_response",
                "payload": {
                    "status": "success",
                    "username": user["username"],
                    "fullname": user["fullname"],
                    "email": user["email"],
                    "tel": user["tel"],
                    "encrypted_private_key": user.get("encrypted_private_key"),
                    "user_id": user["user_id"]
                }
            }
        else:
            response = {"type": "login_response", "payload": {"status": "fail", "message": "Hatalı giriş!"}}
        self.send_packet(conn, response)

    def handle_logout(self, conn, payload):
        username = payload.get("username")
        if username in self.online_users:
            print(f"[SUNUCU] {username} çıkış yaptı.")
            self.last_seen[username] = int(time.time())
            del self.online_users[username]
            self._broadcast_status(username, "offline", self.last_seen[username])
            
            # Onay gönder
            self.send_packet(conn, {"type": "logout_response", "payload": {"status": "success"}})

    def handle_register(self, conn, payload):
        success = create_user(payload.get("username"), payload.get("password"), payload.get("fullname"), payload.get("email"), payload.get("tel", ""))
        self.send_packet(conn, {"type": "register_response", "payload": {"status": "success" if success else "fail"}})

    def handle_chat_message(self, conn, payload):
        chat_id = payload.get("chat_id")
        sender = payload.get("sender")
        all_chats = get_all_chats()
        chat = get_chat_(all_chats, chat_id)
        if chat and sender in chat["members"]:
            # Engelleme kontrolü
            receivers = [m for m in chat["members"] if m != sender]
            sender_user = find_user(sender)
            can_send = True
            if sender_user:
                for r_name in receivers:
                    receiver_user = find_user(r_name)
                    if receiver_user:
                        if block_repository.check_block_status(sender_user["user_id"], receiver_user["user_id"]) != "none":
                            can_send = False; break
            
            if not can_send:
                self.send_packet(conn, {"type": "error", "payload": {"message": "Engelleme nedeniyle mesaj gönderilemedi."}})
                return

            saved = save_message(payload)
            for m in chat["members"]:
                if m in self.online_users:
                    self.send_packet(self.online_users[m], {"type": "chat_message", "payload": saved})

    def handle_typing_indicator(self, payload):
        chat_id = payload.get("chat_id")
        sender = payload.get("sender")
        all_chats = get_all_chats()
        chat = get_chat_(all_chats, chat_id)
        if chat:
            for m in chat["members"]:
                if m != sender and m in self.online_users:
                    self.send_packet(self.online_users[m], {"type": "typing_indicator", "payload": payload})

    def handle_get_user_status(self, conn, payload):
        target = payload.get("username")
        privacy = get_privacy_settings(target)
        is_online = target in self.online_users if privacy.get("online_status", True) else False
        last_seen = self.last_seen.get(target) if privacy.get("last_seen", True) else None
        self.send_packet(conn, {"type": "get_user_status_response", "payload": {"username": target, "status": "online" if is_online else "offline", "last_seen": last_seen}})

    def handle_mark_read(self, payload):
        chat_id = payload.get("chat_id")
        message_ids = payload.get("message_ids", [])
        username = payload.get("username")
        mark_messages_as_read(chat_id, message_ids, username)
        
        privacy = get_privacy_settings(username)
        if privacy.get("read_receipts", True):
            all_chats = get_all_chats()
            chat = get_chat_(all_chats, chat_id)
            if chat:
                # Grup ise herkes okudu mu kontrolü
                is_group = chat.get("is_group", False)
                members = chat.get("members", [])
                msgs = get_messages(chat_id)
                
                broadcast_packet = {
                    "type": "messages_read",
                    "payload": {"chat_id": chat_id, "message_ids": message_ids, "read_by": username, "is_group": is_group}
                }
                if is_group and len(message_ids) > 0:
                    fm = next((m for m in msgs if m.get("message_id") == message_ids[0]), None)
                    if fm and len(fm.get("read_by", [])) >= len(members):
                        broadcast_packet["payload"]["all_read"] = True

                for member in chat["members"]:
                    if member != username and member in self.online_users:
                        self.send_packet(self.online_users[member], broadcast_packet)

    def handle_get_privacy(self, conn, payload):
        username = payload.get("username")
        settings = get_privacy_settings(username)
        self.send_packet(conn, {"type": "get_privacy_settings_response", "payload": {"username": username, "settings": settings}})

    def handle_update_privacy(self, conn, payload):
        username = payload.get("username")
        settings = payload.get("settings", {})
        success = update_privacy_settings(username, settings)
        if success:
            # Anında durum yayınla
            if "online_status" in settings:
                status = "online" if username in self.online_users and settings["online_status"] else "offline"
                self._broadcast_status(username, status, self.last_seen.get(username))
        self.send_packet(conn, {"type": "update_privacy_settings_response", "payload": {"status": "success" if success else "fail"}})

    def handle_get_user_chats(self, conn, payload):
        username = payload.get("username")
        chat_ids = get_user_chats(username)
        all_chats = get_all_chats()
        results = []
        
        privacy_cache = {}
        for cid in chat_ids:
            chat_obj = get_chat_(all_chats, cid)
            if chat_obj:
                messages = get_messages(cid)
                # Gizlilik filtresi: read_receipts kapalıysa o kişiyi listeden sil
                for msg in messages:
                    filtered_read_by = []
                    for reader in msg.get("read_by", []):
                        if reader not in privacy_cache:
                            privacy_cache[reader] = get_privacy_settings(reader).get("read_receipts", True)
                        if reader == username or privacy_cache[reader]:
                            filtered_read_by.append(reader)
                    msg["read_by"] = filtered_read_by

                # Diğer kullanıcı ID'sini ve engelleme durumunu hesapla
                other_user_id = None
                block_status = "none"
                if not chat_obj.get("is_group") and len(chat_obj["members"]) == 2:
                    other_name = [m for m in chat_obj["members"] if m != username][0]
                    ou = find_user(other_name)
                    if ou:
                        other_user_id = ou["user_id"]
                        me = find_user(username)
                        if me:
                            block_status = block_repository.check_block_status(me["user_id"], other_user_id)

                # Okunmamış mesaj sayısını hesapla
                unread_count = 0
                for m in messages:
                    if username not in m.get("read_by", []):
                        unread_count += 1

                results.append({
                    "chat_id": cid,
                    "chat_name": chat_obj.get("chat_name") or ([m for m in chat_obj["members"] if m != username][0] if len(chat_obj["members"])==2 else cid),
                    "other_user_id": other_user_id,
                    "block_status": block_status,
                    "unread_count": unread_count,
                    "messages": messages,
                    "members": chat_obj["members"],
                    "is_group": chat_obj.get("is_group", False)
                })
        self.send_packet(conn, {"type": "get_user_chats_response", "payload": {"status": "success", "chats": results}})

    def handle_create_chat(self, conn, payload):
        members = payload.get("members", [])
        chat_id = f"chat_{int(time.time())}"
        create_chat(chat_id, members, is_group=False)
        write_json(f"messages/{chat_id}.json", [])
        
        other_user_id = None
        if len(members) > 1:
            target_user = find_user(members[1])
            if target_user:
                other_user_id = target_user.get("user_id")

        self.send_packet(conn, {
            "type": "create_chat_response", 
            "payload": {
                "status": "success", 
                "chat_id": chat_id, 
                "target_username": members[1] if len(members)>1 else "",
                "other_user_id": other_user_id
            }
        })

    def handle_create_group(self, conn, payload):
        chat_id = f"group_{int(time.time())}"
        create_chat(chat_id, payload["members"], is_group=True, chat_name=payload["group_name"])
        write_json(f"messages/{chat_id}.json", [])
        resp = {"type": "create_group_response", "payload": {"status": "success", "chat_id": chat_id, "group_name": payload["group_name"], "members": payload["members"]}}
        for m in payload["members"]:
            if m in self.online_users: self.send_packet(self.online_users[m], resp)

    def handle_delete_chat(self, conn, payload):
        chat_id = payload.get("chat_id")
        chat_name = payload.get("chat_name")
        username = payload.get("username", "")
        action = payload.get("action", "delete")

        all_chats = get_all_chats()
        chat_obj = get_chat_(all_chats, chat_id)
        
        success = False
        if chat_obj and chat_obj.get("is_group"):
            if action == "leave":
                success = leave_group_chat(chat_id, username)
            else:
                success = hide_group_chat(chat_id, username)
        else:
            success = delete_chat(chat_id)

        self.send_packet(conn, {
            "type": "delete_chat_response", 
            "payload": {
                "status": "success" if success else "fail", 
                "chat_id": chat_id,
                "chat_name": chat_name,
                "action": action
            }
        })

        # Eğer ikili sohbet silindiyse diğer kullanıcıyı bilgilendir
        if success and chat_obj and not chat_obj.get("is_group"):
            for m in chat_obj.get("members", []):
                if m != username and m in self.online_users:
                    self.send_packet(self.online_users[m], {
                        "type": "chat_deleted_notification",
                        "payload": {
                            "chat_id": chat_id,
                            "chat_name": username  # Sileyen kişi, diğerinin listesinde chat_name olarak görünür
                        }
                    })

    def handle_search_users(self, conn, payload):
        query = payload.get("query", "").lower()
        requester = payload.get("username", "")
        results = search_users(query, exclude_username=requester)
        sanitized = [{"username": u["username"], "fullname": u["fullname"], "user_id": u["user_id"], "is_group": False} for u in results]
        
        # Grupları da ara
        all_chats = get_all_chats()
        for chat in all_chats:
            if chat.get("is_group") and requester in chat.get("members", []):
                if query in chat.get("chat_name", "").lower():
                    sanitized.append({"is_group": True, "chat_id": chat["chat_id"], "chat_name": chat["chat_name"], "members": chat["members"]})
        
        self.send_packet(conn, {"type": "search_users_response", "payload": {"status": "success", "results": sanitized}})

    def handle_get_all_users(self, conn, payload):
        users = get_all_users()
        sanitized = [{"username": u["username"], "fullname": u["fullname"], "user_id": u["user_id"]} for u in users if u["username"] != payload.get("username")]
        self.send_packet(conn, {"type": "get_all_users_response", "payload": {"status": "success", "users": sanitized}})

    def handle_block(self, conn, payload, status):
        blocker_id = payload.get("blocker_id")
        blocked_id = payload.get("blocked_id")
        
        if blocker_id and blocked_id:
            block_repository.add_or_update_block(blocker_id, blocked_id, status)
            
            # Güncel durumu hesapla
            block_status = block_repository.check_block_status(blocker_id, blocked_id)
            
            response = {
                "type": "block_user_response",
                "payload": {
                    "status": "success",
                    "blocker_id": blocker_id,
                    "blocked_id": blocked_id,
                    "block_status": block_status
                }
            }
            self.send_packet(conn, response)
            
            # Eğer karşı taraf da online ise ona da durumu bildir
            # (Engellendiğini anında anlaması için)
            blocked_user = next((u for u, data in self.online_users.items() if find_user(u) and str(find_user(u)["user_id"]) == str(blocked_id)), None)
            if blocked_user:
                # Karşı taraf için durumu tekrar hesapla (onun perspektifinden)
                other_status = block_repository.check_block_status(blocked_id, blocker_id)
                self.send_packet(self.online_users[blocked_user], {
                    "type": "block_user_response",
                    "payload": {
                        "status": "success",
                        "blocker_id": blocked_id,
                        "blocked_id": blocker_id,
                        "block_status": other_status
                    }
                })

    def handle_get_block_list(self, conn, payload):
        blocks = block_repository.get_all_blocks()
        all_users = get_all_users()
        u_dict = {str(u["user_id"]): u["username"] for u in all_users}
        user_blocks = []
        for b in blocks:
            if str(b["blocker_id"]) == str(payload["user_id"]) and b["isBlocked"]:
                user_blocks.append({"blocker_id": b["blocker_id"], "blocked_id": b["blocked_id"], "blocked_username": u_dict.get(str(b["blocked_id"]), "Bilinmeyen"), "isBlocked": True})
        self.send_packet(conn, {"type": "get_block_list_response", "payload": {"status": "success", "blocks": user_blocks}})

    def handle_delete_account(self, conn, payload):
        from database.chat_repository import cleanup_user_chats
        cleanup_user_chats(payload["username"])
        success = delete_user(payload["username"])
        self.send_packet(conn, {"type": "delete_account_response", "payload": {"status": "success" if success else "fail"}})

    def handle_update_profile(self, conn, payload):
        success = update_user_info(payload["username"], payload["fullname"], payload["email"], payload["tel"])
        self.send_packet(conn, {"type": "update_profile_response", "payload": {"status": "success" if success else "fail"}})

    def handle_update_public_key(self, conn, payload):
        success = update_public_key(payload["username"], payload["public_key"])
        print(f"[E2EE] Public key update: {success}")

    def handle_get_public_key(self, conn, payload):
        pk = get_public_key(payload["username"])
        self.send_packet(conn, {"type": "get_public_key_response", "payload": {"status": "success" if pk else "not_found", "username": payload["username"], "public_key": pk}})

    def handle_update_private_key_backup(self, conn, payload):
        success = update_private_key_backup(payload["username"], payload["encrypted_private_key"])
        print(f"[E2EE] Private key backup sync: {success}")

    def handle_star_message(self, conn, payload):
        action = payload.get("action", "star")
        if action == "star": success = add_starred_message(payload)
        else: success = remove_starred_message(payload.get("message_id"), payload.get("starred_by"))
        self.send_packet(conn, {"type": "star_message_response", "payload": {"status": "success" if success else "fail"}})

    def handle_get_starred_messages(self, conn, payload):
        msgs = get_user_starred_messages(payload["username"])
        self.send_packet(conn, {"type": "get_starred_messages_response", "payload": {"messages": msgs}})

    def handle_unstar(self, conn, payload):
        success = remove_starred_message(payload["message_id"], payload["username"])
        self.send_packet(conn, {"type": "unstar_response", "payload": {"success": success, "message_id": payload["message_id"]}})

    def handle_community_message(self, payload):
        comm_id = int(payload["community_id"])
        sender = payload["sender"]
        communities = community_repository.get_all_communities()
        target = next((c for c in communities if c["community_id"] == comm_id), None)
        if target and target["creator"] == sender:
            msg_payload = {"chat_id": f"community_{comm_id}", "sender": sender, "content": payload["content"], "timestamp": time.time(), "message_id": int(time.time()*1000)}
            save_message(msg_payload)
            broadcast = {"type": "community_message", "payload": {"community_id": comm_id, "sender": sender, "content": payload["content"], "timestamp": time.time()}}
            for m in target["members"]:
                if m in self.online_users: self.send_packet(self.online_users[m], broadcast)

    def handle_create_community(self, conn, payload):
        new_comm = community_repository.create_community(payload["name"], payload["creator"])
        write_json(f"messages/community_{new_comm['community_id']}.json", [])
        self.send_packet(conn, {"type": "create_community_response", "payload": {"status": "success", "community": new_comm}})

    def handle_join_community(self, conn, payload):
        success = community_repository.join_community(payload["community_id"], payload["username"])
        self.send_packet(conn, {"type": "join_community_response", "payload": {"status": "success" if success else "fail", "community_id": payload["community_id"]}})

    def handle_search_communities(self, conn, payload):
        results = community_repository.search_communities(payload["query"])
        self.send_packet(conn, {"type": "search_communities_response", "payload": {"results": results}})

    def handle_get_user_communities(self, conn, payload):
        comms = community_repository.get_user_communities(payload["username"])
        results = []
        for c in comms:
            results.append({"community_id": c["community_id"], "name": c["name"], "creator": c["creator"], "members": c["members"], "messages": get_messages(f"community_{c['community_id']}")[-50:]})
        self.send_packet(conn, {"type": "get_user_communities_response", "payload": {"communities": results}})

if __name__ == "__main__":
    ChatServer().start()

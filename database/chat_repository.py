import os

from database.db import read_json, write_json

import time


BASE_DIR = os.path.dirname(__file__)  # chat_repository.py'nin bulunduğu yer
DATA_DIR = os.path.join(BASE_DIR, "data")

FILENAME = "chats.json"
MESSAGES_DIR = os.path.join(DATA_DIR, "messages")

def get_all_chats() -> dict | list:
    """Tüm sohbetleri bir sözlük olarak döndürür."""
    return read_json(FILENAME)

def get_user_chats(username: str) -> list:
    """Kullanıcının dahil olduğu sohbetleri liste olarak döndürür."""
    chats = get_all_chats()
    user_chats = []

    for chat in chats:
        for us in chat["members"]:
            if us == username:
                user_chats.append(chat["chat_id"])
    return user_chats

def get_chat_(chats,chat_id:str) -> None | dict:
    for chat in chats:
        if chat["chat_id"] == chat_id:
            return chat


def create_chat(chat_id: str, members: list, is_group: bool = False,chat_name:str = None) -> bool:
    """Yeni bir sohbet oluşturur. chat_id'yi anahtar olarak kullanır."""
    chats = get_all_chats()
    
    if get_chat_(chats,chat_id) != None:
        return False
    
    new_chat = {
        "chat_name":chat_name,
        "chat_id": chat_id,
        "members": members,
        "is_group": is_group,
        "created_at": time.time()
    }
    chats.append(new_chat)
    write_json(FILENAME, chats)
    return True

def add_member(chat_id: int, username: str) -> bool:
    """Belirli bir chat_id'ye sahip sohbete yeni üye ekler."""
    chats = get_all_chats()
    chat = get_chat_(chats,chat_id)
    if chat == None:
        return False
    
    chat["members"].append(username)
    write_json(FILENAME, chats)
    return True


def delete_chat(chat_id: int) -> bool:
    """Sohbeti chat_id kullanarak siler."""
    chats = get_all_chats()
    chat = get_chat_(chats,chat_id)
    if chat == None:
        return False
    
    chats.remove(chat)
    write_json(FILENAME, chats)
    return True


def cleanup_user_chats(username):
    all_chats = get_all_chats()
    new_chats = []

    for chat in all_chats:
        chat_id = chat.get("chat_id")
        members = chat.get("members", [])
        is_group = chat.get("is_group", False)

        if username in members:
            msg_file_path = os.path.join(MESSAGES_DIR, f"{chat_id}.json")

            if not is_group:
                # ikili sohbetleri tamamen siler
                if os.path.exists(msg_file_path):
                    try:
                        os.remove(msg_file_path)
                    except Exception as e:
                        print(f"[HATA] Dosya silinemedi: {e}")
                # bu sohbeti new_chats listesine eklemiyoruz (listeden siliniyor)
                continue
            else:
                #grup sohbetinde kullanıcıyı üyelerden çıkar
                chat["members"] = [m for m in members if m != username]
                #grup mesaj dosyasının içindeki mesajları temizle
                clean_group_messages_content(chat_id, username)

        new_chats.append(chat)

    # chats.json dosyasını güncelle
    write_json(FILENAME, new_chats)
    print(f"[BİLGİ] {username} için sohbet listesi temizlendi.")


def clean_group_messages_content(chat_id, username):
    file_path = os.path.join(MESSAGES_DIR, f"{chat_id}.json")

    if os.path.exists(file_path):
        try:
            messages = read_json(file_path)
            if not isinstance(messages, list): return

            initial_count = len(messages)

            # göndericisi silinen kullanıcı olan mesajları filtrele (Sil)
            # klan mesajlarda read_by listesinden kullanıcıyı çıkar
            updated_messages = []
            for msg in messages:
                if msg.get("sender") == username:
                    continue  # Bu mesajı listeye alma (Silindi)

                if "read_by" in msg and isinstance(msg["read_by"], list):
                    if username in msg["read_by"]:
                        msg["read_by"].remove(username)

                updated_messages.append(msg)

            # Dosyayı güncelle
            write_json(file_path, updated_messages)
            deleted_count = initial_count - len(updated_messages)
            print(f"[TEMİZLİK] {chat_id} grubunda {deleted_count} mesaj ve okundu bilgileri temizlendi.")

        except Exception as e:
            print(f"[HATA] Grup mesajları temizlenirken hata: {e}")
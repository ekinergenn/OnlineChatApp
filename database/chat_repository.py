from database.db import read_json, write_json

import time

FILENAME = "chats.json"

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

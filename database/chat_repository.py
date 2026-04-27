from database.db import read_json, write_json

FILENAME = "chats.json"

def get_all_chats() -> dict:
    return read_json(FILENAME)

def get_user_chats(username: str) -> list:
    """Kullanıcının dahil olduğu sohbetleri döndürür."""
    chats = get_all_chats()
    user_chats = []
    for chat_name, chat_data in chats.items():
        if username in chat_data.get("members", []):
            user_chats.append(chat_data)
    return user_chats

def create_chat(chat_name: str, members: list, is_group: bool = False) -> bool:
    """Yeni sohbet oluşturur."""
    chats = get_all_chats()
    if chat_name in chats:
        return False
    chats[chat_name] = {
        "chat_name": chat_name,
        "members": members,
        "is_group": is_group,
        "created_at": __import__('time').time()
    }
    write_json(FILENAME, chats)
    return True

def add_member(chat_name: str, username: str) -> bool:
    """Sohbete yeni üye ekler."""
    chats = get_all_chats()
    if chat_name not in chats:
        return False
    if username not in chats[chat_name]["members"]:
        chats[chat_name]["members"].append(username)
        write_json(FILENAME, chats)
    return True

def delete_chat(chat_name: str) -> bool:
    chats = get_all_chats()
    if chat_name not in chats:
        return False
    del chats[chat_name]
    write_json(FILENAME, chats)
    return True
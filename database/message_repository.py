from database.db import read_json, write_json
import time,os

from database.db import read_json, write_json
import os

def get_messages(chat_id: str) -> list:
    file_path = "messages/" + chat_id + ".json"
    return read_json(file_path)

def save_message(payload) -> dict:
    chat_id = str(payload.get("chat_id"))
    # 1. Mevcut mesajları ÇEK
    all_messages = get_messages(chat_id)
    
    # 2. Yeni mesajı listeye EKLE
    all_messages.append(payload)
    
    # 3. Tüm listeyi dosyaya YAZ (Üzerine yazma sorunu burada çözülür)[cite: 7]
    write_json("messages/" + chat_id + ".json", all_messages)
    return payload

# def delete_chat_messages(chat_name: str):
#     all_messages = read_json(FILENAME)
#     if chat_name in all_messages:
#         del all_messages[chat_name]
#         write_json(FILENAME, all_messages)

def mark_messages_as_read(chat_id: str, message_ids: list, username: str) -> None:
    all_messages = get_messages(chat_id)
    updated = False
    for msg in all_messages:
        if msg.get("message_id") in message_ids:
            read_by = msg.get("read_by", [])
            if username not in read_by:
                read_by.append(username)
                msg["read_by"] = read_by
                updated = True
    
    if updated:
        write_json("messages/" + chat_id + ".json", all_messages)

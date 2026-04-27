from database.db import read_json, write_json
import time

FILENAME = "messages.json"

def get_messages(chat_name: str) -> list:
    all_messages = read_json(FILENAME)
    if not isinstance(all_messages, dict):
        return []
    return all_messages.get(chat_name, [])

def save_message(chat_name: str, sender: str, content: str, sender_id: int) -> dict:
    all_messages = read_json(FILENAME)
    if not isinstance(all_messages, dict):
        all_messages = {}

    if chat_name not in all_messages:
        all_messages[chat_name] = []

    message = {
        "message_id": int(time.time() * 1000),
        "chat_name": chat_name,
        "sender": sender,
        "sender_id": sender_id,
        "content": content,
        "timestamp": int(time.time()),
        "status": "delivered",  # sent → delivered → read
        "is_starred": False,
        "read_by": []
    }

    all_messages[chat_name].append(message)
    write_json(FILENAME, all_messages)
    return message

def delete_chat_messages(chat_name: str):
    all_messages = read_json(FILENAME)
    if chat_name in all_messages:
        del all_messages[chat_name]
        write_json(FILENAME, all_messages)
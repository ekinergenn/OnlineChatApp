from db import read_json, write_json
import time

FILENAME = "messages/messages.json"

def get_messages(chat_id: str) -> list:
    all_messages = read_json("messages/" + chat_id + ".json")
    return all_messages

def save_message(payload) -> dict:
    all_messages = get_messages(payload["chat_id"])
    all_messages.append(payload)
    write_json("messages/" + payload["chat_id"] + ".json",all_messages)
    return payload

# def delete_chat_messages(chat_name: str):
#     all_messages = read_json(FILENAME)
#     if chat_name in all_messages:
#         del all_messages[chat_name]
#         write_json(FILENAME, all_messages)


save_message({"chat_id":"chat_0",
              "sender":"ali",
              "content":"merhaba",
              "timestamp":2342424.24423,
              "status":"dd",
              "read_by":[]})
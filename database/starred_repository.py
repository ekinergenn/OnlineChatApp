import os
import json
from database.db import read_json, write_json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
FILENAME = os.path.join(DATA_DIR, "starred_messages.json")


def get_all_starred() -> list:
    #Tüm yıldızlı mesajları JSON dosyasından okur
    if not os.path.exists(FILENAME):
        # Dosya yoksa boş bir liste ile oluştur
        with open(FILENAME, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return []
    return read_json(FILENAME)


def add_starred_message(message_data: dict) -> bool:
    #yeni bir yıldızlı mesaj ekler veya mevcutsa günceller
    starred = get_all_starred()

    # Güvenlik kontrolü: starred_by alanı boş gelmemeli
    if not message_data.get("starred_by"):
        print("[HATA] starred_by alanı boş, kaydedilmiyor!")
        return False

    # aynı kullanıcı aynı mesajı tekrar yıldızlamasın
    for s in starred:
        if s["message_id"] == message_data["message_id"] and s["starred_by"] == message_data["starred_by"]:
            print("[BİLGİ] Mesaj zaten yıldızlı.")
            return False

    starred.append(message_data)
    try:
        write_json(FILENAME, starred)
        print(f"[REPOSİTORY] JSON başarıyla güncellendi: {FILENAME}")
        return True
    except Exception as e:
        print(f"[HATA] Dosya yazılamadı: {e}")
        return False

def remove_starred_message(message_id: str, username: str) -> bool:
    #bir mesajın yıldızını kaldırır
    starred = get_all_starred()
    # hem mesaj ID'si hem de kullanıcı adı eşleşmeli
    new_starred = [s for s in starred if not (s["message_id"] == message_id and s["starred_by"] == username)]

    if len(starred) != len(new_starred):
        write_json(FILENAME, new_starred)
        return True
    return False

def get_user_starred_messages(username: str) -> list:
    #sadece belirli bir kullanıcıya ait yıldızlı mesajları döner
    starred = get_all_starred()
    return [s for s in starred if s.get("starred_by") == username]
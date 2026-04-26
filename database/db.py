import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "data")

print(f"[DB INIT] BASE_DIR = {BASE_DIR}")  # ← ekle
print(f"[DB INIT] DB_PATH = {DB_PATH}")

def _get_path(filename: str) -> str:
    return os.path.join(DB_PATH, filename)

def read_json(filename: str) -> dict | list:
    path = _get_path(filename)
    print(f"[DB] Okunuyor: {os.path.abspath(path)}")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(filename: str, data) -> None:
    path = _get_path(filename)
    os.makedirs(DB_PATH, exist_ok=True)
    print(f"[DB] Yazılıyor: {os.path.abspath(path)}")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "data")

print(f"[DB INIT] BASE_DIR = {BASE_DIR}")
print(f"[DB INIT] DB_PATH = {DB_PATH}")

def _get_path(filename: str) -> str:
    return os.path.join(DB_PATH, filename)

def read_json(filename: str) -> dict | list:
    path = _get_path(filename)
    
    # 1. Kontrol: Dosya hiç yoksa boş bir liste döndür
    if not os.path.exists(path):
        print(f"[DB] Dosya bulunamadı, boş liste dönüyor: {path}")
        return []

    # 2. Kontrol: Dosya var ama içi boşsa (0 byte) hata almamak için kontrol
    if os.path.getsize(path) == 0:
        print(f"[DB] Dosya boş (0 byte), boş liste dönüyor: {path}")
        return []

    print(f"[DB] Okunuyor: {os.path.abspath(path)}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Dosya içeriği bozuksa veya JSON formatında değilse
        print(f"[DB] HATA: Dosya içeriği bozuk: {path}")
        return []

def write_json(filename: str, data) -> None:
    path = _get_path(filename)
    
    # Klasör yapısını dinamik olarak oluştur (Örn: messages/ klasörü yoksa oluşturur)
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        
    print(f"[DB] Yazılıyor: {os.path.abspath(path)}")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
import os

from database.db import read_json, write_json

FILENAME = "users.json"


def get_all_users() -> dict | list:
    return read_json(FILENAME)


def find_user(username: str) -> dict | None:
    users = get_all_users()
    for user in users:
        if user["username"] == username:
            return user


def create_user(username: str, password: str, fullname: str, email: str, tel: str) -> bool:
    users = get_all_users()
    if find_user(username) != None:
        return False

    new_user = {
        "username": username,
        "password": password,  # ileride şifrelenecek
        "fullname": fullname,
        "email": email,
        "tel": tel,
        "user_id": len(users) + 1
    }
    users.append(new_user)
    write_json(FILENAME, users)
    return True


def search_users(query: str, exclude_username: str = None) -> list:
    """
    Kullanıcıları kullanıcı adı, telefon veya isim üzerinden arar.
    Aramayı yapan kullanıcıyı (exclude_username) sonuçlardan hariç tutar.
    """
    users = get_all_users()  # Bu fonksiyon liste döndürür
    results = []
    query = query.lower().strip()

    # Liste üzerinde doğrudan döngü kurmalısın (items() kullanmadan)
    for user in users:
        username = user.get("username", "")

        # Aramayı yapan kullanıcıyı sonuçlarda gösterme
        if exclude_username and username == exclude_username:
            continue

        # Arama kriterlerini kontrol et (Küçük harfe çevirerek karşılaştır)
        if (query in username.lower() or
                query in user.get("tel", "").lower() or
                query in user.get("fullname", "").lower()):
            results.append(user)

    return results


def delete_user(username):
    users = read_json(FILENAME)
    initial_count = len(users)

    target_name = str(username).strip().lower()
    new_users = [
        u for u in users
        if str(u.get("username")).strip().lower() != target_name
    ]

    if len(new_users) < initial_count:
        write_json(FILENAME, new_users)
        print("[DEBUG] Kullanıcı silindi.")
        return True

    print("[DEBUG] Kullanıcı bulunamadı.")
    return False


def update_user_info(username, fullname, email, tel):
    users = read_json(FILENAME)
    updated = False

    for user in users:
        if user.get("username") == username:
            user["fullname"] = fullname
            user["email"] = email
            user["tel"] = tel
            updated = True
            break

    if updated:
        from database.db import write_json
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        write_json(FILENAME, users)
        return True
    return False


def update_public_key(username: str, public_key_pem: str) -> bool:
    """Kullanıcının genel RSA anahtarını JSON dosyasına kaydeder."""
    users = read_json(FILENAME)
    for user in users:
        if user.get("username") == username:
            user["public_key"] = public_key_pem
            write_json(FILENAME, users)
            return True
    return False


def get_public_key(username: str) -> str | None:
    """Kullanıcının genel RSA anahtarını JSON dosyasından okur."""
    user = find_user(username)
    if user:
        return user.get("public_key")
    return None


def get_privacy_settings(username: str) -> dict:
    """Kullanıcının gizlilik ayarlarını döndürür. Yoksa varsayılanı döndürür."""
    user = find_user(username)
    default_settings = {"online_status": True, "last_seen": True, "read_receipts": True}
    if user:
        return user.get("privacy_settings", default_settings)
    return default_settings


def update_privacy_settings(username: str, settings: dict) -> bool:
    """Kullanıcının gizlilik ayarlarını günceller."""
    users = get_all_users()
    for user in users:
        if user["username"] == username:
            if "privacy_settings" not in user:
                user["privacy_settings"] = {}
            user["privacy_settings"].update(settings)
            write_json(FILENAME, users)
            return True
    return False

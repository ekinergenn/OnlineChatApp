from database.db import read_json, write_json

FILENAME = "users.json"


def get_all_users() -> dict:
    return read_json(FILENAME)


def find_user(username: str) -> dict | None:
    users = get_all_users()
    return users.get(username)


def create_user(username: str, password: str, fullname: str, email: str) -> bool:
    users = get_all_users()
    if username in users:
        return False  # Kullanıcı zaten var

    users[username] = {
        "username": username,
        "password": password,  # ileride şifrelenecek
        "fullname": fullname,
        "email": email,
        "user_id": len(users) + 1
    }
    write_json(FILENAME, users)
    return True
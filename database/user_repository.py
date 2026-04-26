from database.db import read_json, write_json

FILENAME = "users.json"


def get_all_users() -> dict:
    return read_json(FILENAME)


def find_user(username: str) -> dict | None:
    users = get_all_users()
    return users.get(username)


def create_user(username: str, password: str, fullname: str, email: str, tel:str) -> bool:
    users = get_all_users()
    if username in users:
        return False  # Kullanıcı zaten var

    users[username] = {
        "username": username,
        "password": password,  # ileride şifrelenecek
        "fullname": fullname,
        "email": email,
         "tel": tel,
        "user_id": len(users) + 1
    }
    write_json(FILENAME, users)
    return True


def search_users(query: str, exclude_username: str = None) -> list:
    users = get_all_users()
    results = []
    query = query.lower().strip()

    for username, user in users.items():
        if exclude_username and username == exclude_username:
            continue
        if (query in username.lower() or
                query in user.get("tel", "").lower() or
                query in user.get("fullname", "").lower()):
            results.append(user)

    return results
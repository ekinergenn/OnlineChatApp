import os
from database.db import read_json, write_json

# Dosya yolunu projenin merkezi veri klasörüne göre ayarla
FILENAME = "blocks.json"


def get_all_blocks() -> list:
    """JSON dosyasındaki engelleme listesini güvenli bir şekilde döndürür."""
    data = read_json(FILENAME)

    # Eğer dosya boşsa veya format farklıysa [] döndür
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("blocks", [])

    return []


def check_block_status(blocker_id, blocked_id) -> str:
    """
    İki kullanıcı arasındaki engel durumunu kontrol eder.
    Dönen değerler: 'none', 'blocked_by_me', 'blocked_by_them', 'both'
    """
    blocks = get_all_blocks()
    my_id = str(blocker_id)
    target_id = str(blocked_id)

    blocked_by_me = False
    blocked_by_them = False

    for block in blocks:
        if block.get("isBlocked") is True:
            b_id = str(block.get("blocker_id"))
            bl_id = str(block.get("blocked_id"))

            if b_id == my_id and bl_id == target_id:
                blocked_by_me = True
            if b_id == target_id and bl_id == my_id:
                blocked_by_them = True

    if blocked_by_me and blocked_by_them:
        return "both"
    if blocked_by_me:
        return "blocked_by_me"
    if blocked_by_them:
        return "blocked_by_them"
    
    return "none"


def add_or_update_block(blocker_id, blocked_id, status: bool = True):
    #yeni engelleme yada var olanı guncelleme
    blocks = get_all_blocks()
    found = False

    for block in blocks:
        if str(block["blocker_id"]) == str(blocker_id) and \
                str(block["blocked_id"]) == str(blocked_id):
            block["isBlocked"] = status
            found = True
            break

    if not found:
        blocks.append({
            "blocker_id": str(blocker_id),
            "blocked_id": str(blocked_id),
            "isBlocked": status,
            "timestamp": __import__('time').time()
        })

    write_json(FILENAME, {"blocks": blocks})
    return True
import os
from database.db import read_json, write_json

FILENAME = "communities.json"

def get_all_communities() -> list:
    return read_json(FILENAME)

def create_community(name: str, creator: str) -> dict:
    communities = get_all_communities()
    
    new_community = {
        "community_id": len(communities) + 1,
        "name": name,
        "creator": creator,
        "members": [creator],
        "messages_file": f"community_{len(communities) + 1}.json"
    }
    
    communities.append(new_community)
    write_json(FILENAME, communities)
    return new_community

def join_community(community_id: int, username: str) -> bool:
    communities = get_all_communities()
    for comm in communities:
        if comm["community_id"] == community_id:
            if username not in comm["members"]:
                comm["members"].append(username)
                write_json(FILENAME, communities)
                return True
            return False
    return False

def search_communities(query: str) -> list:
    communities = get_all_communities()
    query = query.lower().strip()
    results = []
    for comm in communities:
        if query in comm["name"].lower():
            results.append(comm)
    return results

def get_user_communities(username: str) -> list:
    communities = get_all_communities()
    user_comms = []
    for comm in communities:
        if username in comm["members"]:
            user_comms.append(comm)
    return user_comms

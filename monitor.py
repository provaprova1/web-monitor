import requests
import hashlib
import os

URL = "https://eplay24.it/promozioni"

def get_content(url):
    r = requests.get(url, timeout=10)
    return r.text

def hash_content(content):
    return hashlib.md5(content.encode("utf-8")).hexdigest()

def load_old():
    if os.path.exists("state.txt"):
        return open("state.txt").read()
    return None

def save_new(h):
    with open("state.txt", "w") as f:
        f.write(h)

def main():
    content = get_content(URL)
    new_hash = hash_content(content)
    old_hash = load_old()

    if old_hash is None:
        save_new(new_hash)
        print("Prima esecuzione, stato salvato")
        return

    if new_hash != old_hash:
        print("CAMBIAMENTO RILEVATO")
        save_new(new_hash)
    else:
        print("Nessun cambiamento")

if __name__ == "__main__":
    main()
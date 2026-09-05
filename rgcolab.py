import sys
import os
import re
import time
import requests

DELAY_BETWEEN_FILES = 30   # seconds to wait between downloads (adjust as needed)
MAX_RETRIES = 3
RETRY_WAIT = 60            # seconds to wait before retrying a failed download

def login(email, password):
    resp = requests.post(
        "https://rapidgator.net/api/v2/user/login",
        data={"login": email, "password": password}
    )
    data = resp.json()
    if data.get("status") != 200:
        raise Exception(f"Login failed: {data.get('details', data)}")
    return data["response"]["token"]

def extract_file_id(link):
    match = re.search(r"rapidgator\.net/file/([a-zA-Z0-9]+)", link)
    if not match:
        raise Exception(f"Couldn't find a file ID in this link: {link}")
    return match.group(1)

def get_download_link(token, file_id):
    resp = requests.get(
        "https://rapidgator.net/api/v2/file/download",
        params={"token": token, "file_id": file_id}
    )
    data = resp.json()
    if data.get("status") != 200:
        raise Exception(data.get("details", str(data)))
    return data["response"]["download_url"]

def download_file(download_url, dest_folder):
    os.makedirs(dest_folder, exist_ok=True)
    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        cd = r.headers.get("content-disposition", "")
        match = re.search(r'filename="?([^"]+)"?', cd)
        filename = match.group(1) if match else "downloaded_file"
        dest_path = os.path.join(dest_folder, filename)

        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded * 100 // total
                        print(f"\r{filename}: {pct}%", end="")
        print()
    return dest_path

def download_one(token, link, dest_folder):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            file_id = extract_file_id(link)
            download_url = get_download_link(token, file_id)
            path = download_file(download_url, dest_folder)
            print(f"Saved: {path}")
            return True
        except Exception as e:
            print(f"Attempt {attempt} failed for {link}: {e}")
            if attempt < MAX_RETRIES:
                print(f"Waiting {RETRY_WAIT}s before retrying...")
                time.sleep(RETRY_WAIT)
    print(f"Giving up on {link} after {MAX_RETRIES} attempts.")
    return False

def main():
    if len(sys.argv) != 5:
        print("Usage: python rgcolab.py <email> <password> <links_file> <destination_folder>")
        sys.exit(1)

    email, password, links_file, dest_folder = sys.argv[1:5]

    with open(links_file) as f:
        links = [line.strip() for line in f if line.strip()]

    print(f"Found {len(links)} link(s) to download.")
    print("Logging in to Rapidgator...")
    token = login(email, password)

    for i, link in enumerate(links, start=1):
        print(f"\n[{i}/{len(links)}] {link}")
        download_one(token, link, dest_folder)
        if i < len(links):
            print(f"Waiting {DELAY_BETWEEN_FILES}s before the next file...")
            time.sleep(DELAY_BETWEEN_FILES)

    print("\nAll done!")

if __name__ == "__main__":
    main()

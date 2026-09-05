import sys
import os
import re
import requests

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
    # Rapidgator links look like: https://rapidgator.net/file/<file_id>/name.html
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
        raise Exception(f"Could not get download link: {data.get('details', data)}")
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
                        print(f"\rDownloading: {pct}%", end="")
        print()
    return dest_path

def main():
    if len(sys.argv) != 5:
        print("Usage: python rgcolab.py <email> <password> <rapidgator_link> <destination_folder>")
        sys.exit(1)

    email, password, link, dest_folder = sys.argv[1:5]

    print("Logging in to Rapidgator...")
    token = login(email, password)

    file_id = extract_file_id(link)

    print("Requesting download link...")
    download_url = get_download_link(token, file_id)

    print("Downloading...")
    path = download_file(download_url, dest_folder)
    print(f"Done! Saved to {path}")

if __name__ == "__main__":
    main()

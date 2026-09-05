import sys
import os
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

def get_file_info(token, url):
    resp = requests.get(
        "https://rapidgator.net/api/v2/file/info",
        params={"token": token, "url": url}
    )
    data = resp.json()
    if data.get("status") != 200:
        raise Exception(f"Could not get file info: {data.get('details', data)}")
    return data["response"]["file"]

def get_download_link(token, file_id):
    resp = requests.get(
        "https://rapidgator.net/api/v2/file/download",
        params={"token": token, "file_id": file_id}
    )
    data = resp.json()
    if data.get("status") != 200:
        raise Exception(f"Could not get download link: {data.get('details', data)}")
    return data["response"]["download_url"]

def download_file(download_url, dest_folder, filename):
    os.makedirs(dest_folder, exist_ok=True)
    dest_path = os.path.join(dest_folder, filename)
    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded * 100 // total
                        print(f"\rDownloading {filename}: {pct}%", end="")
        print()
    return dest_path

def main():
    if len(sys.argv) != 5:
        print("Usage: python rgcolab.py <email> <password> <rapidgator_link> <destination_folder>")
        sys.exit(1)

    email, password, link, dest_folder = sys.argv[1:5]

    print("Logging in to Rapidgator...")
    token = login(email, password)

    print("Fetching file info...")
    file_info = get_file_info(token, link)
    file_id = file_info["file_id"]
    filename = file_info["name"]

    print(f"Found file: {filename}")
    print("Requesting download link...")
    download_url = get_download_link(token, file_id)

    print("Downloading...")
    path = download_file(download_url, dest_folder, filename)
    print(f"Done! Saved to {path}")

if __name__ == "__main__":
    main()

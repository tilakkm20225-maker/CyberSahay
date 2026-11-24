from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "datasets" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

def download_uci():
    folder = RAW / "uci_sms_spam"
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / "sms_spam_collection.zip"
    url = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"
    print(f"Downloading UCI SMS Spam Collection to {archive}")
    urllib.request.urlretrieve(url, archive)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(folder)
    print("UCI dataset downloaded.")

def download_hf(repo_id, folder_name):
    from datasets import load_dataset
    target = RAW / folder_name
    print(f"Downloading {repo_id}")
    ds = load_dataset(repo_id)
    ds.save_to_disk(str(target))
    print(f"Saved to {target}")

if __name__ == "__main__":
    download_uci()
    download_hf("carnageiron/scam-ham-india", "indian_scam_ham")
    download_hf("Ridham115/indian-scam-sms-synthetic-audited", "indian_synthetic_audited")
    download_hf("harshcasper/bsis", "bsis_indian_synthetic")
    print("SMS downloads finished. Download URL datasets manually from datasets/README.md.")

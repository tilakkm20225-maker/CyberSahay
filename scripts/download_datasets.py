
from __future__ import annotations

import argparse
import json
import shutil
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from datasets import load_dataset

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "datasets" / "raw"

UCI_URL = (
    "https://archive.ics.uci.edu/static/public/228/"
    "sms+spam+collection.zip"
)

HF_SOURCES = {
    "scam-ham-india": {
        "repo_id": "carnageiron/scam-ham-india",
        "folder": "indian_scam_ham",
    }
}


def write_metadata(folder: Path, metadata: dict) -> None:
    metadata["downloaded_at_utc"] = (
        datetime.now(timezone.utc).isoformat()
    )

    metadata_path = folder / "metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def ensure_new_folder(folder: Path) -> None:
    if folder.exists() and any(folder.iterdir()):
        raise FileExistsError(
            f"Destination already contains files: {folder}\n"
            "Move or inspect the existing data before downloading again."
        )

    folder.mkdir(parents=True, exist_ok=True)


def download_uci() -> None:
    folder = RAW / "uci_sms_spam"
    ensure_new_folder(folder)

    archive = folder / "sms_spam_collection.zip"

    try:
        print("Downloading UCI SMS Spam Collection...")
        urllib.request.urlretrieve(UCI_URL, archive)

        with zipfile.ZipFile(archive) as zf:
            # Reject unsafe archive paths before extraction.
            destination = folder.resolve()

            for member in zf.infolist():
                target = (folder / member.filename).resolve()

                if not target.is_relative_to(destination):
                    raise ValueError(
                        f"Unsafe archive path detected: {member.filename}"
                    )

            zf.extractall(folder)

        write_metadata(folder, {
            "source_name": "UCI SMS Spam Collection",
            "source_type": "public research dataset",
            "source_url": (
                "https://archive.ics.uci.edu/dataset/228/"
                "sms+spam+collection"
            ),
            "download_url": UCI_URL,
            "format": "ZIP archive with extracted original files",
            "license_status": "Verify publisher terms before redistribution.",
            "synthetic_data": False,
            "notes": "Original files preserved; no message preprocessing performed.",
        })

        print(f"UCI dataset saved to: {folder}")

    except Exception:
        # Remove incomplete downloads, but only this newly created folder.
        shutil.rmtree(folder, ignore_errors=True)
        raise


def download_huggingface(source_name: str) -> None:
    source = HF_SOURCES[source_name]
    folder = RAW / source["folder"]
    ensure_new_folder(folder)

    try:
        print(f"Downloading Hugging Face dataset: {source['repo_id']}")

        dataset = load_dataset(source["repo_id"])
        dataset.save_to_disk(str(folder))

        write_metadata(folder, {
            "source_name": source_name,
            "source_type": "Hugging Face dataset",
            "repository": source["repo_id"],
            "format": "Hugging Face save_to_disk",
            "license_status": (
                "Not independently verified. Review the dataset card "
                "and license before research or redistribution."
            ),
            "synthetic_data": "Check dataset card and provenance.",
            "notes": "Original dataset splits preserved.",
        })

        print(f"Dataset saved to: {folder}")

    except Exception:
        shutil.rmtree(folder, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download CyberSahay research datasets individually."
    )

    parser.add_argument(
        "source",
        choices=["uci", "scam-ham-india", "all"],
        help="Dataset source to download.",
    )

    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)

    if args.source in ("uci", "all"):
        download_uci()

    if args.source in ("scam-ham-india", "all"):
        download_huggingface("scam-ham-india")

    print("\nDownload operation completed.")


if __name__ == "__main__":
    main()

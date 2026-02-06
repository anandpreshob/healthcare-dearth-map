"""Download public datasets for the Healthcare Dearth Map ETL pipeline.

Downloads to DATA_DIR/raw/:
  1. NPPES NPI Registry (~1GB zipped, ~8GB extracted)
  2. Census County Gazetteer (~138KB zipped)
  3. ZCTA-County Crosswalk (~1MB)
  4. Census ZCTA Gazetteer (~1MB zipped)
  5. Census County Population Estimates (~4MB)
"""

import os
import sys
import zipfile

import requests

from .config import RAW_DIR

# Download URLs
DOWNLOADS = {
    "nppes": {
        "url": "https://download.cms.gov/nppes/NPPES_Data_Dissemination_January_2025.zip",
        "filename": "nppes_full.zip",
        "description": "NPPES NPI Registry",
    },
    "county_gazetteer": {
        "url": "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_counties_national.zip",
        "filename": "2024_Gaz_counties_national.zip",
        "description": "Census County Gazetteer",
        "extract": True,
    },
    "zcta_county_crosswalk": {
        "url": "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt",
        "filename": "tab20_zcta520_county20_natl.txt",
        "description": "ZCTA-County Crosswalk",
    },
    "zcta_gazetteer": {
        "url": "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_zcta_national.zip",
        "filename": "2024_Gaz_zcta_national.zip",
        "description": "Census ZCTA Gazetteer",
        "extract": True,
    },
    "county_population": {
        "url": "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/counties/totals/co-est2024-alldata.csv",
        "filename": "co-est2024-alldata.csv",
        "description": "Census County Population Estimates",
    },
}


def _download_file(url: str, dest_path: str, description: str) -> None:
    """Download a file with progress display. Skip if already exists."""
    if os.path.exists(dest_path):
        size_mb = os.path.getsize(dest_path) / (1024 * 1024)
        print(f"  [SKIP] {description} already exists ({size_mb:.1f} MB)")
        return

    print(f"  Downloading {description}...")
    print(f"    URL: {url}")

    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    total = int(response.headers.get("content-length", 0))
    downloaded = 0
    chunk_size = 8192 * 16  # 128KB chunks

    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                pct = downloaded * 100 / total
                mb = downloaded / (1024 * 1024)
                total_mb = total / (1024 * 1024)
                sys.stdout.write(
                    f"\r    {mb:.1f} / {total_mb:.1f} MB ({pct:.1f}%)"
                )
                sys.stdout.flush()

    if total > 0:
        print()  # newline after progress
    size_mb = os.path.getsize(dest_path) / (1024 * 1024)
    print(f"    Done: {size_mb:.1f} MB")


def _extract_zip(zip_path: str, description: str) -> None:
    """Extract all files from a small zip archive."""
    extract_dir = os.path.dirname(zip_path)
    print(f"  Extracting {description}...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)
        for name in zf.namelist():
            print(f"    -> {name}")


def _extract_nppes(zip_path: str) -> None:
    """Extract the main NPPES CSV from the zip file."""
    extract_dir = os.path.dirname(zip_path)
    # Check if already extracted
    for f in os.listdir(extract_dir):
        if f.startswith("npidata_pfile") and f.endswith(".csv"):
            size_mb = os.path.getsize(os.path.join(extract_dir, f)) / (1024 * 1024)
            print(f"  [SKIP] NPPES CSV already extracted: {f} ({size_mb:.1f} MB)")
            return

    print("  Extracting NPPES zip (this may take a few minutes)...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        # Find the main data file (npidata_pfile_*.csv), skip header/readme
        csv_files = [
            n for n in zf.namelist()
            if n.startswith("npidata_pfile") and n.endswith(".csv")
        ]
        if not csv_files:
            # Fallback: find largest CSV
            csv_files = sorted(
                [n for n in zf.namelist() if n.endswith(".csv")],
                key=lambda n: zf.getinfo(n).file_size,
                reverse=True,
            )

        if csv_files:
            target = csv_files[0]
            print(f"    Extracting {target}...")
            zf.extract(target, extract_dir)
            print(f"    Extracted to {os.path.join(extract_dir, target)}")
        else:
            print("    WARNING: No CSV found in NPPES zip!")


def get_nppes_csv_path() -> str:
    """Find the extracted NPPES CSV file path."""
    for f in os.listdir(RAW_DIR):
        if f.startswith("npidata_pfile") and f.endswith(".csv"):
            return os.path.join(RAW_DIR, f)
    raise FileNotFoundError(
        f"NPPES CSV not found in {RAW_DIR}. Run download_data first."
    )


def get_county_gazetteer_path() -> str:
    """Find the county gazetteer txt file."""
    for f in os.listdir(RAW_DIR):
        if "gaz_counties_national" in f.lower() and f.endswith(".txt"):
            return os.path.join(RAW_DIR, f)
    raise FileNotFoundError(
        f"County gazetteer not found in {RAW_DIR}. Run download_data first."
    )


def get_zcta_gazetteer_path() -> str:
    """Find the ZCTA gazetteer txt file."""
    for f in os.listdir(RAW_DIR):
        if "gaz_zcta" in f.lower() and f.endswith(".txt"):
            return os.path.join(RAW_DIR, f)
    raise FileNotFoundError(
        f"ZCTA gazetteer not found in {RAW_DIR}. Run download_data first."
    )


def get_population_csv_path() -> str:
    """Find the population estimates CSV."""
    for f in os.listdir(RAW_DIR):
        if f.startswith("co-est") and f.endswith("-alldata.csv"):
            return os.path.join(RAW_DIR, f)
    raise FileNotFoundError(
        f"Population CSV not found in {RAW_DIR}. Run download_data first."
    )


def run():
    """Download all datasets."""
    print("=== Downloading Public Data ===")

    os.makedirs(RAW_DIR, exist_ok=True)
    print(f"  Data directory: {RAW_DIR}")

    for key, info in DOWNLOADS.items():
        dest = os.path.join(RAW_DIR, info["filename"])
        _download_file(info["url"], dest, info["description"])

        # Extract small census zip files
        if info.get("extract") and os.path.exists(dest):
            _extract_zip(dest, info["description"])

    # Extract NPPES zip
    nppes_zip = os.path.join(RAW_DIR, DOWNLOADS["nppes"]["filename"])
    if os.path.exists(nppes_zip):
        _extract_nppes(nppes_zip)

    print("=== Downloads Complete ===")


if __name__ == "__main__":
    run()

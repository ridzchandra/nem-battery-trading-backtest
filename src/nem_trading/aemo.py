from __future__ import annotations

import csv
import io
import re
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

CURRENT_PRICES_URL = "https://www.nemweb.com.au/Reports/CURRENT/Public_Prices/"
ARCHIVE_PRICES_URL = "https://www.nemweb.com.au/Reports/ARCHIVE/Public_Prices/"
REQUIRED_COLUMNS = {"SETTLEMENTDATE", "REGIONID", "RRP", "TOTALDEMAND"}


def list_price_files(url: str = CURRENT_PRICES_URL) -> list[str]:
    """Return PUBLIC_PRICES zip links listed on a NEMWeb directory page."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if re.search(r"PUBLIC_PRICES_.*\.zip$", href, flags=re.IGNORECASE):
            links.append(urljoin(url, href))
    return sorted(set(links))


def download_file(url: str, destination: Path) -> Path:
    """Download one zip file unless it already exists locally."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return destination
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    destination.write_bytes(response.content)
    return destination


def download_recent_daily_files(days: int, destination_dir: Path) -> list[Path]:
    """Download the most recent daily PUBLIC_PRICES files exposed by NEMWeb."""
    if days < 1:
        raise ValueError("days must be at least 1")
    urls = list_price_files(CURRENT_PRICES_URL)[-days:]
    if not urls:
        raise RuntimeError("No PUBLIC_PRICES files were found on NEMWeb")
    return [download_file(url, destination_dir / url.rsplit("/", 1)[-1]) for url in urls]


def download_archive_month(month: str, destination_dir: Path) -> Path:
    """Download one monthly archive, where month is YYYY-MM."""
    timestamp = pd.Timestamp(f"{month}-01")
    filename = f"PUBLIC_PRICES_{timestamp:%Y%m}01.zip"
    url = urljoin(ARCHIVE_PRICES_URL, filename)
    try:
        return download_file(url, destination_dir / filename)
    except requests.HTTPError as exc:
        raise RuntimeError(
            f"Archive {filename} is not available. NEMWeb monthly archives can lag; "
            "use recent daily files for the current period."
        ) from exc


def _rows_from_zip(zip_path: Path):
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if not name.lower().endswith(".csv"):
                continue
            with archive.open(name) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace")
                yield from csv.reader(text)


def parse_public_prices_zip(zip_path: Path, region: str = "NSW1") -> pd.DataFrame:
    """Parse DREGION rows from one AEMO PUBLIC_PRICES zip file."""
    header_positions: dict[str, int] | None = None
    table_version: str | None = None
    records: list[dict[str, str]] = []

    for row in _rows_from_zip(zip_path):
        if len(row) < 5 or row[1] != "DREGION":
            continue
        if row[0] == "I":
            candidate = {name: index for index, name in enumerate(row) if name}
            if REQUIRED_COLUMNS.issubset(candidate):
                header_positions = candidate
                table_version = row[3]
            continue
        if row[0] != "D" or header_positions is None:
            continue
        if table_version is not None and row[3] != table_version:
            continue
        if len(row) <= max(header_positions.values()):
            continue
        if row[header_positions["REGIONID"]] != region:
            continue
        record = {
            name: row[index]
            for name, index in header_positions.items()
            if name in {"SETTLEMENTDATE", "REGIONID", "RRP", "TOTALDEMAND", "NETINTERCHANGE"}
        }
        records.append(record)

    if not records:
        raise ValueError(f"No DREGION rows for {region} found in {zip_path.name}")

    frame = pd.DataFrame.from_records(records)
    frame["SETTLEMENTDATE"] = pd.to_datetime(frame["SETTLEMENTDATE"], errors="coerce")
    for column in ["RRP", "TOTALDEMAND", "NETINTERCHANGE"]:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["SETTLEMENTDATE", "RRP", "TOTALDEMAND"])
    frame = frame.sort_values("SETTLEMENTDATE").drop_duplicates("SETTLEMENTDATE")
    return frame.reset_index(drop=True)


def load_price_files(paths: list[Path], region: str = "NSW1") -> pd.DataFrame:
    """Parse and concatenate multiple PUBLIC_PRICES files."""
    frames = [parse_public_prices_zip(path, region=region) for path in paths]
    result = pd.concat(frames, ignore_index=True)
    result = result.sort_values("SETTLEMENTDATE").drop_duplicates("SETTLEMENTDATE")
    return result.reset_index(drop=True)

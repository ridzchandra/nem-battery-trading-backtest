from __future__ import annotations

import argparse
from pathlib import Path

from nem_trading.aemo import download_archive_month, download_recent_daily_files, load_price_files


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and parse public AEMO NEM price data.")
    parser.add_argument("--region", default="NSW1")
    parser.add_argument("--months", nargs="*", default=[] , help="Archive months in YYYY-MM format")
    parser.add_argument("--recent-days", type=int, default=0, help="Also download recent daily files")
    args = parser.parse_args()

    raw_dir = Path("data/raw")
    paths = [download_archive_month(month, raw_dir) for month in args.months]
    if args.recent_days:
        paths.extend(download_recent_daily_files(args.recent_days, raw_dir))
    if not paths:
        raise SystemExit("Pass --months YYYY-MM ... or --recent-days N")

    frame = load_price_files(paths, region=args.region)
    output = Path("data/processed") / f"{args.region.lower()}_prices.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    print(f"Wrote {len(frame):,} rows to {output}")


if __name__ == "__main__":
    main()

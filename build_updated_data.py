#!/usr/bin/env python3
"""
Merge all injury_list_*.txt (+ optional injury_list.txt) into injury_data.csv,
then cleanse, standardize, and dedupe into updated_data.csv for the Dash app.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    os.chdir(ROOT)
    sys.path.insert(0, ROOT)

    from DataOrganizer import discover_injury_list_files, parse_multiple_injury_lists
    from helpers.helpers import parse_injury_data_first_occurrence
    from paths import DATA_DIR, data_path

    files = discover_injury_list_files(DATA_DIR)
    if not files:
        print("No injury_list_*.txt or injury_list.txt found under", DATA_DIR)
        return 1

    injury_csv = data_path("injury_data.csv")
    updated_csv = data_path("updated_data.csv")

    print(f"Merging {len(files)} file(s) -> {injury_csv}")
    for f in files:
        print(f"  - {os.path.basename(f)}")
    parse_multiple_injury_lists(files, injury_csv)

    print(f"Cleansing and deduplicating -> {updated_csv}")
    parse_injury_data_first_occurrence(injury_csv, updated_csv)
    print("Done. Start the app with: python main.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())

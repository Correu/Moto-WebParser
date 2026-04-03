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

    files = discover_injury_list_files(ROOT)
    if not files:
        print("No injury_list_*.txt or injury_list.txt found under", ROOT)
        return 1

    print(f"Merging {len(files)} file(s) -> injury_data.csv")
    for f in files:
        print(f"  - {os.path.basename(f)}")
    parse_multiple_injury_lists(files, "injury_data.csv")

    print("Cleansing and deduplicating -> updated_data.csv")
    parse_injury_data_first_occurrence("injury_data.csv", "updated_data.csv")
    print("Done. Start the app with: python3 main.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())

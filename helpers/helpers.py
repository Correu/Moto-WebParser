import pkg_resources
import csv
import re
from datetime import datetime

from paths import data_path

# Canonical sport codes used across scrapers / UI
_CANONICAL_SPORTS = frozenset({"motocross", "off_road", "bmx", "skate", "fmx"})

# Medical / common acronyms to preserve when title-casing injury text
_INJURY_ACRONYMS = {"ACL", "MCL", "PCL", "LCL", "TBI", "MRI", "CT", "AC"}


def _collapse_whitespace(text):
    return re.sub(r"\s+", " ", (text or "").strip())


def _canonical_sport(value):
    s = (value or "").strip().lower().replace(" ", "_").replace("-", "_")
    if not s:
        return "motocross"
    if s in _CANONICAL_SPORTS:
        return s
    if "off" in s and "road" in s:
        return "off_road"
    if "bmx" in s:
        return "bmx"
    if "skate" in s:
        return "skate"
    if "fmx" in s or "freestyle" in s:
        return "fmx"
    if "moto" in s:
        return "motocross"
    return s


def _norm_key_part(text):
    return _collapse_whitespace(text).casefold()


def _title_case_preserve_acronyms(text):
    """Title-case a phrase but keep known all-caps medical acronyms."""
    t = _collapse_whitespace(text)
    if not t:
        return t
    words = t.split()
    out = []
    for w in words:
        upper = w.upper()
        if upper in _INJURY_ACRONYMS:
            out.append(upper)
        else:
            out.append(w[:1].upper() + w[1:].lower() if w else w)
    return " ".join(out)


def _standardize_discipline(value):
    d = _collapse_whitespace(value)
    if not d:
        return ""
    parts = re.split(r"[/|,]+", d)
    parts = [_collapse_whitespace(p) for p in parts if p.strip()]
    if not parts:
        return ""
    return "/".join(p.title() for p in parts)


def _standardize_venue(value):
    v = _collapse_whitespace(value)
    if not v:
        return ""
    if v.lower() in ("unknown track", "unknown venue"):
        return "Unknown Track"
    return v.title()


def _standardize_athlete(value):
    a = _collapse_whitespace(value)
    if not a or a.lower() == "unknown athlete":
        return "Unknown athlete"
    return a.title()


def _standardize_injury_display(value):
    inj = _collapse_whitespace(value)
    if not inj:
        return ""
    if inj.isupper() and len(inj) <= 48:
        return _title_case_preserve_acronyms(inj.lower())
    return inj


def _parse_date_sort_key(date_str):
    try:
        return datetime.strptime((date_str or "").strip(), "%Y-%m-%d")
    except ValueError:
        return datetime.max


def _format_date_iso(date_str):
    try:
        return datetime.strptime((date_str or "").strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return ""


def standardize_injury_row(row):
    """
    Normalize one CSV row dict to canonical columns for display and dedupe keys.
    Handles legacy 4-column files (Rider, Injury, Track, Date).
    """
    athlete = _standardize_athlete(row.get("Athlete") or row.get("Rider") or "")
    injury = _standardize_injury_display(row.get("Injury") or "")
    venue = _standardize_venue(row.get("Venue") or row.get("Track") or "")
    sport = _canonical_sport(row.get("Sport"))
    discipline = _standardize_discipline(row.get("Discipline") or "")
    date_raw = (row.get("Date") or "").strip()
    date_iso = _format_date_iso(date_raw) if date_raw else ""

    return {
        "Sport": sport,
        "Discipline": discipline,
        "Athlete": athlete,
        "Rider": athlete,
        "Injury": injury,
        "Venue": venue,
        "Track": venue,
        "Date": date_iso,
    }


def dedupe_key_for_row(std_row):
    """Normalized key for duplicate detection (case/whitespace insensitive)."""
    return (
        std_row["Sport"],
        _norm_key_part(std_row["Athlete"]),
        _norm_key_part(std_row["Injury"]),
        _norm_key_part(std_row["Venue"]),
    )

def generate_requirements_txt_with_pkg_resources(output_file="requirements.txt"):
    """
    Generates a requirements.txt file using pkg_resources.
    """
    requirements = []
    for dist in pkg_resources.working_set:
        requirements.append(str(dist.as_requirement()))

    try:
        with open(output_file, "w") as f:
            for req in requirements:
                f.write(req + "\n")
        print(f"Successfully generated {output_file}")
    except IOError as e:
        print(f"Error writing to file: {e}")


def parse_injury_data_first_occurrence(input_file=None, output_file=None):
    """
    Cleanse, standardize, and dedupe injury rows, then write updated_data.csv.

    - Standardizes Sport, Discipline, Athlete/Rider, Injury, Venue/Track, Date.
    - Deduplicates using normalized keys (case-insensitive, whitespace collapsed)
      so e.g. KNEE vs Knee maps to one row.
    - Keeps the earliest valid Date per dedupe key when sorting chronologically.
    Rows with empty Date sort last and can still be kept if the key is new.

    Args:
        input_file (str): Path to the input CSV file (default: data/injury_data.csv)
        output_file (str): Path to the output CSV file (default: data/updated_data.csv)
    """
    if input_file is None:
        input_file = data_path("injury_data.csv")
    if output_file is None:
        output_file = data_path("updated_data.csv")

    fieldnames = ['Sport', 'Discipline', 'Athlete', 'Rider', 'Injury', 'Venue', 'Track', 'Date']

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        standardized = [standardize_injury_row(r) for r in rows]
        standardized.sort(key=lambda r: _parse_date_sort_key(r["Date"]))

        seen_keys = set()
        first_occurrences = []
        for std in standardized:
            key = dedupe_key_for_row(std)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            first_occurrences.append(std)

        if first_occurrences:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in first_occurrences:
                    writer.writerow(row)

            print(f"Successfully processed {len(first_occurrences)} deduped rows from {len(rows)} total entries")
            print(f"Output saved to {output_file}")
        else:
            print("No data to write.")

    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
    except Exception as e:
        print(f"Error processing file: {e}")


# Example usage:
if __name__ == "__main__":
    generate_requirements_txt_with_pkg_resources()
    #parse_injury_data_first_occurrence()
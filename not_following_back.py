from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

# Everything is anchored to where this script lives, not the current working
# directory
# It behaves the same whether you click Run in PyCharm or
# invoke it from a terminal in some other folder.
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "output"

# Instagram leaves placeholder entries for accounts that were deleted or
# deativated
# Their handle starts with this prefix. They aren't real people
# you can interact with, so they're skipped.
_DELETED_PREFIX = "__deleted__"

def _username_from_record(record: dict) -> str | None:
    """Extracts one username from a single Instagram record.
    This checks `title` first, then `value`, then falls back to pulling the
    final path segment out of `href` -- so it works for both shapes. Deleted
    or deactivated placeholder accounts are skipped.
    """
    name = None

    title = record.get("title")
    if isinstance(title, str) and title.strip():
        name = title.strip().lower()
    else:
        for item in record.get("string_list_data", []):
            if not isinstance(item, dict):
                continue
            value = item.get("value")
            if isinstance(value, str) and value.strip():
                name = value.strip().lower()
                break
            href = item.get("href")
            if isinstance(href, str) and href.strip():
                slug = href.rstrip("/").split("/")[-1]
                if slug:
                    name = slug.strip().lower()
                    break

    if name and name.startswith(_DELETED_PREFIX):
        return None
    return name

def _extract_usernames(data) -> set[str]:
    """Pulls every username out of one parsed Instagram JSON object."""
    usernames: set[str] = set()

    def walk(obj) -> None:
        if isinstance(obj, dict):
            if isinstance(obj.get("string_list_data"), list):
                name = _username_from_record(obj)
                if name:
                    usernames.add(name)
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    return usernames

def _describe_shape(data) -> str:
    """Short description of a file's top-level structure, for the warning."""
    if isinstance(data, dict):
        return "object with keys: " + ", ".join(data.keys())
    if isinstance(data, list):
        return f"list with {len(data)} items"
    return type(data).__name__

def load_usernames(*paths: Path) -> set[str]:
    """Loads and merges usernames from one or more JSON files."""
    usernames: set[str] = set()
    for path in paths:
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            sys.exit(
                f"Error: {path} is not valid JSON ({e}).\n"
                "Did you request the export in JSON format (not HTML)?"
            )
        found = _extract_usernames(data)
        if not found:
            print(
                f"Warning: found no usernames in {path.name} "
                f"({_describe_shape(data)}).",
                file=sys.stderr,
            )
        usernames |= found
    return usernames

def find_export_files(folder: Path):
    """Locates the following + followers JSON files inside an export folder."""
    following = sorted(folder.rglob("following.json"))
    followers = sorted(folder.rglob("followers_*.json"))
    followers += sorted(folder.rglob("followers.json"))  # some exports use this
    return following, sorted(set(followers))

def write_csv(path: Path, usernames: list[str]) -> None:
    """Writes a numbered CSV with columns: #, Handle, Profile URL.

    newline="" is required so the CSV doesn't get blank rows between
    entries on Windows.
    """
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["#", "Handle", "Profile URL"])
        for i, name in enumerate(usernames, start=1):
            writer.writerow([i, name, f"https://www.instagram.com/{name}"])

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find people you follow on Instagram who don't follow you back."
    )
    parser.add_argument(
        "folder", nargs="?", default=None,
        help="Path to your Instagram export folder "
             "(default: search this script's own folder).",
    )
    parser.add_argument(
        "-o", "--output", default="not_following_back.csv",
        help="Output CSV filename (default: not_following_back.csv). "
             "It is always written into the `output` folder.",
    )
    parser.add_argument(
        "--show-fans", action="store_true",
        help="Also write a CSV of people who follow you that you don't follow back.",
    )
    args = parser.parse_args()

    # If no folder given -> search the folder this script lives in.
    folder = Path(args.folder).expanduser() if args.folder else SCRIPT_DIR
    if not folder.exists():
        sys.exit(f"Error: folder not found: {folder}")

    following_files, follower_files = find_export_files(folder)
    if not following_files or not follower_files:
        sys.exit(
            "Error: couldn't find your Instagram export files under:\n"
            f"  {folder.resolve()}\n\n"
            "Make sure you've unzipped the export and that this folder "
            "contains `following.json` and `followers_1.json` somewhere inside "
            "it.\nEasiest fix: drop the unzipped export folder into the same "
            "folder as this script and run again."
        )

    following = load_usernames(*following_files)
    followers = load_usernames(*follower_files)

    not_following_back = sorted(following - followers)
    fans = sorted(followers - following)

    # --- Console summary ------------------------------------------------
    print("Read following from: " + ", ".join(str(p) for p in following_files))
    print("Read followers from: " + ", ".join(str(p) for p in follower_files))
    print()
    print(f"You follow:        {len(following)}")
    print(f"Followers:         {len(followers)}")
    print(f"Don't follow back: {len(not_following_back)}")
    print()

    # --- Making sure the output folder exists -----------------------------
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Writing the main CSV (always into the output folder) -------------
    out_name = Path(args.output).name  # ignore any folders in -o, keep the name
    out_path = OUTPUT_DIR / out_name
    write_csv(out_path, not_following_back)
    print(f"Saved {len(not_following_back)} accounts you follow who don't follow "
          f"you back to:\n  {out_path}")

    # --- writing the fans CSV (lol)  ----------------------------------
    if args.show_fans:
        fans_name = Path(out_name).stem + "_fans" + (Path(out_name).suffix or ".csv")
        fans_path = OUTPUT_DIR / fans_name
        write_csv(fans_path, fans)
        print(f"\nSaved {len(fans)} people who follow you that you don't follow "
              f"back to:\n  {fans_path}")

    print("\nOpen the CSV in Excel or Google Sheets.")

if __name__ == "__main__":
    main()
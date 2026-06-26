# Follower-Following Ratio Manager

Find the Instagram accounts you follow that **don't follow you back** — using your own data export, with no login, no password, and no API. Results are written to CSV files (in an `output` folder) that you can open in Excel or Google Sheets.

## Why this exists

If your following count dwarfs your follower count, the first step to fixing the ratio is knowing *who* you follow that doesn't follow back. Instagram's official API deliberately won't give you your follower/following lists, and unofficial scraping tools require your password and can get your account flagged.

This tool sidesteps all of that. It reads the data export that **Instagram gives you about yourself** and does the comparison locally on your machine. Nothing ever logs into your account.

## How it works

The whole thing rests on one idea: set subtraction.

- `following` = the set of accounts you follow
- `followers` = the set of accounts that follow you
- **People who don't follow you back** = `following − followers`

The rest of the code handles the quirks of Instagram's export format:

- The two files are stored differently. In `following.json` the username sits in each record's `title` field; in `followers_*.json` it sits in `string_list_data[].value`. The script reads whichever is present.
- Usernames are normalized to lowercase so capitalization differences don't cause false mismatches.
- Accounts split across multiple `followers_1.json`, `followers_2.json`, … files are merged automatically.
- Placeholder entries for deleted/deactivated accounts (handles beginning with `__deleted__`) are skipped, since they aren't real accounts you can interact with.
- The script anchors itself to its own folder, so it finds your export and writes its output to the same predictable place no matter which directory you run it from.

## Requirements

- Python 3.7 or newer
- **No third-party packages** — it uses only the Python standard library.

## Getting your Instagram data

1. In Instagram: **Settings → Accounts Center → "Your information and permissions" → "Download your information."**
2. Request a download of **Followers and following**.
3. **Choose JSON as the format** (not HTML — the script needs JSON).
4. When it's ready, download the `.zip` from the **Download requests** area (Instagram also emails you a link).
5. **Unzip it** and place the unzipped export folder anywhere inside this project. Inside it you'll find `following.json` and one or more `followers_1.json` files, usually under `connections/followers_and_following/`.

## Usage

Simplest: just run it with no arguments — it searches its own folder for the export automatically and writes `output/not_following_back.csv`:

```bash
python not_following_back.py
```

Or point it explicitly at your export folder:

```bash
python not_following_back.py path/to/your/export/folder
```

### Options

| Flag | What it does |
| --- | --- |
| `-o my_name.csv` | Choose the output filename (default: `not_following_back.csv`) |
| `--show-fans` | Also write a second CSV of people who follow you that you don't follow back (named like `not_following_back_fans.csv`) |

Example with both:

```bash
python not_following_back.py my_export --show-fans -o results.csv
```

### Running in PyCharm (no terminal needed)

Click the green **Run** button to run the script with no flags — it writes `output/not_following_back.csv`. To use a flag like `--show-fans`, add it once under **Run → Edit Configurations → Script parameters**, then use the Run button as normal; it will include the flag every time. Clear that field to go back to a plain run. (Run configurations are personal IDE settings stored under `.idea/`, which is gitignored, so they aren't part of the repo.)

## Output

All CSVs are written into an `output/` folder next to the script. Each CSV has three columns:

| # | Handle | Profile URL |
| --- | --- | --- |
| 1 | example_one | https://www.instagram.com/example_one |
| 2 | example_two | https://www.instagram.com/example_two |

The console also prints a short summary:

```
You follow:        1022
Followers:         645
Don't follow back: 452

Saved 452 accounts you follow who don't follow you back to:
  .../output/not_following_back.csv
```

## A note on the counts

The numbers here may not exactly match what the Instagram app shows you, and that's expected:

- **Following often reads higher in the export than in the app.** The export is a snapshot that still lists accounts which were later deactivated, deleted, or banned. The app drops those from its live count. (This script removes only the entries Instagram explicitly tags as `__deleted__`; deactivated/banned accounts can't be reliably detected and may remain.)
- **Follower counts can drift by a few.** The export reflects the moment it was generated, so a handful of follows/unfollows since then will cause small differences.

## Privacy & safety

- **No credentials anywhere.** The script never logs in and has no place to put a username or password. The only password step happens inside Instagram itself when *you* download your export — the script never sees it.
- **Your data stays local.** The script only reads files already on your computer.
- **Keep your export and output out of the repo.** The export and the generated CSVs contain real usernames — your personal data. Make sure your `.gitignore` ignores both the export files and the `output/` folder, and double-check before committing.

## A note on unfollowing

If you act on the list, **space the unfollowing out** rather than doing it all in one burst. Rapid mass-unfollowing is exactly the behavior Instagram's automated systems flag. It's also worth skimming the list first — clubs, teams, public figures, and accounts you intentionally follow will appear there too, regardless of whether they follow you back.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

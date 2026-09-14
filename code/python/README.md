# code/python

The core algorithm: turn a scanned page into a 1D profile, then compare
profiles to decide if it matches an enrolled key.

- `main.py` — **start here.** Loads the keys, tests a page, prints
  match/no-match.
- `filters.py` — image → 1D profile (background removal, line
  isolation, resampling).
- `peaks.py` — peak detection and tolerant peak-set matching.
- `keys.py` — loads `data/templates/key/config.json` and builds a
  `Key` (with its profiles) for each entry.
- `classify.py` — compares one image against a list of keys.
- `settings.py` — tunable constants, loaded from `data/settings.json`.
- `API/api.py` — a single, standalone file (`add_key` / `remove_key` /
  `classify`) for handing this off to another system.

## Run it

```bash
pip install -r requirements.txt
python main.py
```

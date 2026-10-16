# Chrome Version Browser

Console app that browses live Chrome for Testing versions (milestone 115+), lets you pick a
version, choose Chrome or ChromeDriver, pick a platform, and get the direct download URL.

## Run from source

Requires Python 3.x.

```
python main.py
```

Each online fetch writes a copy of the raw JSON response to `app_data\data.json` in this folder.

## Online / offline mode

`app.properties` in this folder controls where the data comes from:

```
mode=online
```

- `mode=online` (default) — fetches the latest data from the live URL and refreshes the cache.
- `mode=offline` — skips the network call and reads `app_data\data.json` instead. Run once in
  online mode first so a cache exists, or offline mode will show an error.

## Build a standalone .exe

```
build.bat
```

This installs PyInstaller (from `requirements.txt`), builds a single-file console exe, and
assembles a ready-to-distribute folder at `dist\chrome_version_browser\` containing:

- `run.exe`
- `app_data\` (the data cache, copied from this folder if present)
- `app.properties`
- `README.md`

That folder is self-contained — copy it anywhere and run `run.exe`. `dist\run.exe` (the raw
PyInstaller output), `build\`, and `run.spec` are intermediate build artifacts, safe to
delete/regenerate.

## Errors and exit codes

Invalid menu input (wrong choice, non-numeric search entry, no matching version) never exits
the app — it prints `ERROR: <message>` to **stderr** and redisplays the same screen.

The process exit code is only decided when the app actually ends:

| Exit code | Meaning |
|-----------|---------|
| `0` | Normal quit (`Q`) |
| `1` | Fetch/data error (network failure, malformed JSON, missing offline cache) or unexpected end of input (EOF) |
| `130` | Interrupted with `Ctrl+C` |

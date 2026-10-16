import json
import os
import sys
import urllib.error
import urllib.request

DATA_URL = "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json"
MIN_MILESTONE = 115
PAGE_SIZE = 10
BORDER = "=" * 40
TYPE_LABELS = {"chrome": "Chrome", "chromedriver": "ChromeDriver"}
PROPERTIES_FILENAME = "app.properties"
CACHE_PATH = os.path.join("app_data", "data.json")


def clear_screen():
    os.system("cls")


def show_error(message):
    print(f"ERROR: {message}", file=sys.stderr)
    print("Press Enter to continue...", end="", file=sys.stderr, flush=True)
    input()


def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def save_raw_data(raw_bytes):
    cache_path = os.path.join(get_base_dir(), CACHE_PATH)
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "wb") as f:
            f.write(raw_bytes)
    except OSError:
        pass


def load_cached_data():
    try:
        with open(os.path.join(get_base_dir(), CACHE_PATH), "rb") as f:
            return f.read()
    except OSError:
        return None


def load_mode():
    path = os.path.join(get_base_dir(), PROPERTIES_FILENAME)
    properties = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                properties[key.strip().lower()] = value.strip().lower()
    except OSError:
        pass
    return properties.get("mode", "online")


def version_key(version):
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        return (0,)


def fetch_versions():
    offline = load_mode() == "offline"

    if offline:
        print("Offline mode - loading cached Chrome versions...")
        raw = load_cached_data()
        if raw is None:
            show_error(
                f"Offline mode is enabled but no cached data was found at {CACHE_PATH}. "
                "Run once with mode=online in app.properties to create a cache."
            )
            sys.exit(1)
    else:
        print("Fetching latest Chrome versions...")
        try:
            with urllib.request.urlopen(DATA_URL, timeout=15) as response:
                raw = response.read()
        except (urllib.error.URLError, OSError):
            show_error("Unable to fetch Chrome version data. Check your internet connection and try again.")
            sys.exit(1)
        save_raw_data(raw)

    try:
        data = json.loads(raw)
        milestones = data["milestones"]
    except (json.JSONDecodeError, KeyError, TypeError):
        source = "cache file" if offline else "server"
        show_error(f"Received unexpected data from the {source}.")
        sys.exit(1)

    records = []
    for entry in milestones.values():
        milestone_raw = entry.get("milestone")
        version = entry.get("version")
        if milestone_raw is None or version is None:
            continue
        try:
            milestone = int(milestone_raw)
        except (TypeError, ValueError):
            continue
        if milestone < MIN_MILESTONE:
            continue

        downloads = entry.get("downloads") or {}
        chrome_map = {
            d["platform"]: d["url"]
            for d in downloads.get("chrome") or []
            if "platform" in d and "url" in d
        }
        if not chrome_map:
            continue

        record = {"version": version, "downloads": {"chrome": chrome_map}}
        chromedriver_map = {
            d["platform"]: d["url"]
            for d in downloads.get("chromedriver") or []
            if "platform" in d and "url" in d
        }
        if chromedriver_map:
            record["downloads"]["chromedriver"] = chromedriver_map
        records.append(record)

    records.sort(key=lambda r: version_key(r["version"]), reverse=True)
    return records


def find_by_milestone(records, milestone):
    for rec in records:
        if int(rec["version"].split(".")[0]) == milestone:
            return rec
    return None


def total_pages(count):
    return max(1, -(-count // PAGE_SIZE))


def show_welcome():
    clear_screen()
    print(BORDER)
    print(" Chrome Version Browser")
    print(BORDER)
    print(" This app lists available Chrome for Testing")
    print(" versions (milestone 115+). Pick a version,")
    print(" choose Chrome or ChromeDriver, pick your")
    print(" platform, and get the direct download link.")
    print(BORDER)
    return input(" Press Enter to start (or Q to quit): ").strip().lower()


def show_list_screen(records, page):
    clear_screen()
    count = len(records)
    pages = total_pages(count)
    start = (page - 1) * PAGE_SIZE
    page_records = records[start:start + PAGE_SIZE]

    print(BORDER)
    print(" Chrome for Testing - Available Versions")
    print(f" Page {page} of {pages}  ({count} versions total)")
    print(BORDER)
    for i, rec in enumerate(page_records, start=1):
        print(f"  {i}. {rec['version']}")
    print(BORDER)
    if page < pages:
        print("  N. Next Page")
    if page > 1:
        print("  P. Previous Page")
    print("  S. Search by major version")
    print("  Q. Quit")
    print(BORDER)
    choice = input("Select an option: ").strip().lower()
    return choice, page_records, pages


def show_type_screen(rec):
    clear_screen()
    options = [t for t in ("chrome", "chromedriver") if t in rec["downloads"]]

    print(BORDER)
    print(f" Chrome {rec['version']} - Select Type")
    print(BORDER)
    for i, t in enumerate(options, start=1):
        print(f"  {i}. {TYPE_LABELS[t]}")
    print(BORDER)
    print("  B. Back")
    print("  M. Main Menu")
    print("  Q. Quit")
    print(BORDER)
    choice = input("Select an option: ").strip().lower()
    return choice, options


def show_platform_screen(rec, type_key):
    clear_screen()
    platforms = sorted(rec["downloads"][type_key].keys())

    print(BORDER)
    print(f" Chrome {rec['version']} - {TYPE_LABELS[type_key]} - Select Platform")
    print(BORDER)
    for i, p in enumerate(platforms, start=1):
        print(f"  {i}. {p}")
    print(BORDER)
    print("  B. Back")
    print("  M. Main Menu")
    print("  Q. Quit")
    print(BORDER)
    choice = input("Select an option: ").strip().lower()
    return choice, platforms


def show_result_screen(rec, type_key, platform):
    clear_screen()
    url = rec["downloads"][type_key][platform]

    print(BORDER)
    print(f" Chrome {rec['version']} - {TYPE_LABELS[type_key]} - {platform}")
    print(BORDER)
    print("  Download URL:")
    print(f"  {url}")
    print(BORDER)
    print("  B. Back")
    print("  M. Main Menu")
    print("  Q. Quit")
    print(BORDER)
    return input("Select an option: ").strip().lower()


def run():
    choice = show_welcome()
    if choice == "q":
        clear_screen()
        print("Goodbye!")
        return

    print()
    records = fetch_versions()

    stack = [("LIST", {"page": 1})]

    while stack:
        state, ctx = stack[-1]

        if state == "LIST":
            page = ctx["page"]
            choice, page_records, pages = show_list_screen(records, page)

            if choice == "q":
                break
            elif choice == "n" and page < pages:
                stack[-1] = ("LIST", {"page": page + 1})
            elif choice == "p" and page > 1:
                stack[-1] = ("LIST", {"page": page - 1})
            elif choice == "s":
                raw = input("Enter major version (e.g. 131): ").strip()
                if not raw.isdigit():
                    show_error(f"'{raw}' is not a valid major version number.")
                else:
                    match = find_by_milestone(records, int(raw))
                    if match is None:
                        show_error(f"No Chrome version found for milestone {raw}.")
                    else:
                        stack.append(("TYPE", {"page": page, "version": match}))
            elif choice.isdigit() and 1 <= int(choice) <= len(page_records):
                rec = page_records[int(choice) - 1]
                stack.append(("TYPE", {"page": page, "version": rec}))
            else:
                show_error(f"'{choice}' is not a valid option. Please choose from the list above.")

        elif state == "TYPE":
            rec = ctx["version"]
            choice, options = show_type_screen(rec)

            if choice == "q":
                break
            elif choice == "b":
                stack.pop()
            elif choice == "m":
                stack[:] = [("LIST", {"page": 1})]
            elif choice.isdigit() and 1 <= int(choice) <= len(options):
                type_key = options[int(choice) - 1]
                stack.append(("PLATFORM", {**ctx, "type": type_key}))
            else:
                show_error(f"'{choice}' is not a valid option. Please choose from the list above.")

        elif state == "PLATFORM":
            rec = ctx["version"]
            type_key = ctx["type"]
            choice, platforms = show_platform_screen(rec, type_key)

            if choice == "q":
                break
            elif choice == "b":
                stack.pop()
            elif choice == "m":
                stack[:] = [("LIST", {"page": 1})]
            elif choice.isdigit() and 1 <= int(choice) <= len(platforms):
                platform = platforms[int(choice) - 1]
                stack.append(("RESULT", {**ctx, "platform": platform}))
            else:
                show_error(f"'{choice}' is not a valid option. Please choose from the list above.")

        elif state == "RESULT":
            choice = show_result_screen(ctx["version"], ctx["type"], ctx["platform"])

            if choice == "q":
                break
            elif choice == "b":
                stack.pop()
            elif choice == "m":
                stack[:] = [("LIST", {"page": 1})]
            else:
                show_error(f"'{choice}' is not a valid option. Please choose from the list above.")

    clear_screen()
    print("Goodbye!")


def main():
    try:
        run()
    except KeyboardInterrupt:
        print()
        print("Goodbye!")
        sys.exit(130)
    except EOFError:
        print()
        print("Goodbye!")
        sys.exit(1)


if __name__ == "__main__":
    main()

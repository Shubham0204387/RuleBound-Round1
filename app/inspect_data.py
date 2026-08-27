import json
from pathlib import Path


def show_structure(name, data, indent=0):
    prefix = " " * indent

    if isinstance(data, dict):
        print(f"{prefix}{name}: DICT")
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{prefix}  {key}: {type(value).__name__}")
            else:
                print(f"{prefix}  {key}: {type(value).__name__} = {value}")

    elif isinstance(data, list):
        print(f"{prefix}{name}: LIST ({len(data)} items)")

        if data:
            print(f"{prefix}  First item:")
            show_structure("item", data[0], indent + 4)

    else:
        print(f"{prefix}{name}: {type(data).__name__}")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


print("\n========== CATALOG ==========")
catalog = load_json("data/catalog.json")
show_structure("catalog", catalog)

print("\n========== FINISHES ==========")
finishes = load_json("data/finishes.json")
show_structure("finishes", finishes)

print("\n========== ROOMS ==========")
room_files = sorted(Path("data/rooms").glob("*.json"))

for room_file in room_files:
    room = load_json(room_file)
    print(f"\n--- {room_file.name} ---")
    show_structure("room", room)

print("\n========== HISTORICAL JOBS ==========")
jobs = load_json("data/historical_jobs.json")
show_structure("historical_jobs", jobs)

print("\n========== BRIEFS ==========")
brief_files = sorted(Path("data/briefs").glob("*"))

for brief_file in brief_files:
    if brief_file.is_file():
        text = brief_file.read_text(encoding="utf-8").strip()
        print(f"\n--- {brief_file.name} ---")
        print(text[:500])
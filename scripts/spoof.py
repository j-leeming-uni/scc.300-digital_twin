import time
from pathlib import Path

hints_dir = Path("hints")

while True:
    for hint_file in hints_dir.iterdir():
        print(f"Spoofing {hint_file}")
        hint_file.write_text("0 0 0 0")
    time.sleep(0.3)

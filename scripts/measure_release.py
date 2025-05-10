import sys
import time
from pathlib import Path

hints_dir = Path("hints")
hints_file = hints_dir / f'junction-{sys.argv[1]}'

while True:
    print(f"Spoofing {hints_file}")
    hints_file.write_text(sys.argv[2])
    time.sleep(0.3)

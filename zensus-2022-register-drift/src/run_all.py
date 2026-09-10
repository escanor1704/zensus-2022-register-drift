"""Run the whole pipeline in order. Stops at the first failure."""
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).parent

for stage in ["pull.py", "clean.py", "join.py", "analyze.py"]:
    print(f"\n--- {stage} ---")
    if subprocess.run([sys.executable, str(SRC / stage)], cwd=SRC).returncode:
        print(f"\nFAILED at {stage}")
        sys.exit(1)
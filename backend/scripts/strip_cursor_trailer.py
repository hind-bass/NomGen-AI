"""Remove Cursor co-author trailer from git commit messages."""
import sys

for line in sys.stdin:
    if "Co-authored-by: Cursor" not in line:
        sys.stdout.write(line)

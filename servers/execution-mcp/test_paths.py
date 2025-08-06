#!/usr/bin/env python3

import sys
from pathlib import Path

print("=== PATH DEBUGGING ===")
print(f"Current working directory: {Path.cwd()}")
print(f"Script directory: {Path(__file__).parent}")
print(f"Script file: {__file__}")

# Test the same logic as instruction_executor.py
script_dir = Path(__file__).parent
instructions_file = script_dir / "instructions.md"

print(f"Instructions file path: {instructions_file}")
print(f"File exists: {instructions_file.exists()}")

# Test fallback logic
if not Path(instructions_file).exists():
    instructions_file = Path.cwd() / "instructions.md"
    print(f"Fallback 1 - Instructions file path: {instructions_file}")
    print(f"Fallback 1 - File exists: {instructions_file.exists()}")

if not Path(instructions_file).exists():
    current = Path.cwd()
    while current != current.parent:
        potential_path = current / "execution-mcp" / "instructions.md"
        print(f"Checking: {potential_path} - exists: {potential_path.exists()}")
        if potential_path.exists():
            instructions_file = potential_path
            break
        current = current.parent

print(f"Final instructions file path: {instructions_file}")
print(f"Final file exists: {instructions_file.exists()}") 
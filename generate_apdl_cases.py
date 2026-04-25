#!/usr/bin/env python3
"""
Generate APDL files for all weight/speed cases.

Output structure:
  adplcommand/
    w40/
      w40_v10/
        w40_v10.apdl

The generated APDL files are based on deck_moving_load.apdl, with only
case name, axle weight, speed, and step count changed.
"""

from __future__ import annotations

import math
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_FILE = BASE_DIR / "deck_moving_load.apdl"
OUTPUT_ROOT = BASE_DIR / "adplcommand"

WEIGHTS_KN = [38, 40, 42, 44, 45, 46, 48, 50]
SPEEDS_MS = [10, 15, 20, 25, 30, 35, 40, 45]

DECK_LENGTH = 40.0
AXLE_SPACE = 8.0
DT = 0.001


def replace_parameter(lines: list[str], name: str, value: str) -> list[str]:
    prefix = f"{name}="
    return [f"{prefix}{value}\n" if line.startswith(prefix) else line for line in lines]


def generate_case(template_lines: list[str], weight_kn: int, speed_ms: int) -> str:
    case_name = f"w{weight_kn}_v{speed_ms}"
    axle_weight_n = weight_kn * 1000
    end_time = (DECK_LENGTH + AXLE_SPACE) / speed_ms
    n_steps = math.ceil(end_time / DT)

    lines = template_lines[:]
    lines = [
        f"/FILNAME,{case_name},1\n" if line.startswith("/FILNAME,") else line
        for line in lines
    ]
    lines = [
        f"/TITLE,Deck Moving Double-Axle Load {case_name}\n"
        if line.startswith("/TITLE,")
        else line
        for line in lines
    ]
    lines = replace_parameter(lines, "VEL", str(speed_ms))
    lines = replace_parameter(lines, "F_FRONT", str(axle_weight_n))
    lines = replace_parameter(lines, "F_REAR", str(axle_weight_n))
    lines = replace_parameter(lines, "N_STEPS", str(n_steps))
    lines = [
        f"FILE,{case_name},rst\n" if line.startswith("FILE,deck_moving_load,rst") else line
        for line in lines
    ]

    return "".join(lines)


def main() -> None:
    if not TEMPLATE_FILE.exists():
        raise FileNotFoundError(f"Template APDL not found: {TEMPLATE_FILE}")

    template_lines = TEMPLATE_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
    count = 0

    for weight_kn in WEIGHTS_KN:
        weight_dir = OUTPUT_ROOT / f"w{weight_kn}"
        for speed_ms in SPEEDS_MS:
            case_name = f"w{weight_kn}_v{speed_ms}"
            case_dir = weight_dir / case_name
            case_dir.mkdir(parents=True, exist_ok=True)
            case_file = case_dir / f"{case_name}.apdl"
            case_file.write_text(
                generate_case(template_lines, weight_kn, speed_ms),
                encoding="utf-8",
                newline="",
            )
            count += 1

    print(f"Generated {count} APDL files under {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()

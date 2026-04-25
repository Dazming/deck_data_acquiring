#!/usr/bin/env python3
"""
Merge split ANSYS POST26 CSV exports.

Input:
  {CASE_NAME}p1.csv  TIME, N1_UZ, N1_AZ, ..., N4_UZ, N4_AZ
  {CASE_NAME}p2.csv  TIME, N5_UZ, N5_AZ, ..., N7_UZ, N7_AZ

Output:
  {CASE_NAME}.csv    TIME, N1_UZ, N1_AZ, ..., N7_UZ, N7_AZ

Edit CASE_NAME below to choose which split files to merge.
"""

from __future__ import annotations

import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
RAW_SPLIT_DIR = BASE_DIR / "csv_p1p2"
MERGED_DIR = BASE_DIR / "csv_merged"

# ============================================================
# Change this one value to select the files to merge.
# Example:
#   CASE_NAME = "w40_v40" reads w40_v40p1.csv and w40_v40p2.csv,
#   then writes w40_v40.csv.
# ============================================================
CASE_NAME = "w40_v30"
# ============================================================

P1_FILE = RAW_SPLIT_DIR / f"{CASE_NAME}p1.csv"
P2_FILE = RAW_SPLIT_DIR / f"{CASE_NAME}p2.csv"
OUTPUT_FILE = MERGED_DIR / f"{CASE_NAME}.csv"

TIME_TOL = 1e-12


def clean_cell(value: str) -> str:
    return value.strip()


def read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = [clean_cell(cell) for cell in next(reader)]
        rows = [
            [clean_cell(cell) for cell in row]
            for row in reader
            if row and row[0].strip()
        ]

    return header, rows


def assert_same_time(row_index: int, time_1: str, time_2: str) -> None:
    t1 = float(time_1)
    t2 = float(time_2)
    if abs(t1 - t2) > TIME_TOL:
        line_number = row_index + 2
        raise ValueError(
            f"TIME mismatch at data row {row_index + 1} "
            f"(CSV line {line_number}): {time_1} != {time_2}"
        )


def main() -> None:
    header_1, rows_1 = read_csv(P1_FILE)
    header_2, rows_2 = read_csv(P2_FILE)

    if not header_1 or header_1[0] != "TIME":
        raise ValueError(f"{P1_FILE.name} first column must be TIME")
    if not header_2 or header_2[0] != "TIME":
        raise ValueError(f"{P2_FILE.name} first column must be TIME")
    if len(rows_1) != len(rows_2):
        raise ValueError(
            f"Row count mismatch: {P1_FILE.name} has {len(rows_1)} rows, "
            f"{P2_FILE.name} has {len(rows_2)} rows"
        )

    output_header = header_1 + header_2[1:]
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(output_header)

        for index, (row_1, row_2) in enumerate(zip(rows_1, rows_2)):
            assert_same_time(index, row_1[0], row_2[0])
            writer.writerow(row_1 + row_2[1:])

    print(f"Reading:  {P1_FILE}")
    print(f"Reading:  {P2_FILE}")
    print(f"Writing:  {OUTPUT_FILE}")
    print(f"Columns:  {output_header}")
    print(f"Rows written: {len(rows_1)}")


if __name__ == "__main__":
    main()

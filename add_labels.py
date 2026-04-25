#!/usr/bin/env python3
"""
add_labels.py
Add ground truth labels to the deck simulation CSV for training.

Input:  csv_merged/w45_v10.csv  (TIME, N1_UZ, N1_AZ, N7_UZ, N7_AZ, ...)
Output: csv_labeled/w45_v10_labeled.csv  (same + 4 label columns)

Label columns:
  front_wheel_pos  -- front wheel distance from left end of deck (m)
  rear_wheel_pos   -- rear wheel distance from left end of deck (m)
  front_axle_wt   -- front axle weight (N), 0 when off deck
  rear_axle_wt    -- rear axle weight (N), 0 when off deck

Logic:
  front_x = speed * time
  rear_x  = front_x - axle_dist
  If wheel x is outside [0, 40]: position = 0, weight = 0
  If the final sample slightly overshoots x=40 by less than one time step,
  clamp it to x=40 to avoid an artificial label jump.
"""

import csv
import re
from pathlib import Path

# ============================================================
# Change this one value to select the case to label.
# Example:
#   CASE_NAME = "w40_v40" reads csv_merged/w40_v40.csv,
#   parses 40 kN and 40 m/s, then writes csv_labeled/w40_v40_labeled.csv.
# ============================================================
CASE_NAME = "w40_v30"
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
MERGED_DIR = BASE_DIR / "csv_merged"
LABELED_DIR = BASE_DIR / "csv_labeled"

AXLE_DIST = 8.0
DECK_LENGTH = 40.0
DT = 0.001


def parse_case_name(case_name):
    match = re.fullmatch(r"w(?P<weight>\d+(?:\.\d+)?)_v(?P<speed>\d+(?:\.\d+)?)", case_name)
    if not match:
        raise ValueError(
            f"Invalid CASE_NAME: {case_name!r}. Expected format like 'w40_v40'."
        )
    axle_weight = float(match.group("weight")) * 1000.0
    speed = float(match.group("speed"))
    return axle_weight, speed


AXLE_WEIGHT, SPEED = parse_case_name(CASE_NAME)
INPUT_FILE = MERGED_DIR / f"{CASE_NAME}.csv"
OUTPUT_FILE = LABELED_DIR / f"{CASE_NAME}_labeled.csv"
EXIT_TOL = SPEED * DT + 1e-9


def label_wheel_position(x, allow_exit_clamp=False):
    if 0.0 <= x <= DECK_LENGTH:
        return x, AXLE_WEIGHT
    if allow_exit_clamp and DECK_LENGTH < x <= DECK_LENGTH + EXIT_TOL:
        return DECK_LENGTH, AXLE_WEIGHT
    return 0.0, 0.0


def compute_labels(t):
    """
    Given time t (seconds), return (front_pos, rear_pos, front_wt, rear_wt).
    When wheel is off deck (x < 0 or x > 40), position and weight are 0.
    """
    front_x = SPEED * t
    rear_x  = front_x - AXLE_DIST

    front_pos, front_wt = label_wheel_position(front_x)
    rear_pos, rear_wt = label_wheel_position(rear_x, allow_exit_clamp=True)

    return front_pos, rear_pos, front_wt, rear_wt


def main():
    input_path = INPUT_FILE
    output_path = OUTPUT_FILE

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}")
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Reading:  {input_path}")
    print(f"Writing:  {output_path}")
    print(f"Params:   weight={AXLE_WEIGHT}N, speed={SPEED}m/s, axle_dist={AXLE_DIST}m")
    print(f"Exit tol: {EXIT_TOL}m")

    with open(input_path, "r", newline="", encoding="utf-8") as fin, \
         open(output_path, "w", newline="", encoding="utf-8") as fout:

        reader = csv.reader(fin)
        writer = csv.writer(fout)

        # Read and write header
        header = next(reader)
        new_header = header + ["front_wheel_pos", "rear_wheel_pos",
                               "front_axle_wt", "rear_axle_wt"]
        writer.writerow(new_header)
        print(f"Columns:  {new_header}")

        # Process each data row
        row_count = 0
        for row in reader:
            if len(row) < 1 or row[0].strip() == "":
                continue

            t = float(row[0])
            front_pos, rear_pos, front_wt, rear_wt = compute_labels(t)

            new_row = row + [front_pos, rear_pos, front_wt, rear_wt]
            writer.writerow(new_row)
            row_count += 1

        print(f"Rows written: {row_count}")

    print("Done.")


if __name__ == "__main__":
    main()

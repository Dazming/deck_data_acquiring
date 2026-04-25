import csv
import re
from pathlib import Path

import matplotlib.pyplot as plt

# ============================
CASE_NAME = "w38_v40"
# ===========================

"""
Run the full CSV workflow for one simulation case:
1. Merge csv_p1p2/{CASE_NAME}p1.csv and {CASE_NAME}p2.csv
2. Add ground-truth labels to csv_labeled/{CASE_NAME}_labeled.csv
3. Plot selected node responses and labels

Change CASE_NAME on the first line to switch case, for example:
  CASE_NAME = "w40_v40"
  CASE_NAME = "w38_v10"
"""

# Choose measurement nodes to plot.
# Examples:
#   NODES_TO_PLOT = ["N1", "N7"]
#   NODES_TO_PLOT = ["N1", "N2"]
#   NODES_TO_PLOT = ["N1", "N2", "N3", "N4", "N5", "N6", "N7"]
NODES_TO_PLOT = ["N1", "N7"]

BASE_DIR = Path(__file__).resolve().parent
RAW_SPLIT_DIR = BASE_DIR / "csv_p1p2"
MERGED_DIR = BASE_DIR / "csv_merged"
LABELED_DIR = BASE_DIR / "csv_labeled"

AXLE_DIST = 8.0
DECK_LENGTH = 40.0
DT = 0.001
TIME_TOL = 1e-12


def clean_cell(value):
    return value.strip()


def parse_case_name(case_name):
    match = re.fullmatch(
        r"w(?P<weight>\d+(?:\.\d+)?)_v(?P<speed>\d+(?:\.\d+)?)", case_name
    )
    if not match:
        raise ValueError(
            f"Invalid CASE_NAME: {case_name!r}. Expected format like 'w40_v40'."
        )
    axle_weight = float(match.group("weight")) * 1000.0
    speed = float(match.group("speed"))
    return axle_weight, speed


def read_csv_rows(path):
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


def assert_same_time(row_index, time_1, time_2):
    t1 = float(time_1)
    t2 = float(time_2)
    if abs(t1 - t2) > TIME_TOL:
        line_number = row_index + 2
        raise ValueError(
            f"TIME mismatch at data row {row_index + 1} "
            f"(CSV line {line_number}): {time_1} != {time_2}"
        )


def merge_split_csv(case_name):
    p1_file = RAW_SPLIT_DIR / f"{case_name}p1.csv"
    p2_file = RAW_SPLIT_DIR / f"{case_name}p2.csv"
    output_file = MERGED_DIR / f"{case_name}.csv"

    header_1, rows_1 = read_csv_rows(p1_file)
    header_2, rows_2 = read_csv_rows(p2_file)

    if not header_1 or header_1[0] != "TIME":
        raise ValueError(f"{p1_file.name} first column must be TIME")
    if not header_2 or header_2[0] != "TIME":
        raise ValueError(f"{p2_file.name} first column must be TIME")
    if len(rows_1) != len(rows_2):
        raise ValueError(
            f"Row count mismatch: {p1_file.name} has {len(rows_1)} rows, "
            f"{p2_file.name} has {len(rows_2)} rows"
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_header = header_1 + header_2[1:]

    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(output_header)
        for index, (row_1, row_2) in enumerate(zip(rows_1, rows_2)):
            assert_same_time(index, row_1[0], row_2[0])
            writer.writerow(row_1 + row_2[1:])

    print(f"Merged:   {output_file}")
    print(f"Rows:     {len(rows_1)}")
    return output_file


def label_wheel_position(x, axle_weight, exit_tol):
    if 0.0 <= x <= DECK_LENGTH:
        return x, axle_weight
    if DECK_LENGTH < x <= DECK_LENGTH + exit_tol:
        return DECK_LENGTH, axle_weight
    return 0.0, 0.0


def compute_labels(t, axle_weight, speed):
    exit_tol = speed * DT + 1e-9
    front_x = speed * t
    rear_x = front_x - AXLE_DIST
    front_pos, front_wt = label_wheel_position(front_x, axle_weight, exit_tol)
    rear_pos, rear_wt = label_wheel_position(rear_x, axle_weight, exit_tol)
    return front_pos, rear_pos, front_wt, rear_wt


def add_labels(case_name):
    axle_weight, speed = parse_case_name(case_name)
    input_file = MERGED_DIR / f"{case_name}.csv"
    output_file = LABELED_DIR / f"{case_name}_labeled.csv"

    if not input_file.exists():
        raise FileNotFoundError(f"Merged CSV not found: {input_file}")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with (
        input_file.open("r", newline="", encoding="utf-8") as fin,
        output_file.open("w", newline="", encoding="utf-8") as fout,
    ):
        reader = csv.reader(fin)
        writer = csv.writer(fout)

        header = next(reader)
        label_header = [
            "front_wheel_pos",
            "rear_wheel_pos",
            "front_axle_wt",
            "rear_axle_wt",
        ]
        writer.writerow(header + label_header)

        row_count = 0
        for row in reader:
            if len(row) < 1 or row[0].strip() == "":
                continue
            t = float(row[0])
            labels = compute_labels(t, axle_weight, speed)
            writer.writerow(row + list(labels))
            row_count += 1

    print(f"Labeled:  {output_file}")
    print(f"Params:   weight={axle_weight}N, speed={speed}m/s")
    print(f"Rows:     {row_count}")
    return output_file


def read_labeled_csv(file_path, nodes_to_plot):
    with file_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        rows = []
        for r in reader:
            rows.append(
                {
                    (k.strip() if k else k): (v.strip() if isinstance(v, str) else v)
                    for k, v in r.items()
                }
            )

    if not rows:
        raise ValueError("CSV is empty")

    required_cols = [
        "TIME",
        "front_wheel_pos",
        "rear_wheel_pos",
        "front_axle_wt",
        "rear_axle_wt",
    ]
    for node in nodes_to_plot:
        required_cols.extend([f"{node}_UZ", f"{node}_AZ"])

    missing = [c for c in required_cols if c not in rows[0]]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    t = [float(r["TIME"]) for r in rows]
    displacement = {
        node: [float(r[f"{node}_UZ"]) for r in rows] for node in nodes_to_plot
    }
    acceleration = {
        node: [float(r[f"{node}_AZ"]) for r in rows] for node in nodes_to_plot
    }
    front_pos = [float(r["front_wheel_pos"]) for r in rows]
    rear_pos = [float(r["rear_wheel_pos"]) for r in rows]
    front_wt = [float(r["front_axle_wt"]) for r in rows]
    rear_wt = [float(r["rear_axle_wt"]) for r in rows]
    return t, displacement, acceleration, front_pos, rear_pos, front_wt, rear_wt


def plot_labeled_csv(case_name, nodes_to_plot):
    input_file = LABELED_DIR / f"{case_name}_labeled.csv"
    if not input_file.exists():
        raise FileNotFoundError(f"Labeled CSV not found: {input_file}")

    (
        t,
        displacement,
        acceleration,
        front_pos,
        rear_pos,
        front_wt,
        rear_wt,
    ) = read_labeled_csv(input_file, nodes_to_plot)

    fig, axes = plt.subplots(2, 2, figsize=(14, 9), sharex=True)

    ax = axes[0, 0]
    for node in nodes_to_plot:
        ax.plot(t, displacement[node], label=f"{node}_UZ", linewidth=1.2)
    ax.set_title("Displacement Response")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Displacement UZ (m)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    ax = axes[0, 1]
    for node in nodes_to_plot:
        ax.plot(t, acceleration[node], label=f"{node}_AZ", linewidth=1.2)
    ax.set_title("Acceleration Response")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Acceleration AZ (m/s^2)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    ax = axes[1, 0]
    ax.plot(t, front_pos, label="Front Wheel Position", linewidth=1.2)
    ax.plot(t, rear_pos, label="Rear Wheel Position", linewidth=1.2)
    ax.set_title("Axle Position")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Position (m)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    ax = axes[1, 1]
    ax.plot(t, front_wt, label="Front Axle Weight", linewidth=1.2)
    ax.plot(t, rear_wt, label="Rear Axle Weight", linewidth=1.2)
    ax.set_title("Axle Weight")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Weight (N)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.suptitle(f"Labeled Data Visualization: {input_file.name}", fontsize=12)
    plt.tight_layout()
    plt.show()


def main():
    print(f"Case:     {CASE_NAME}")
    merge_split_csv(CASE_NAME)
    add_labels(CASE_NAME)
    plot_labeled_csv(CASE_NAME, NODES_TO_PLOT)


if __name__ == "__main__":
    main()

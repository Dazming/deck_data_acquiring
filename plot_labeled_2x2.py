#!/usr/bin/env python3
"""
plot_labeled_2x2.py
Plot a 2x2 figure from labeled deck simulation CSV.

Usage:
- Edit CASE_NAME and NODES_TO_PLOT below.
- Run: python plot_labeled_2x2.py
"""

import csv
from pathlib import Path

import matplotlib.pyplot as plt

# ============================================================
# Change this one value to select the labeled CSV to plot.
# Example:
#   CASE_NAME = "w40_v40" reads csv_labeled/w40_v40_labeled.csv.
# ============================================================
CASE_NAME = "w40_v30"

# Choose measurement nodes to plot.
# Examples:
#   NODES_TO_PLOT = ["N1", "N7"]
#   NODES_TO_PLOT = ["N1", "N2"]
#   NODES_TO_PLOT = ["N1", "N2", "N3", "N4", "N5", "N6", "N7"]
NODES_TO_PLOT = ["N1", "N7"]
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
LABELED_DIR = BASE_DIR / "csv_labeled"
INPUT_CSV = LABELED_DIR / f"{CASE_NAME}_labeled.csv"


def read_labeled_csv(file_path, nodes_to_plot):
    with open(file_path, "r", newline="", encoding="utf-8") as f:
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


def main():
    input_path = INPUT_CSV
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    (
        t,
        displacement,
        acceleration,
        front_pos,
        rear_pos,
        front_wt,
        rear_wt,
    ) = read_labeled_csv(input_path, NODES_TO_PLOT)

    fig, axes = plt.subplots(2, 2, figsize=(14, 9), sharex=True)

    # (1) Displacement response
    ax = axes[0, 0]
    for node in NODES_TO_PLOT:
        ax.plot(t, displacement[node], label=f"{node}_UZ", linewidth=1.2)
    ax.set_title("Displacement Response")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Displacement UZ")
    ax.grid(True, alpha=0.3)
    ax.legend()

    # (2) Acceleration response
    ax = axes[0, 1]
    for node in NODES_TO_PLOT:
        ax.plot(t, acceleration[node], label=f"{node}_AZ", linewidth=1.2)
    ax.set_title("Acceleration Response")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Acceleration AZ")
    ax.grid(True, alpha=0.3)
    ax.legend()

    # (3) Front/Rear axle position
    ax = axes[1, 0]
    ax.plot(t, front_pos, label="Front Wheel Position", linewidth=1.2)
    ax.plot(t, rear_pos, label="Rear Wheel Position", linewidth=1.2)
    ax.set_title("Axle Position")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Position (m)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    # (4) Front/Rear axle weight
    ax = axes[1, 1]
    ax.plot(t, front_wt, label="Front Axle Weight", linewidth=1.2)
    ax.plot(t, rear_wt, label="Rear Axle Weight", linewidth=1.2)
    ax.set_title("Axle Weight")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Weight (N)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.suptitle(
        f"Labeled Data Visualization: {input_path.name}", fontsize=12
    )
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()

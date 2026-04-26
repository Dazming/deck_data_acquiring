# Deck Data Acquiring

This project is used to acquire, organize, label, and visualize deck moving-load
simulation data from ANSYS APDL.

The main workflow is:

1. Run APDL command files in ANSYS.
2. Export split CSV files from POST26.
3. Merge N1-N7 response data.
4. Add ground-truth axle labels.
5. Plot displacement, acceleration, axle position, and axle weight curves.

## Environment

When running Python scripts, use the `test` conda environment:

```powershell
conda run -n test python process_case.py
```

The model and data use SI units:

- Displacement `N*_UZ`: `m`
- Acceleration `N*_AZ`: `m/s^2`
- Axle weight labels: `N`
- Speed: `m/s`
- Time: `s`

## Directory Structure

```text
deck_data_acquiring/
  adplcommand/
    w38/
      w38_v10/w38_v10.apdl
      ...
    w40/
      w40_v10/w40_v10.apdl
      ...
    w45/
      w45_v10/w45_v10.apdl
      ...

  csv_p1p2/
    w40_v40p1.csv
    w40_v40p2.csv

  csv_merged/
    w40_v40.csv

  csv_labeled/
    w40_v40_labeled.csv

  process_case.py
  generate_apdl_cases.py
  merge_split_csv.py
  add_labels.py
  plot_labeled_2x2.py
```

## Case Naming

Simulation cases use this naming format:

```text
w{axle_weight_kN}_v{speed_mps}
```

Examples:

- `w38_v40`: axle weight `38 kN`, speed `40 m/s`
- `w40_v45`: axle weight `40 kN`, speed `45 m/s`
- `w45_v10`: axle weight `45 kN`, speed `10 m/s`

## APDL Command Files

APDL command files are stored under `adplcommand/`.

Example:

```text
adplcommand/w40/w40_v10/w40_v10.apdl
```

Each APDL file sets:

- `F_FRONT = axle_weight_kN * 1000`
- `F_REAR = axle_weight_kN * 1000`
- `VEL = speed_mps`
- `DT = 0.001`

To regenerate APDL command files:

```powershell
conda run -n test python generate_apdl_cases.py
```

## Measurement Points

The response nodes are:

```text
N1 = (5,  2, 0)
N2 = (10, -2, 0)
N3 = (15,  2, 0)
N4 = (20, -2, 0)
N5 = (25,  2, 0)
N6 = (30, -2, 0)
N7 = (35,  2, 0)
```

N7 follows Fig. 9 and the alternating measurement-point layout.

## Full Workflow

Use `process_case.py` for the combined workflow.

At the first line of `process_case.py`, change:

```python
CASE_NAME = "w40_v45"
```

Then run:

```powershell
conda run -n test python process_case.py
```

This script will:

1. Read:

   ```text
   csv_p1p2/{CASE_NAME}p1.csv
   csv_p1p2/{CASE_NAME}p2.csv
   ```

2. Write merged response data:

   ```text
   csv_merged/{CASE_NAME}.csv
   ```

3. Write labeled data:

   ```text
   csv_labeled/{CASE_NAME}_labeled.csv
   ```

4. Plot selected node responses and labels.

To choose plotted nodes, edit:

```python
NODES_TO_PLOT = ["N1", "N7"]
```

Examples:

```python
NODES_TO_PLOT = ["N1", "N2"]
NODES_TO_PLOT = ["N1", "N2", "N3", "N4", "N5", "N6", "N7"]
```

## Split CSV Export Rule

ANSYS POST26 export may be split into two files:

- `p1`: N1-N4 response data
- `p2`: N5-N7 response data

For case `w40_v40`, place files here:

```text
csv_p1p2/w40_v40p1.csv
csv_p1p2/w40_v40p2.csv
```

Expected columns:

```text
w40_v40p1.csv:
TIME, N1_UZ, N1_AZ, N2_UZ, N2_AZ, N3_UZ, N3_AZ, N4_UZ, N4_AZ

w40_v40p2.csv:
TIME, N5_UZ, N5_AZ, N6_UZ, N6_AZ, N7_UZ, N7_AZ
```

## Individual Scripts

### Merge Only

Edit `CASE_NAME` in `merge_split_csv.py`, then run:

```powershell
conda run -n test python merge_split_csv.py
```

Output:

```text
csv_merged/{CASE_NAME}.csv
```

### Add Labels Only

Edit `CASE_NAME` in `add_labels.py`, then run:

```powershell
conda run -n test python add_labels.py
```

Output:

```text
csv_labeled/{CASE_NAME}_labeled.csv
```

The script parses axle weight and speed from the case name.

### Plot Only

Edit `CASE_NAME` and `NODES_TO_PLOT` in `plot_labeled_2x2.py`, then run:

```powershell
conda run -n test python plot_labeled_2x2.py
```

## Label Logic

For a case like `w40_v45`:

```text
front_x = speed * time
rear_x  = front_x - 8
```

The deck length is `40 m`, and axle spacing is `8 m`.

Rules:

- If the front axle position is outside `[0, 40]`, front position and weight are `0`.
- If the rear axle position is outside `[0, 40]`, rear position and weight are `0`.
- To avoid a final-frame jump caused by rounded APDL step counts, the rear axle is allowed to clamp to `40 m` only when it slightly exceeds `40 m` by less than one time step.

This means for `v40`, at `t=1.001s`:

```text
front_x = 40.04 m
front_wheel_pos = 0
front_axle_wt = 0
```

## Typical Usage

1. Select an APDL command file from `adplcommand/`.
2. Run it in ANSYS.
3. Export N1-N4 as `csv_p1p2/{CASE_NAME}p1.csv`.
4. Export N5-N7 as `csv_p1p2/{CASE_NAME}p2.csv`.
5. Set `CASE_NAME` in `process_case.py`.
6. Run:

   ```powershell
   conda run -n test python process_case.py
   ```

7. Use the generated labeled CSV from `csv_labeled/`.


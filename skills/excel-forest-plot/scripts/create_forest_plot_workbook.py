#!/usr/bin/env python3
"""Create an Excel workbook for a vertical forest plot.

The workbook contains source data, helper columns, a native Excel chart, and
brief instructions for editing the plot inside Excel.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import xlsxwriter


@dataclass(frozen=True)
class ForestRow:
    label: str
    estimate: float
    lower: float
    upper: float

    @property
    def minus_error(self) -> float:
        return self.estimate - self.lower

    @property
    def plus_error(self) -> float:
        return self.upper - self.estimate


LABEL_KEYS = ("label", "group", "name", "study")
ESTIMATE_KEYS = ("estimate", "hr", "or", "rr", "value")
LOWER_KEYS = ("lower", "low", "lcl", "ci_low")
UPPER_KEYS = ("upper", "high", "ucl", "ci_high")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create an Excel workbook for a vertical forest plot."
    )
    parser.add_argument("--output", required=True, help="Path for the .xlsx file.")
    parser.add_argument(
        "--data",
        help=(
            "Semicolon-separated rows in the form label,estimate,lower,upper. "
            "Example: 'Group 1,0.80,0.66,0.97;Group 2,0.76,0.64,0.91'"
        ),
    )
    parser.add_argument(
        "--input-csv",
        help="CSV file with label/group/name/study, estimate/hr/or/rr/value, lower, and upper columns.",
    )
    parser.add_argument(
        "--metric-label",
        default="Hazard ratio",
        help="Axis label and chart wording, for example 'Hazard ratio' or 'Odds ratio'.",
    )
    parser.add_argument(
        "--title",
        default="Forest plot",
        help="Chart title.",
    )
    parser.add_argument(
        "--no-log-axis",
        action="store_true",
        help="Use a linear value axis instead of a log-scale axis.",
    )
    return parser.parse_args()


def first_present(row: dict[str, str], keys: Iterable[str]) -> str | None:
    normalized = {k.strip().lower(): v for k, v in row.items()}
    for key in keys:
        if key in normalized:
            return normalized[key]
    return None


def parse_inline_data(raw: str) -> list[ForestRow]:
    rows: list[ForestRow] = []
    for index, chunk in enumerate(raw.split(";"), start=1):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = [part.strip() for part in chunk.split(",")]
        if len(parts) != 4:
            raise ValueError(
                f"Row {index} must have 4 comma-separated values: label,estimate,lower,upper"
            )
        rows.append(ForestRow(parts[0], float(parts[1]), float(parts[2]), float(parts[3])))
    return rows


def parse_csv(path: Path) -> list[ForestRow]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV file has no header row.")
        rows = []
        for index, row in enumerate(reader, start=2):
            label = first_present(row, LABEL_KEYS)
            estimate = first_present(row, ESTIMATE_KEYS)
            lower = first_present(row, LOWER_KEYS)
            upper = first_present(row, UPPER_KEYS)
            if label is None or estimate is None or lower is None or upper is None:
                raise ValueError(
                    f"CSV row {index} must include label, estimate, lower, and upper columns."
                )
            rows.append(ForestRow(label, float(estimate), float(lower), float(upper)))
    return rows


def validate_rows(rows: list[ForestRow], *, log_axis: bool) -> None:
    if not rows:
        raise ValueError("At least one data row is required.")
    for index, row in enumerate(rows, start=1):
        if not row.label:
            raise ValueError(f"Row {index} has an empty label.")
        if row.lower > row.estimate or row.estimate > row.upper:
            raise ValueError(
                f"Row {index} is invalid: require lower <= estimate <= upper."
            )
        if log_axis and min(row.lower, row.estimate, row.upper) <= 0:
            raise ValueError(
                f"Row {index} has non-positive values; log-scale axes require positive values."
            )


def floor_to_tick(value: float) -> float:
    if value >= 1:
        return max(0.1, round(value - 0.1, 1))
    return max(0.01, round(value - 0.05, 2))


def ceil_to_tick(value: float) -> float:
    if value >= 1:
        return round(value + 0.1, 1)
    return round(value + 0.05, 2)


def write_workbook(
    output: Path,
    rows: list[ForestRow],
    *,
    metric_label: str,
    title: str,
    log_axis: bool,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    workbook = xlsxwriter.Workbook(str(output))
    ws = workbook.add_worksheet("Forest plot data")
    notes = workbook.add_worksheet("How to edit")

    header_fmt = workbook.add_format(
        {"bold": True, "bg_color": "#EAF1FE", "border": 1, "align": "center"}
    )
    number_fmt = workbook.add_format({"num_format": "0.00"})
    text_fmt = workbook.add_format({"text_wrap": True, "valign": "top"})

    headers = [
        "Group",
        "Estimate",
        "Lower CI",
        "Upper CI",
        "Minus error",
        "Plus error",
        "Reference",
    ]
    for col, header in enumerate(headers):
        ws.write(0, col, header, header_fmt)

    for row_index, row in enumerate(rows, start=1):
        excel_row = row_index + 1
        ws.write(row_index, 0, row.label)
        ws.write_number(row_index, 1, row.estimate, number_fmt)
        ws.write_number(row_index, 2, row.lower, number_fmt)
        ws.write_number(row_index, 3, row.upper, number_fmt)
        ws.write_formula(row_index, 4, f"=B{excel_row}-C{excel_row}", number_fmt)
        ws.write_formula(row_index, 5, f"=D{excel_row}-B{excel_row}", number_fmt)
        ws.write_number(row_index, 6, 1, number_fmt)

    ws.set_column("A:A", 20)
    ws.set_column("B:G", 14)
    ws.freeze_panes(1, 0)

    chart = workbook.add_chart({"type": "line"})
    last_row = len(rows) + 1
    chart.add_series(
        {
            "name": metric_label,
            "categories": f"='Forest plot data'!$A$2:$A${last_row}",
            "values": f"='Forest plot data'!$B$2:$B${last_row}",
            "line": {"none": True},
            "marker": {
                "type": "circle",
                "size": 8,
                "border": {"color": "#2E4780", "width": 1.5},
                "fill": {"color": "#A3BEFA"},
            },
            "y_error_bars": {
                "type": "custom",
                "plus_values": f"='Forest plot data'!$F$2:$F${last_row}",
                "minus_values": f"='Forest plot data'!$E$2:$E${last_row}",
                "line": {"color": "#2E4780", "width": 1.5},
                "end_style": 1,
            },
        }
    )
    chart.add_series(
        {
            "name": "Reference = 1",
            "categories": f"='Forest plot data'!$A$2:$A${last_row}",
            "values": f"='Forest plot data'!$G$2:$G${last_row}",
            "line": {"color": "#464C55", "dash_type": "dash"},
            "marker": {"type": "none"},
        }
    )

    min_value = min(row.lower for row in rows)
    max_value = max(max(row.upper for row in rows), 1)
    y_axis = {
        "name": f"{metric_label} ({'log scale' if log_axis else 'linear scale'})",
        "min": floor_to_tick(min_value),
        "max": ceil_to_tick(max_value),
        "major_gridlines": {"visible": True, "line": {"color": "#E6E8F0"}},
    }
    if log_axis:
        y_axis["log_base"] = 10

    chart.set_title({"name": title})
    chart.set_y_axis(y_axis)
    chart.set_x_axis({"name": "Group"})
    chart.set_legend({"position": "bottom"})
    chart.set_size({"width": 720, "height": 500})
    chart.set_chartarea({"border": {"none": True}, "fill": {"color": "#FCFCFD"}})
    chart.set_plotarea({"border": {"color": "#D7DBE7"}, "fill": {"color": "#FFFFFF"}})
    ws.insert_chart("I2", chart)

    notes.set_column("A:A", 105)
    note_lines = [
        "Excel forest plot method:",
        "1. Keep the helper columns: Minus error = Estimate - Lower CI; Plus error = Upper CI - Estimate.",
        "2. The main chart uses a native Excel line chart with markers and custom vertical error bars.",
        "3. The dashed reference series is fixed at 1. Edit it only if the null value is not 1.",
        "4. To change labels, edit the Group column on the data sheet.",
        "5. If Excel removes error bars after heavy editing, select the estimate series, add Error Bars, choose Custom, and point positive values to Plus error and negative values to Minus error.",
    ]
    for i, line in enumerate(note_lines):
        notes.write(i, 0, line, text_fmt)

    workbook.close()


def main() -> None:
    args = parse_args()
    if bool(args.data) == bool(args.input_csv):
        raise SystemExit("Provide exactly one of --data or --input-csv.")

    rows = parse_inline_data(args.data) if args.data else parse_csv(Path(args.input_csv))
    log_axis = not args.no_log_axis
    validate_rows(rows, log_axis=log_axis)
    write_workbook(
        Path(args.output),
        rows,
        metric_label=args.metric_label,
        title=args.title,
        log_axis=log_axis,
    )


if __name__ == "__main__":
    main()

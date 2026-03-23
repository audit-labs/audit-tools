"""CSV reporter: writes one CSV file per data section into an output directory."""

import csv
import os


def write(output_dir, filename, rows):
    """
    Write a list of dicts to a CSV file in output_dir.
    Skips writing if rows is empty, but logs the skip.
    """
    if not rows:
        print(f"  {filename}: no data, skipping")
        return

    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"  {filename}: {len(rows)} rows -> {path}")


def write_summary(output_dir, org, sections):
    """
    Write a plain-text summary file listing section names and row counts.
    sections: list of (label, row_count) tuples
    """
    path = os.path.join(output_dir, "summary.txt")
    lines = [
        f"GitHub Audit Package",
        f"Org: {org}",
        f"",
        f"Section                        Rows",
        f"{'─' * 40}",
    ]
    for label, count in sections:
        lines.append(f"{label:<35}{count}")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"  summary.txt -> {path}")

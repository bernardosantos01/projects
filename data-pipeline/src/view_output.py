"""Utility script to inspect parquet output files in a readable format."""

import argparse
from pathlib import Path

import pandas as pd


def display_dataframe(df: pd.DataFrame, limit: int = 10, show_columns: bool = True) -> None:
    """Print a concise summary and preview of the DataFrame."""
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print()

    if show_columns:
        print("Columns:")
        for column in df.columns:
            print(f"  - {column}")
        print()

    print("Preview:")
    preview = df.head(limit)
    if preview.empty:
        print("  <empty DataFrame>")
        return

    print(preview.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Display a parquet output file created by the company data pipeline."
    )
    parser.add_argument(
        "--file",
        type=str,
        default="output/enriched_companies.parquet",
        help="Path to the parquet file to inspect (default: output/enriched_companies.parquet)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of rows to preview in the output table (default: 10)",
    )
    parser.add_argument(
        "--no-columns",
        action="store_true",
        help="Hide the list of columns in the summary output.",
    )
    args = parser.parse_args()

    input_path = Path(args.file)
    if not input_path.exists():
        raise FileNotFoundError(f"Output file not found: {input_path}")

    df = pd.read_parquet(input_path)
    display_dataframe(df, limit=args.limit, show_columns=not args.no_columns)


if __name__ == "__main__":
    main()

"""Main entry point for the data pipeline."""

import argparse
import sys
from pathlib import Path

from src.logger import setup_logger
from src.pipeline import CompanyDataPipeline


logger = setup_logger(__name__, log_level="INFO")


def main():
    """Run the company data pipeline."""
    parser = argparse.ArgumentParser(
        description="Process company data and enrich with family tree information"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Directory containing input JSON files (data_blocks.json, family_tree.json)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Directory for output parquet files (default: output)"
    )
    parser.add_argument(
        "--filename",
        type=str,
        default="enriched_companies.parquet",
        help="Name of output parquet file (default: enriched_companies.parquet)"
    )
    parser.add_argument(
        "--validate",
        type=bool,
        default=True,
        help="Validate data before saving (default: True)"
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    input_dir = Path(args.input)
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {args.input}")
        sys.exit(1)
    
    # Initialize and run pipeline
    try:
        pipeline = CompanyDataPipeline(
            input_dir=str(input_dir),
            output_dir=args.output
        )
        
        output_path = pipeline.run(
            output_filename=args.filename,
            validate=args.validate
        )
        
        if output_path:
            logger.info(f"Pipeline completed successfully. Output saved to: {output_path}")
            sys.exit(0)
        else:
            logger.error("Pipeline failed to complete")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

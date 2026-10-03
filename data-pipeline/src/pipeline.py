"""Main data pipeline orchestration."""

import logging
from pathlib import Path
from typing import Optional

from .logger import setup_logger
from .data_loader import DataLoader
from .enricher import DataEnricher


logger = setup_logger(__name__)


class CompanyDataPipeline:
    """Orchestrates the company data ingestion, enrichment, and export pipeline."""
    
    def __init__(self, input_dir: str, output_dir: str = "output"):
        """
        Initialize the pipeline.
        
        Args:
            input_dir: Directory containing input JSON files
            output_dir: Directory for output parquet files
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.data_loader = DataLoader(str(self.input_dir))
        self.data_enricher = DataEnricher()
        
        logger.info(f"Pipeline initialized with input: {self.input_dir}")
    
    def run(
        self,
        output_filename: str = "enriched_companies.parquet",
        validate: bool = True
    ) -> Optional[Path]:
        """
        Run the complete pipeline: load, enrich, and save data.
        
        Args:
            output_filename: Name of the output parquet file
            validate: Whether to validate data before saving
            
        Returns:
            Path to output file if successful, None otherwise
        """
        logger.info("Starting company data pipeline")
        
        try:
            # Step 1: Load data
            logger.info("Step 1: Loading data blocks")
            companies, loader_stats = self.data_loader.load_data_blocks()
            
            if not companies:
                logger.error("No companies loaded from data blocks")
                return None
            
            logger.info("Step 2: Loading family tree")
            family_tree, _ = self.data_loader.load_family_tree()
            
            logger.info(f"Loaded {len(companies)} companies and {len(family_tree)} family tree entries")
            
            # Step 2: Enrich data
            logger.info("Step 3: Enriching data")
            enriched_df, enrichment_stats = self.data_enricher.join_company_with_family_tree(
                companies,
                family_tree
            )
            
            if enriched_df.empty:
                logger.error("Enrichment resulted in empty DataFrame")
                return None
            
            # Step 3: Validate (optional)
            if validate:
                logger.info("Step 4: Validating enriched data")
                is_valid = self.data_enricher.validate_enriched_data(enriched_df)
                
                if not is_valid:
                    logger.warning("Data validation failed, but proceeding with output")
            
            # Step 4: Save to parquet
            logger.info("Step 5: Saving to parquet")
            output_path = self.output_dir / output_filename
            
            enriched_df.to_parquet(
                output_path,
                engine='pyarrow',
                index=False,
                compression='snappy'
            )
            
            logger.info(f"Successfully saved enriched data to {output_path}")
            
            # Log summary
            self._log_pipeline_summary(loader_stats, enrichment_stats, len(enriched_df))
            
            return output_path
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            return None
    
    def _log_pipeline_summary(self, loader_stats, enrichment_stats, final_record_count):
        """Log a summary of the pipeline execution."""
        logger.info("=" * 60)
        logger.info("PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total companies loaded: {loader_stats.total_companies}")
        logger.info(f"Companies processed: {loader_stats.companies_processed}")
        logger.info(f"Companies enriched: {enrichment_stats.enriched_companies}")
        logger.info(f"Companies without parent: {enrichment_stats.companies_without_parent}")
        logger.info(f"Processing errors: {loader_stats.companies_with_errors}")
        logger.info(f"Final record count: {final_record_count}")
        
        if loader_stats.errors:
            logger.warning(f"Errors encountered during processing:")
            for error in loader_stats.errors[:5]:  # Show first 5 errors
                logger.warning(f"  - DUNS {error['duns']}: {error['error_message']}")
            if len(loader_stats.errors) > 5:
                logger.warning(f"  ... and {len(loader_stats.errors) - 5} more errors")
        
        logger.info("=" * 60)

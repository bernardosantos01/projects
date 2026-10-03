"""Join and enrichment logic for company data."""

import logging
from typing import List, Dict, Any, Tuple
import pandas as pd

from .logger import setup_logger
from .models import ProcessingStats


logger = setup_logger(__name__)


class DataEnricher:
    """Handles joining and enriching company data with family tree information."""
    
    def __init__(self):
        """Initialize the DataEnricher."""
        self.stats = ProcessingStats()
    
    def join_company_with_family_tree(
        self,
        companies: List[Dict[str, Any]],
        family_tree: Dict[str, Dict[str, Any]]
    ) -> Tuple[pd.DataFrame, ProcessingStats]:
        """
        Join company records with family tree information (parent company enrichment).
        
        Args:
            companies: List of company records from data_blocks
            family_tree: Dictionary mapping DUNS to family tree information
            
        Returns:
            Tuple of (enriched DataFrame, processing stats)
        """
        logger.info(f"Starting join/enrichment for {len(companies)} companies")
        
        # Create DataFrame from companies
        df_companies = pd.DataFrame(companies)
        self.stats.total_companies = len(df_companies)
        
        logger.info(f"Created DataFrame with {len(df_companies)} records")
        
        # Initialize parent company columns
        df_companies['parent_company_id'] = None
        df_companies['parent_company_name'] = None
        df_companies['hierarchy_level'] = None
        
        # Join with family tree information
        for idx, row in df_companies.iterrows():
            duns = row['duns']
            
            try:
                if duns in family_tree:
                    family_info = family_tree[duns]
                    parent_duns = family_info.get('parent_duns')
                    
                    if parent_duns:
                        # Look up parent company name from the family tree or other companies
                        # For now, we just store the parent DUNS
                        df_companies.at[idx, 'parent_company_id'] = parent_duns
                        df_companies.at[idx, 'hierarchy_level'] = family_info.get('hierarchy_level')
                        self.stats.enriched_companies += 1
                        logger.debug(f"Enriched DUNS {duns} with parent {parent_duns}")
                    else:
                        self.stats.companies_without_parent += 1
                        logger.debug(f"No parent found for DUNS {duns}")
                else:
                    self.stats.companies_without_parent += 1
                    logger.debug(f"DUNS {duns} not found in family tree")
                    
                self.stats.companies_processed += 1
                
            except Exception as e:
                error_msg = f"Error enriching DUNS {duns}: {str(e)}"
                logger.error(error_msg)
                self.stats.add_error(duns, str(e), "enrichment")
        
        logger.info(
            f"Join/enrichment complete: "
            f"{self.stats.enriched_companies} enriched, "
            f"{self.stats.companies_without_parent} without parent, "
            f"{len(self.stats.errors)} errors"
        )
        
        return df_companies, self.stats
    
    def validate_enriched_data(self, df: pd.DataFrame) -> bool:
        """
        Validate the enriched dataset for completeness and integrity.
        
        Args:
            df: Enriched DataFrame
            
        Returns:
            True if validation passes, False otherwise
        """
        logger.info("Validating enriched data")
        
        checks = {
            "No duplicate DUNS": df['duns'].nunique() == len(df),
            "DUNS column not null": df['duns'].notna().all(),
            "primary_name column not null": df['primary_name'].notna().all(),
            "Expected columns present": all(col in df.columns for col in [
                'duns', 'primary_name', 'parent_company_id', 'hierarchy_level'
            ])
        }
        
        all_valid = True
        for check_name, result in checks.items():
            status = "PASS" if result else "FAIL"
            logger.info(f"  {check_name}: {status}")
            if not result:
                all_valid = False
        
        return all_valid

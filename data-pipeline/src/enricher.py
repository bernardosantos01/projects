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

        self.stats = ProcessingStats()
        
        # Create DataFrame from companies
        df_companies = pd.DataFrame(companies)
        self.stats.total_companies = len(df_companies)
        
        logger.info(f"Created DataFrame with {len(df_companies)} records")
        
        # Initialize parent company columns
        df_companies['parent_company_id'] = None
        df_companies['parent_company_name'] = None
        df_companies['hierarchy_level'] = None
        df_companies['global_ultimate_duns'] = None
        df_companies['family_tree_members_count'] = None
        df_companies['family_tree_roles'] = None

        company_names = {
            str(company.get('duns')): company.get('primary_name')
            for company in companies
            if company.get('duns') is not None
        }
        
        # Join with family tree information
        for idx, row in df_companies.iterrows():
            duns = str(row['duns']) if pd.notna(row['duns']) else None
            
            try:
                if duns is not None and duns in family_tree:
                    family_info = family_tree[duns]
                    parent_duns = family_info.get('parent_duns')
                    df_companies.at[idx, 'hierarchy_level'] = family_info.get('hierarchy_level')
                    df_companies.at[idx, 'global_ultimate_duns'] = family_info.get(
                        'global_ultimate_duns'
                    )
                    df_companies.at[idx, 'family_tree_members_count'] = family_info.get(
                        'family_tree_members_count'
                    )
                    df_companies.at[idx, 'family_tree_roles'] = family_info.get(
                        'family_tree_roles'
                    )
                    
                    if parent_duns:
                        parent_duns = str(parent_duns)
                        df_companies.at[idx, 'parent_company_id'] = parent_duns
                        parent_info = family_tree.get(parent_duns, {})
                        parent_name = parent_info.get('primary_name') or company_names.get(parent_duns)
                        df_companies.at[idx, 'parent_company_name'] = parent_name
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

        required_columns = [
            'duns', 'primary_name', 'parent_company_id', 'hierarchy_level',
            'global_ultimate_duns', 'family_tree_members_count', 'family_tree_roles'
        ]
        missing_columns = [column for column in required_columns if column not in df.columns]
        if missing_columns:
            logger.error("Missing required columns: %s", missing_columns)
            return False
        
        checks = {
            "No duplicate DUNS": df['duns'].nunique() == len(df),
            "DUNS column not null": df['duns'].notna().all(),
            "primary_name column not null": df['primary_name'].notna().all(),
            "No self-parent relationships": (
                df['parent_company_id'].isna()
                | (df['duns'].astype(str) != df['parent_company_id'].astype(str))
            ).all(),
            "Hierarchy levels are positive": (
                df['hierarchy_level'].isna() | (df['hierarchy_level'] >= 1)
            ).all(),
        }
        
        all_valid = True
        for check_name, result in checks.items():
            status = "PASS" if result else "FAIL"
            logger.info(f"  {check_name}: {status}")
            if not result:
                all_valid = False
        
        return all_valid

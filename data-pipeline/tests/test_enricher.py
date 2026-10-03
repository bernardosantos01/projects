"""Unit tests for data enrichment logic."""

import pytest
import pandas as pd
from typing import List, Dict, Any

from src.enricher import DataEnricher


class TestDataEnricher:
    """Test cases for the DataEnricher class."""
    
    @pytest.fixture
    def enricher(self):
        """Create a DataEnricher instance for testing."""
        return DataEnricher()
    
    @pytest.fixture
    def sample_companies(self) -> List[Dict[str, Any]]:
        """Create sample company data for testing."""
        return [
            {
                "duns": "103832861",
                "primary_name": "Harford Bank",
                "industry_code": "6022",
                "industry_description": "State commercial bank",
                "primary_address_country": "United States",
                "primary_address_region": "Maryland",
                "primary_address_locality": "Aberdeen",
                "postal_code": "21001-3200",
                "number_of_employees": 80,
                "yearly_revenue": 30282000.0,
                "control_ownership_type": "Publicly Traded Company",
                "operating_status": "Active",
                "parent_company_id": None,
                "parent_company_name": None,
            },
            {
                "duns": "987654321",
                "primary_name": "Subsidiary Bank",
                "industry_code": "6022",
                "industry_description": "State commercial bank",
                "primary_address_country": "United States",
                "primary_address_region": "New York",
                "primary_address_locality": "New York",
                "postal_code": "10001",
                "number_of_employees": 50,
                "yearly_revenue": 15000000.0,
                "control_ownership_type": "Subsidiary",
                "operating_status": "Active",
                "parent_company_id": None,
                "parent_company_name": None,
            },
        ]
    
    @pytest.fixture
    def sample_family_tree(self) -> Dict[str, Dict[str, Any]]:
        """Create sample family tree data for testing."""
        return {
            "103832861": {
                "duns": "103832861",
                "global_ultimate_duns": "103832861",
                "parent_duns": None,  # This is the ultimate parent
                "hierarchy_level": 1,
                "family_tree_members_count": 9,
            },
            "987654321": {
                "duns": "987654321",
                "global_ultimate_duns": "103832861",
                "parent_duns": "103832861",  # This company's parent
                "hierarchy_level": 2,
                "family_tree_members_count": 9,
            },
        }
    
    def test_join_company_with_family_tree_enriches_subsidiaries(
        self, enricher, sample_companies, sample_family_tree
    ):
        """Test that subsidiary companies are enriched with parent company information."""
        # Execute
        enriched_df, stats = enricher.join_company_with_family_tree(
            sample_companies, sample_family_tree
        )
        
        # Assert
        assert len(enriched_df) == 2, "Should have 2 companies in result"
        assert enriched_df.shape[1] > len(sample_companies[0]), "Should have added columns"
        
        # Check the subsidiary company was enriched
        subsidiary = enriched_df[enriched_df['duns'] == '987654321'].iloc[0]
        assert subsidiary['parent_company_id'] == '103832861', "Subsidiary should have parent DUNS"
        assert subsidiary['hierarchy_level'] == 2, "Subsidiary should have hierarchy level 2"
        
        # Check the ultimate company has no parent
        ultimate = enriched_df[enriched_df['duns'] == '103832861'].iloc[0]
        assert pd.isna(ultimate['parent_company_id']), "Ultimate should have no parent"
        
        # Check stats
        assert stats.enriched_companies == 1, "Should have enriched 1 company (the subsidiary)"
        assert stats.companies_without_parent == 1, "Should have 1 company without parent (the ultimate)"
    
    def test_join_handles_missing_family_tree_data(
        self, enricher, sample_companies
    ):
        """Test that companies without family tree data are handled gracefully."""
        # Use empty family tree
        empty_family_tree = {}
        
        # Execute
        enriched_df, stats = enricher.join_company_with_family_tree(
            sample_companies, empty_family_tree
        )
        
        # Assert
        assert len(enriched_df) == 2, "Should return all companies even with missing family tree data"
        assert enriched_df['parent_company_id'].isna().all(), "All parent_company_id should be None/NaN"
        assert stats.companies_without_parent == 2, "All companies should be marked as without parent"
        assert stats.enriched_companies == 0, "No companies should be enriched"
    
    def test_enriched_data_validation_passes_on_valid_data(
        self, enricher, sample_companies, sample_family_tree
    ):
        """Test that validation passes on well-formed enriched data."""
        # Setup
        enriched_df, _ = enricher.join_company_with_family_tree(
            sample_companies, sample_family_tree
        )
        
        # Execute
        is_valid = enricher.validate_enriched_data(enriched_df)
        
        # Assert
        assert is_valid is True, "Validation should pass on valid data"
    
    def test_join_maintains_all_company_attributes(
        self, enricher, sample_companies, sample_family_tree
    ):
        """Test that join operation preserves all original company attributes."""
        # Execute
        enriched_df, _ = enricher.join_company_with_family_tree(
            sample_companies, sample_family_tree
        )
        
        # Assert - check that all original attributes are present
        original_columns = set(sample_companies[0].keys())
        enriched_columns = set(enriched_df.columns)
        
        assert original_columns.issubset(enriched_columns), \
            "All original columns should be preserved"
        
        # Verify specific values haven't changed
        first_company = enriched_df.iloc[0]
        assert first_company['duns'] == sample_companies[0]['duns']
        assert first_company['primary_name'] == sample_companies[0]['primary_name']
        assert first_company['yearly_revenue'] == sample_companies[0]['yearly_revenue']

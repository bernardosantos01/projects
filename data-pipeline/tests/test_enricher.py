"""Focused unit test for company-family-tree enrichment."""

import pandas as pd

from src.enricher import DataEnricher


def test_join_uses_direct_parent_and_preserves_root_company():
    companies = [
        {"duns": "100000001", "primary_name": "Global Parent", "yearly_revenue": 1000.0},
        {"duns": "200000002", "primary_name": "Subsidiary", "yearly_revenue": 500.0},
    ]
    family_tree = {
        "100000001": {
            "duns": "100000001",
            "primary_name": "Global Parent",
            "global_ultimate_duns": "100000001",
            "parent_duns": None,
            "hierarchy_level": 1,
            "family_tree_members_count": 2,
            "family_tree_roles": ["Global Ultimate", "Parent/Headquarters"],
        },
        "200000002": {
            "duns": "200000002",
            "primary_name": "Subsidiary",
            "global_ultimate_duns": "100000001",
            "parent_duns": "100000001",
            "hierarchy_level": 2,
            "family_tree_members_count": 2,
            "family_tree_roles": ["Subsidiary"],
        },
    }

    enricher = DataEnricher()
    enriched, stats = enricher.join_company_with_family_tree(companies, family_tree)

    subsidiary = enriched.loc[enriched["duns"] == "200000002"].iloc[0]
    parent = enriched.loc[enriched["duns"] == "100000001"].iloc[0]

    assert len(enriched) == 2
    assert subsidiary["parent_company_id"] == "100000001"
    assert subsidiary["parent_company_name"] == "Global Parent"
    assert subsidiary["global_ultimate_duns"] == "100000001"
    assert subsidiary["hierarchy_level"] == 2
    assert subsidiary["family_tree_roles"] == ["Subsidiary"]
    assert subsidiary["yearly_revenue"] == 500.0
    assert pd.isna(parent["parent_company_id"])
    assert parent["hierarchy_level"] == 1
    assert stats.enriched_companies == 1
    assert stats.companies_without_parent == 1
    assert enricher.validate_enriched_data(enriched)

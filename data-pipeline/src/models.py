"""Data models and validation schemas."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CompanyRecord(BaseModel):
    """Pydantic model for company record validation."""
    duns: str
    primary_name: str
    industry_code: Optional[str] = None
    industry_description: Optional[str] = None
    primary_address_country: Optional[str] = None
    primary_address_region: Optional[str] = None
    primary_address_locality: Optional[str] = None
    postal_code: Optional[str] = None
    number_of_employees: Optional[int] = None
    yearly_revenue: Optional[float] = None
    control_ownership_type: Optional[str] = None
    operating_status: Optional[str] = None
    parent_company_id: Optional[str] = None
    parent_company_name: Optional[str] = None
    
    class Config:
        populate_by_name = True


class FamilyTreeMember(BaseModel):
    """Pydantic model for family tree member validation."""
    duns: str
    primary_name: str
    hierarchy_level: Optional[int] = None
    family_tree_roles: Optional[List[str]] = None
    parent_duns: Optional[str] = None
    
    class Config:
        populate_by_name = True


@dataclass
class ProcessingStats:
    """Statistics for data processing."""
    total_companies: int = 0
    companies_processed: int = 0
    enriched_companies: int = 0
    companies_with_errors: int = 0
    companies_without_parent: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_error(self, duns: str, error_message: str, error_type: str = "validation"):
        """Record an error during processing."""
        self.errors.append({
            "duns": duns,
            "error_message": error_message,
            "error_type": error_type
        })
        self.companies_with_errors += 1

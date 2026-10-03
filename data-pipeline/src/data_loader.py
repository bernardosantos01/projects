"""Data ingestion module for reading and parsing JSON files."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from pydantic import ValidationError

from .logger import setup_logger
from .models import CompanyRecord, FamilyTreeMember, ProcessingStats


logger = setup_logger(__name__)


class DataLoader:
    """Handles loading and parsing of JSON data files."""
    
    def __init__(self, data_dir: str):
        """
        Initialize DataLoader.
        
        Args:
            data_dir: Directory containing the JSON data files
        """
        self.data_dir = Path(data_dir)
        self.stats = ProcessingStats()
        
    def load_json_file(self, filename: str) -> Optional[Any]:
        """
        Load and parse a JSON file with error handling.
        
        Args:
            filename: Name of the JSON file to load
            
        Returns:
            Parsed JSON data or None if loading fails
        """
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            return None
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Successfully loaded {filename}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in {filename}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading {filename}: {str(e)}")
            return None
    
    def extract_company_info(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract and flatten company information from raw data_blocks.json.
        
        Args:
            raw_data: Raw company data from JSON
            
        Returns:
            Flattened company record or None if essential fields are missing
        """
        try:
            # Handle both single records and arrays
            if isinstance(raw_data, list) and len(raw_data) > 0:
                company = raw_data[0]
            else:
                company = raw_data
                
            # Extract primary industry code
            industry_code = None
            industry_desc = None
            if "primaryIndustryCode" in company:
                industry_code = company["primaryIndustryCode"].get("usSicV4")
                industry_desc = company["primaryIndustryCode"].get("usSicV4Description")
            
            # Extract employee count (try multiple sources)
            employees = None
            if "numberOfEmployees" in company and isinstance(company["numberOfEmployees"], list):
                # Prefer "Consolidated" scope
                for emp_record in company["numberOfEmployees"]:
                    if emp_record.get("informationScopeDescription") == "Consolidated":
                        employees = emp_record.get("value")
                        break
                # Fallback to first record if no consolidated found
                if employees is None:
                    employees = company["numberOfEmployees"][0].get("value")
            
            # Extract revenue
            yearly_revenue = None
            if "financials" in company and isinstance(company["financials"], list):
                for fin in company["financials"]:
                    if "yearlyRevenue" in fin:
                        revenue_list = fin["yearlyRevenue"]
                        if isinstance(revenue_list, list) and len(revenue_list) > 0:
                            yearly_revenue = revenue_list[0].get("value")
                            break
            
            # Extract address information
            address_country = None
            address_region = None
            address_locality = None
            postal_code = None
            
            if "primaryAddress" in company and company["primaryAddress"]:
                addr = company["primaryAddress"]
                if "addressCountry" in addr:
                    address_country = addr["addressCountry"].get("name")
                if "addressRegion" in addr:
                    address_region = addr["addressRegion"].get("name")
                if "addressLocality" in addr:
                    address_locality = addr["addressLocality"].get("name")
                postal_code = addr.get("postalCode")
            
            # Extract control ownership type
            control_ownership = None
            if "controlOwnershipType" in company:
                control_ownership = company["controlOwnershipType"].get("description")
            
            # Extract operating status
            operating_status = None
            if "dunsControlStatus" in company:
                status = company["dunsControlStatus"]
                if "operatingStatus" in status:
                    operating_status = status["operatingStatus"].get("description")
            
            return {
                "duns": company.get("duns"),
                "primary_name": company.get("primaryName"),
                "industry_code": industry_code,
                "industry_description": industry_desc,
                "primary_address_country": address_country,
                "primary_address_region": address_region,
                "primary_address_locality": address_locality,
                "postal_code": postal_code,
                "number_of_employees": employees,
                "yearly_revenue": yearly_revenue,
                "control_ownership_type": control_ownership,
                "operating_status": operating_status,
            }
            
        except Exception as e:
            logger.warning(f"Error extracting company info: {str(e)}")
            return None
    
    def extract_family_tree_info(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract parent company information from family_tree.json.
        
        Args:
            raw_data: Raw family tree data from JSON
            
        Returns:
            Dictionary with company and parent info or None if extraction fails
        """
        try:
            # Get the primary company (global ultimate)
            global_ultimate_duns = raw_data.get("globalUltimateDuns")
            
            # Extract family tree members - looking for parent relationships
            parent_duns = None
            family_members = raw_data.get("familyTreeMembers", [])
            
            if family_members and len(family_members) > 0:
                # The first member is typically the inquired company
                primary_member = family_members[0]
                primary_duns = primary_member.get("duns")
                
                # If this company is not the global ultimate, the global ultimate is the parent
                if primary_duns != global_ultimate_duns:
                    parent_duns = global_ultimate_duns
                
                return {
                    "duns": primary_duns,
                    "global_ultimate_duns": global_ultimate_duns,
                    "parent_duns": parent_duns,
                    "hierarchy_level": primary_member.get("corporateLinkage", {}).get("hierarchyLevel"),
                    "family_tree_members_count": raw_data.get("globalUltimateFamilyTreeMembersCount"),
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting family tree info: {str(e)}")
            return None
    
    def load_data_blocks(self, filename: str = "data_blocks.json") -> Tuple[List[Dict[str, Any]], ProcessingStats]:
        """
        Load and parse data_blocks.json.
        
        Args:
            filename: Name of the data blocks file
            
        Returns:
            Tuple of (list of company records, processing stats)
        """
        logger.info(f"Loading data blocks from {filename}")
        raw_data = self.load_json_file(filename)
        
        if raw_data is None:
            logger.error("Failed to load data blocks")
            return [], self.stats
        
        companies = []
        
        # Handle both single object and array formats
        records = raw_data if isinstance(raw_data, list) else [raw_data]
        self.stats.total_companies = len(records)
        
        for record in records:
            try:
                company_info = self.extract_company_info(record)
                if company_info:
                    # Validate with Pydantic model
                    validated = CompanyRecord(**company_info)
                    companies.append(validated.model_dump())
                    self.stats.companies_processed += 1
                else:
                    self.stats.add_error("unknown", "Failed to extract company information", "extraction")
            except ValidationError as e:
                duns = record.get("duns", "unknown")
                error_msg = f"Validation error: {str(e)}"
                logger.warning(f"Validation error for DUNS {duns}: {error_msg}")
                self.stats.add_error(duns, error_msg, "validation")
            except Exception as e:
                duns = record.get("duns", "unknown")
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"Error processing record for DUNS {duns}: {error_msg}")
                self.stats.add_error(duns, error_msg, "processing")
        
        logger.info(f"Processed {self.stats.companies_processed} companies from data blocks")
        return companies, self.stats
    
    def load_family_tree(self, filename: str = "family_tree.json") -> Tuple[Dict[str, Dict[str, Any]], ProcessingStats]:
        """
        Load and parse family_tree.json.
        
        Args:
            filename: Name of the family tree file
            
        Returns:
            Tuple of (dict mapping DUNS to family tree info, processing stats)
        """
        logger.info(f"Loading family tree from {filename}")
        raw_data = self.load_json_file(filename)
        
        if raw_data is None:
            logger.error("Failed to load family tree")
            return {}, self.stats
        
        family_tree = {}
        
        try:
            family_info = self.extract_family_tree_info(raw_data)
            if family_info:
                duns = family_info.get("duns")
                family_tree[duns] = family_info
                logger.info(f"Loaded family tree for DUNS {duns}")
            else:
                logger.warning("No valid family tree information extracted")
        except Exception as e:
            logger.error(f"Error processing family tree: {str(e)}")
        
        return family_tree, self.stats

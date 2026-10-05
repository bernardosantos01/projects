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
            primary_industry = company.get("primaryIndustryCode") or {}
            if isinstance(primary_industry, dict):
                industry_code = primary_industry.get("usSicV4")
                industry_desc = primary_industry.get("usSicV4Description")
            
            # Extract employee count (try multiple sources)
            employees = None
            if "numberOfEmployees" in company and isinstance(company["numberOfEmployees"], list):
                # Prefer "Consolidated" scope
                for emp_record in company["numberOfEmployees"]:
                    if (
                        isinstance(emp_record, dict)
                        and emp_record.get("informationScopeDescription") == "Consolidated"
                    ):
                        employees = emp_record.get("value")
                        break
                # Fallback to first record if no consolidated found
                if employees is None:
                    if company["numberOfEmployees"]:
                        first_employee_record = company["numberOfEmployees"][0]
                        if isinstance(first_employee_record, dict):
                            employees = first_employee_record.get("value")
            
            # Extract revenue
            yearly_revenue = None
            if "financials" in company and isinstance(company["financials"], list):
                for fin in company["financials"]:
                    if isinstance(fin, dict) and "yearlyRevenue" in fin:
                        revenue_list = fin["yearlyRevenue"]
                        if (
                            isinstance(revenue_list, list)
                            and revenue_list
                            and isinstance(revenue_list[0], dict)
                        ):
                            yearly_revenue = revenue_list[0].get("value")
                            break
            
            # Extract address information
            address_country = None
            address_region = None
            address_locality = None
            postal_code = None
            
            if isinstance(company.get("primaryAddress"), dict):
                addr = company["primaryAddress"]
                address_country_obj = addr.get("addressCountry") or {}
                address_region_obj = addr.get("addressRegion") or {}
                address_locality_obj = addr.get("addressLocality") or {}
                if isinstance(address_country_obj, dict):
                    address_country = address_country_obj.get("name")
                if isinstance(address_region_obj, dict):
                    address_region = address_region_obj.get("name")
                if isinstance(address_locality_obj, dict):
                    address_locality = address_locality_obj.get("name")
                postal_code = addr.get("postalCode")
            
            # Extract control ownership type
            control_ownership = None
            control_type = company.get("controlOwnershipType") or {}
            if isinstance(control_type, dict):
                control_ownership = control_type.get("description")
            
            # Extract operating status
            operating_status = None
            status = company.get("dunsControlStatus") or {}
            if isinstance(status, dict):
                operating_status_obj = status.get("operatingStatus") or {}
                if isinstance(operating_status_obj, dict):
                    operating_status = operating_status_obj.get("description")
            
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
    
    def extract_family_tree_info(
        self, raw_data: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract hierarchy information for every family-tree member.
        
        Args:
            raw_data: Raw family tree data from JSON
            
        Returns:
            Dictionary mapping each member DUNS to its hierarchy information
        """
        try:
            if not isinstance(raw_data, dict):
                logger.warning("Family tree JSON root is not an object")
                return {}

            global_ultimate_duns = raw_data.get("globalUltimateDuns")
            family_members = raw_data.get("familyTreeMembers", [])
            if not isinstance(family_members, list):
                logger.warning("familyTreeMembers is not a list")
                return {}

            family_tree: Dict[str, Dict[str, Any]] = {}
            member_count = raw_data.get("globalUltimateFamilyTreeMembersCount")

            for member in family_members:
                if not isinstance(member, dict):
                    logger.warning("Skipping malformed family tree member: expected object")
                    continue

                duns = member.get("duns")
                if not duns:
                    logger.warning("Skipping family tree member without DUNS")
                    continue

                corporate_linkage = member.get("corporateLinkage") or {}
                if not isinstance(corporate_linkage, dict):
                    corporate_linkage = {}

                parent = corporate_linkage.get("parent") or {}
                if not isinstance(parent, dict):
                    parent = {}

                roles = corporate_linkage.get("familytreeRolesPlayed") or []
                role_descriptions = [
                    role.get("description")
                    for role in roles
                    if isinstance(role, dict) and role.get("description")
                ] if isinstance(roles, list) else []

                family_tree[str(duns)] = {
                    "duns": str(duns),
                    "primary_name": member.get("primaryName"),
                    "global_ultimate_duns": global_ultimate_duns,
                    "parent_duns": parent.get("duns"),
                    "hierarchy_level": corporate_linkage.get("hierarchyLevel"),
                    "family_tree_members_count": member_count,
                    "family_tree_roles": role_descriptions,
                }

            return family_tree
            
        except Exception as e:
            logger.warning(f"Error extracting family tree info: {str(e)}")
            return {}
    
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
                if not isinstance(record, dict):
                    self.stats.add_error("unknown", "Company record is not an object", "validation")
                    continue

                company_info = self.extract_company_info(record)
                if company_info:
                    # Validate with Pydantic model
                    validated = CompanyRecord(**company_info)
                    companies.append(validated.model_dump())
                    self.stats.companies_processed += 1
                else:
                    self.stats.add_error("unknown", "Failed to extract company information", "extraction")
            except ValidationError as e:
                duns = record.get("duns", "unknown") if isinstance(record, dict) else "unknown"
                error_msg = f"Validation error: {str(e)}"
                logger.warning(f"Validation error for DUNS {duns}: {error_msg}")
                self.stats.add_error(duns, error_msg, "validation")
            except Exception as e:
                duns = record.get("duns", "unknown") if isinstance(record, dict) else "unknown"
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
            family_tree = self.extract_family_tree_info(raw_data)
            for duns, family_info in list(family_tree.items()):
                try:
                    validated = FamilyTreeMember(**family_info)
                    family_tree[duns] = validated.model_dump()
                except ValidationError as e:
                    logger.warning("Skipping invalid family tree member %s: %s", duns, e)
                    family_tree.pop(duns)

            if family_tree:
                logger.info("Loaded %d family tree members", len(family_tree))
            else:
                logger.warning("No valid family tree information extracted")
        except Exception as e:
            logger.error(f"Error processing family tree: {str(e)}")
        
        return family_tree, self.stats

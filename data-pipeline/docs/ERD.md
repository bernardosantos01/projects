# Entity-Relationship Diagram (ERD)

This directory contains the Entity-Relationship Diagram for the Company Data Pipeline in multiple formats.

## Files

- `erd.svg` - Vector format (scalable, best for web and printing)
- `erd.png` - Raster format (good for embedding in documents)

## Diagram Overview

The ERD shows the normalized relational model for the data pipeline with the following key entities:

- **COMPANIES** - Core company table with business identifiers and attributes
- **COMPANY_ADDRESSES** - Company address records with distinct roles
- **COMPANY_INDUSTRY_CODES** - Industry classifications from multiple systems
- **COMPANY_FINANCIAL_STATEMENTS** - Financial reporting period data
- **COMPANY_FINANCIAL_ITEMS** - Individual financial line items
- **COMPANY_EMPLOYEE_OBSERVATIONS** - Employment data with scope tracking
- **COMPANY_CONTACTS** - Phone, email, and website contact records
- **COMPANY_REGISTRATION_NUMBERS** - Business registration identifiers
- **COMPANY_STOCK_EXCHANGES** - Stock ticker and exchange information
- **COMPANY_OWNERSHIP_LINKS** - Self-referencing parent/subsidiary relationships
- **FAMILY_TREE_RESPONSES** - Captured hierarchy snapshots with metadata
- **FAMILY_TREE_MEMBERS** - Individual member entries in hierarchy responses
- **FAMILY_TREE_MEMBER_ROLES** - Role assignments for family tree members

## Relationships

All child tables maintain one-to-many relationships with their parent tables using foreign keys:
- Primary key: `duns` (company DUNS number)
- Foreign key references link child records back to companies
- `COMPANY_OWNERSHIP_LINKS` is a self-referencing table for parent-subsidiary relationships
- Family tree tables form a hierarchy: `FAMILY_TREE_RESPONSES` → `FAMILY_TREE_MEMBERS` → `FAMILY_TREE_MEMBER_ROLES`

See the main README for detailed field descriptions and modeling rationale.

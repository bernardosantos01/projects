# Company Data Pipeline

A production-ready Python data pipeline for ingesting, enriching, and processing company information from multiple data sources.

## Overview

This pipeline processes company data from two primary sources:
- `data_blocks.json`: detailed company information including addresses, classifications, financials, and hierarchical relationships
- `family_tree.json`: corporate hierarchy and parent-subsidiary linkages

The pipeline performs a join/enrichment operation to attach parent company information to each company record and outputs the enriched dataset in Parquet format for efficient querying and analysis.

## Architecture

### Source JSON data model

The JSON files contain a nested D&B company profile, not just the small set of fields in the first version of this ERD. The following inventory describes the significant field groups present in the supplied `data_blocks.json` and `family_tree.json` examples. Some values can be null, empty, or absent, and arrays can contain zero or multiple entries.

| Source group | Example source fields | Meaning and modeling notes |
| --- | --- | --- |
| Company identity | `duns`, `primaryName`, `registeredName`, `legalEntityIdentifier` | Business identifiers and names. DUNS is the natural company key; registered names and LEIs should not be collapsed into it. |
| Legal and entity form | `businessEntityType`, `legalForm`, `registeredDetails.legalForm`, `charterType`, `incorporatedDate`, `registrationNumbers` | Legal classification, incorporation data, and potentially multiple jurisdiction-specific identifiers. `registrationNumbers` is a repeating group. |
| Operating status | `dunsControlStatus.operatingStatus`, `operatingSubStatus`, `detailedOperatingStatus`, `recordClass`, `isMarketable`, `isMailUndeliverable`, `isTelephoneDisconnected`, `startDate` | Operational state and record-quality/contact flags. Status objects include descriptions, codes, and sometimes effective dates. |
| Ownership and corporate linkage | `controlOwnershipType`, `isStandalone`, `corporateLinkage.familytreeRolesPlayed`, `corporateLinkage.hierarchyLevel`, `corporateLinkage.globalUltimateFamilyTreeMembersCount`, `corporateLinkage.globalUltimate`, `corporateLinkage.domesticUltimate`, `corporateLinkage.parent`, `corporateLinkage.headQuarter`, `corporateLinkage.branches` | Ownership type and distinct relationship roles. A record can be the global ultimate, domestic ultimate, and parent/headquarters simultaneously. `parent` and `branches` can be empty even when family-tree response metadata reports a wider family. |
| Addresses | `primaryAddress`, `mailingAddress`, `registeredAddress`, `multilingualPrimaryAddress`, `multilingualRegisteredAddress` | Distinct address roles. Address objects can include country and ISO code, region and subdivision code, county, locality, street lines, postal code/route, PO box, latitude/longitude, geographic precision, statistical area, and manufacturing-location flags. Preserve address type and source instead of combining addresses into one row. |
| Industry classifications | `primaryIndustryCode`, `industryCodes`, `activities`, `unspscCodes` | Multiple classification systems and code types may describe one company. `industryCodes` includes code, description, classification-system description/code, and priority. UNSPSC is a separate classification. |
| Financial statements | `financials`, `latestFiscalFinancials`, `globalUltimate.financials`, `domesticUltimate.financials` | Revenue and detailed statement data, with fiscal dates, duration, currency/units, scope, reliability, audit/final/restatement flags, source/provider, explanations, ratios, and statement items. `latestFiscalFinancials.overview` carries balance-sheet and income-statement measures such as cash, assets, liabilities, capital, net worth, sales, operating profit, profit before/after tax, dividends, and working capital. |
| Employment | `numberOfEmployees`, `globalUltimate.numberOfEmployees`, `domesticUltimate.numberOfEmployees` | Employee observations can be for headquarters or consolidated scope and may include dates, reliability, ranges, and categories. Scope must be retained to interpret the value. |
| Contact and web | `telephone`, `email`, `websiteAddress`, `certifiedEmail` | Repeating phone, email, and web records with country codes or domain information. These are not scalar company attributes. |
| Market and trading | `stockExchanges`, `standardizedStockExchanges`, `isFortune1000Listed`, `isForbesLargestPrivateCompaniesListed` | Listing flags and exchange/ticker records, including exchange country and primary-listing marker. |
| Other classifications and scores | `organizationSizeCategory`, `employerDesignation`, `businessTrustIndex`, `isAgent`, `isImporter`, `isExporter`, `isSmallBusiness`, `isNonClassifiedEstablishment` | Supplemental classification, derived scores, and business-role indicators; several are nullable. |
| Multilingual and descriptive data | `summary`, `multilingualPrimaryName`, `multilingualRegisteredNames`, `multilingualTradestyleNames`, `multiLingualSearchNames`, `preferredLanguage`, `subjectComments` | Optional localized names and descriptions, language metadata, and comments. These may be empty arrays in a particular source record. |
| Other source groups | `banks`, `activities`, `industrialPlantsCount`, `fiscalYearEnd`, `defaultCurrency`, `securitiesReportID` | Additional operational, activity, plant, fiscal-calendar, and source-specific attributes. |
| Source and transaction metadata | `transactionDetail`, `inquiryDetail`, `links`, `investigationDate`, `tsrReportDate`, `controlOwnershipDate` | Request, response, and effective-date context. Store this separately from enduring company identity when retaining source lineage. |
| Family-tree response | `globalUltimateDuns`, `globalUltimateFamilyTreeMembersCount`, `branchesExcludedMembersCount`, `familyTreeMembers`, `links` | Response-level hierarchy metadata plus a repeating set of members. Each member can include identity, address, industry, employees, financials, hierarchy level, and `corporateLinkage.familytreeRolesPlayed`. |

The nested JSON is the source contract. A relational design must turn nested objects into columns and repeated arrays into child rows, while retaining identifiers, classification-system context, effective dates, scope, currency, and provenance. Flattening everything into one row would repeat company-level attributes and make array-valued fields ambiguous.

Examples of nested values that affect the schema:

- An address is not a single string. `primaryAddress.addressRegion` can itself carry a display name, abbreviation, ISO subdivision name/code, and administrative code; `streetAddress` has separate lines; `geographicalPrecision` has a description and D&B code.
- An industry code's value is only meaningful together with its classification system. For example, code `6022` is a US SIC code, while `522110` in the same array is a NAICS code. Store system/type and code together; do not treat equal code strings from different systems as identical.
- Revenue is an array of observations with `value` and `currency`, under a statement with a date, information scope, reliability, and units. The `latestFiscalFinancials.overview` holds many separate named measures, and `financialRatios.statementItems` is another repeated group with an `itemKey` and value.
- Employee values are separate observations. The sample distinguishes `Headquarters Only (Employs Here)` from `Consolidated`; storing only an integer loses that business meaning.
- Family-tree roles are multi-valued. In the sample, one member can have `Global Ultimate`, `Domestic Ultimate`, and `Parent/Headquarters` roles. These are role records, not mutually exclusive company types.

### Proposed normalized relational model

This is the target relational design for preserving the meaningful source groups. It is a data model proposal, not a claim that the current Python pipeline writes all these tables.

| Table | Key fields and purpose |
| --- | --- |
| `companies` | `duns` (PK), names, LEI, entity/legal form, country, start/incorporation dates, operating-status attributes, ownership type, standalone/listing flags. One row per company identity. |
| `company_addresses` | `address_id` (PK), `duns` (FK), address role (`primary`, `mailing`, `registered`), address lines, locality, county, region, country, postal code, coordinates, precision, manufacturing flag, source/effective dates. Many addresses per company. |
| `company_industry_codes` | `industry_code_id` (PK), `duns` (FK), code, description, classification-system name/code, priority, primary marker. Many codes per company, including distinct systems such as NAICS, SIC, NACE, ISIC, D&B classifications, and UNSPSC. |
| `company_financial_statements` | `financial_statement_id` (PK), `duns` (FK), fiscal from/to dates, duration, information scope, reliability, currency, units, audit/final/restated flags, provider and source metadata. One row per statement/scope. |
| `company_financial_items` | `financial_statement_id` (FK), item key/code, item description, value, currency/units. Child rows for revenue, assets, liabilities, ratios, and other statement measures. |
| `company_employee_observations` | `employee_observation_id` (PK), `duns` (FK), value/range, observation date, information scope, reliability, employee category. Keeps headquarters and consolidated counts distinct. |
| `company_contacts` | `contact_id` (PK), `duns` (FK), contact type, value, country/ISD code, domain, source. Child rows for telephone, email, and website entries. |
| `company_registration_numbers` | `registration_id` (PK), `duns` (FK), number, type/code, class, preferred flag, jurisdiction/location. One company can have several identifiers. |
| `company_stock_exchanges` | `listing_id` (PK), `duns` (FK), ticker, exchange, country, primary marker. |
| `company_ownership_links` | `duns` (FK), related DUNS, relationship role (`parent`, `domestic_ultimate`, `global_ultimate`, etc.), hierarchy level, source/effective dates. Supports explicit linkage without treating ultimate parent and immediate parent as interchangeable. |
| `family_tree_responses` | `response_id` (PK), inquiry DUNS, global ultimate DUNS, reported member count, excluded branch count, transaction ID/timestamp, source links. One row per captured family-tree response. |
| `family_tree_members` | `response_id` (FK), member DUNS, hierarchy level, member identity/name and response-level attributes. A response has many members. |
| `family_tree_member_roles` | `response_id` and member DUNS (FK), role code/description. A member can play multiple roles, such as global ultimate, domestic ultimate, or parent/headquarters. |

Important relationships:

- `companies.duns` is the parent key for company-specific child tables.
- Company-to-address, industry-code, financial-statement, employee-observation, contact, registration, and stock-listing relationships are one-to-many.
- `company_ownership_links` is a self-reference between companies. Keep the relationship role so immediate parent, domestic ultimate, and global ultimate are distinguishable.
- `family_tree_responses` has many `family_tree_members`; each member can have many roles.
- Family-tree observations should retain response identity and timestamp because the hierarchy is a captured source response and can change over time.

ERD overview (the arrows indicate one-to-many relationships):

```text
COMPANIES (1) ------< (many) COMPANY_ADDRESSES
COMPANIES (1) ------< (many) COMPANY_INDUSTRY_CODES
COMPANIES (1) ------< (many) COMPANY_FINANCIAL_STATEMENTS (1) ------< (many) COMPANY_FINANCIAL_ITEMS
COMPANIES (1) ------< (many) COMPANY_EMPLOYEE_OBSERVATIONS
COMPANIES (1) ------< (many) COMPANY_CONTACTS
COMPANIES (1) ------< (many) COMPANY_REGISTRATION_NUMBERS
COMPANIES (1) ------< (many) COMPANY_STOCK_EXCHANGES
COMPANIES (1) ------< (many) COMPANY_OWNERSHIP_LINKS >------ (1) COMPANIES (related DUNS)
COMPANIES (1) ------< (many) FAMILY_TREE_RESPONSES
FAMILY_TREE_RESPONSES (1) ------< (many) FAMILY_TREE_MEMBERS
FAMILY_TREE_MEMBERS (1) ------< (many) FAMILY_TREE_MEMBER_ROLES
```

Each company child table stores one repeating source group as rows rather than embedding arrays in the company record. The ERD is a logical target; primary/foreign-key enforcement and physical database DDL are not part of the current Parquet pipeline.

### What the current pipeline actually outputs

The current implementation does **not** create the normalized tables above. It writes one flat Parquet table with these selected fields:

| Parquet column | Current extraction |
| --- | --- |
| `duns`, `primary_name` | Company DUNS and primary name. |
| `industry_code`, `industry_description` | `primaryIndustryCode.usSicV4` and its description only; other entries in `industryCodes` are not emitted. |
| `primary_address_country`, `primary_address_region`, `primary_address_locality`, `postal_code` | A subset of `primaryAddress`; mailing and registered addresses and street/coordinate details are not emitted. |
| `number_of_employees` | Prefers the consolidated employee observation, otherwise takes the first observation. Scope/date/reliability are not retained in this column. |
| `yearly_revenue` | Takes the first value from the first usable `financials[].yearlyRevenue[]`; statement date, currency, scope, and other financial items are not emitted. |
| `control_ownership_type`, `operating_status` | Descriptions from the corresponding nested objects. |
| `parent_company_id`, `parent_company_name`, `hierarchy_level` | Direct parent DUNS and name, plus the hierarchy level from the matching family-tree member. Root companies have no direct parent. |
| `global_ultimate_duns`, `family_tree_members_count`, `family_tree_roles` | Global ultimate identifier, response-reported family size, and role descriptions for the matching member. |

The loader treats an object-form `data_blocks.json` as one company record and iterates over every item if the root is an array. It indexes every valid entry in `familyTreeMembers[]` by DUNS and uses that member's `corporateLinkage.parent.duns` as the direct parent. It does not manufacture company rows for family members absent from `data_blocks.json`; it enriches the company records provided by that file. Thus one source company record still produces one output row, while a company present as a subsidiary member can receive its direct parent even when the global ultimate is several levels above it.

Accordingly, the current Parquet is a compact enriched company extract, not a complete representation of the source JSON or the normalized ERD. The schema proposal captures information available in the source; implementing those additional normalized tables remains outside the current Parquet pipeline.

### Design decisions

1. Use DUNS as the company business key, while keeping other identifiers in their own child table.
2. Model address and classification roles explicitly; a company's mailing address is not necessarily its primary location, and industry codes belong to different code systems.
3. Keep financial statement date, currency, units, scope, and reliability with financial values so comparisons are meaningful.
4. Preserve employee scope and observation date rather than mixing headquarters and consolidated counts.
5. Distinguish immediate parent relationships from domestic/global ultimate relationships.
6. Retain source-response identifiers and timestamps for hierarchy and other time-varying facts.
7. Treat the current one-row-per-input-company Parquet as a practical task output; do not imply it contains all normalized entities listed above.

## Project structure

```text
data-pipeline/
├── main.py
├── requirements.txt
├── .gitignore
├── README.md
├── IMPLEMENTATION_SUMMARY.md
├── output/
├── src/
│   ├── __init__.py
│   ├── logger.py
│   ├── models.py
│   ├── data_loader.py
│   ├── enricher.py
│   ├── pipeline.py
│   └── view_output.py
└── tests/
    ├── __init__.py
    └── test_enricher.py
```

## Installation

### Prerequisites
- Python 3.9+
- pip or conda

### Setup

1. Go to the project directory:

```bash
cd ../data-pipeline
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic pipeline execution

Run the pipeline on a directory containing `data_blocks.json` and `family_tree.json`:

```bash
python main.py --input /path/to/data/directory
```

### Advanced options

```bash
python main.py \
  --input /path/to/data/directory \
  --output ./output \
  --filename enriched_companies.parquet \
    --validate
```

Parameters:
- `--input`: required directory with the JSON files
- `--output`: output directory for parquet files
- `--filename`: output parquet filename
- `--validate` / `--no-validate`: enable or disable data checks before saving (enabled by default)

### Read the output

```python
import pandas as pd

df = pd.read_parquet('output/enriched_companies.parquet')
print(df.head())
print(df.columns)
```

## Features

### Data ingestion
- Robust JSON parsing with error recovery
- Support for nested data structures
- Null and missing value handling
- Type validation with Pydantic models

### Data processing
- Company-family tree joins
- Parent company enrichment
- Hierarchy level assignment
- Data quality checks and logging

### Data quality
- Schema validation
- Duplicate detection
- Completeness checks
- Error summary reporting

### Output
- Parquet format with Snappy compression
- Efficient columnar storage
- Data type preservation

## Testing

Run the unit tests:

```bash
pytest tests/test_enricher.py -v
```

The single focused pytest test checks direct-parent enrichment, root-company handling, hierarchy metadata, source-column preservation, processing counts, and output validation. A GitHub Actions workflow at the repository root (`.github/workflows/data-pipeline-tests.yml`) installs the pinned dependencies and runs this test on pushes and pull requests.

## Logging and error handling

The pipeline includes logging for:
- file loading issues
- JSON parsing problems
- validation failures
- missing parent-company relationships
- final pipeline summary metrics

This makes it easier to identify and address bad records without stopping the full process.

The pipeline also runs output checks for unique and non-null DUNS values, non-null company names, valid hierarchy levels, and absence of self-parent links. When validation is enabled (the default), failed checks prevent the Parquet file from being written. Malformed individual records are logged and counted; missing or unusable family-tree data leaves company records in the output with null hierarchy fields.

## Handling large datasets

For production-scale workloads, two concrete code changes would be useful without changing the underlying infrastructure:

### 1. Stream large JSON arrays

The current loader uses `json.load`, which materializes the full JSON document in memory. The provided files are nested JSON documents, not JSON Lines, so a line-by-line `json.loads` loop is not valid for them. Use a streaming parser such as `ijson` to iterate over each company record in an array-form `data_blocks.json` and each `familyTreeMembers.item` entry in `family_tree.json`. Build a DUNS-to-parent lookup as the hierarchy stream is read, then enrich and emit company records in bounded batches. If source producers can be changed, newline-delimited JSON is another option, but it is not the current input format.

### 2. Write Parquet incrementally

Instead of constructing one DataFrame for the entire input, convert each enriched batch to an Arrow table and append it with `pyarrow.parquet.ParquetWriter`. This bounds memory use while retaining Parquet output and the existing infrastructure. Keep validation counters (duplicate DUNS, missing required identifiers, malformed rows, parent match counts) across batches and fail or report according to explicit thresholds.

## Error handling

The processing logic handles:
- missing files
- malformed JSON
- missing fields
- unexpected data types
- missing family tree entries

Errors are logged and summarized instead of crashing the whole pipeline.

## Version control

This project is ready for Git use. A typical workflow is:

```bash
git init
git add .
git commit -m "Initial implementation"
```

## License

Confidential - for authorized use only.

## Contact

For questions or issues, contact your HR representative.

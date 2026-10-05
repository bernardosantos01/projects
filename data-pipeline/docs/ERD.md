# Entity-Relationship Diagram (ERD)

The **proposed normalized relational model** for the Company Data Pipeline is shown in [`erd.svg`](erd.svg). Open or download the SVG for a scalable diagram, or export it to PNG using a browser, Inkscape, or another vector-graphics application.

> The ERD is a logical schema proposal. The current pipeline writes a flat enriched Parquet table; it does not create these normalized tables.

The diagram covers the company entity and its repeating detail tables, financial statements and line items, self-referencing ownership links, and the captured family-tree response/member/role hierarchy. For full field descriptions and modeling rationale, see the **Proposed normalized relational model** section in [`../README.md`](../README.md).

## Entities and why they are separate

The entities below normalize the nested source data. Primary and foreign keys are shown explicitly. DUNS values must be stored as text, not numbers, so leading zeros are preserved.

### 1. COMPANIES

**Attributes to draw:**

- PK `duns` (text)
- `primary_name`, `registered_name`, `legal_entity_identifier`
- `business_entity_type`, `legal_form`, `country_code`
- `start_date`, `incorporated_date`
- `operating_status`, `control_ownership_type`, `is_standalone`

**Example:** Harford Bank has DUNS `103832861`, primary name Harford Bank, and country US. Its `data_blocks.json` also gives `registeredName` as HARFORD BANK. The DUNS identifies the company; the names and status describe it.

### 2. COMPANY_ADDRESSES

**Attributes to draw:**

- PK `address_id`
- FK `duns`
- `address_role` (primary, mailing, registered)
- `street_line_1`, `street_line_2`, `locality`, `county`, `region`
- `country_code`, `postal_code`, `latitude`, `longitude`, `geographical_precision`

**Example:** Harford Bank's primary address is 8 W Bel Air Ave, Aberdeen, Maryland, ZIP 21001-3200. Its mailing address is a PO Box - PO Box 640, ZIP 21001-0640. These are different address roles and values, so they should be separate address rows rather than one company address.

### 3. COMPANY_INDUSTRY_CODES

**Attributes to draw:**

- PK `industry_code_id`
- FK `duns`
- `code`, `description`, `classification_system`, `classification_system_code`
- `priority`, `is_primary`

**Example:** Harford Bank has codes from multiple systems: NAICS 522110 (Commercial Banking), US SIC 6022 (State commercial bank), and ISIC 6419. The code alone is not enough to interpret the classification; keep its system with it. Microsoft's array also contains repeated codes at different priorities, so a company can have multiple classification rows.

### 4. COMPANY_FINANCIAL_STATEMENTS

**Attributes to draw:**

- PK `financial_statement_id`
- FK `duns`
- `statement_from_date`, `statement_to_date`, `duration`
- `information_scope`, `reliability`, `currency`, `units`
- `is_audited`, `is_final`, `is_restated`

**Example:** Harford Bank's financials entry is for the year ending 2023-12-31; it is Individual scope, Actual reliability, and uses USD and single units. Those details describe the statement and give context to its values.

### 5. COMPANY_FINANCIAL_ITEMS

**Attributes to draw:**

- PK `financial_item_id` (or a composite key including the statement and item code)
- FK `financial_statement_id`
- `item_code`, `item_description`, `value`, `currency`, `units`

**Example:** Harford's latest fiscal financials include separate values such as cash and liquid assets 34,261,000, total assets 665,617,000, sales revenue 30,282,000, and operating profit 9,484,000. These are many named values for one statement, so model them as item rows related to that statement.

### 6. COMPANY_EMPLOYEE_OBSERVATIONS

**Attributes to draw:**

- PK `employee_observation_id`
- FK `duns`
- `value`, `minimum_value`, `maximum_value`, `observation_date`
- `information_scope`, `reliability`, `employee_category`

**Example:** Harford Bank has two observations: 35 employees at Headquarters Only (Employs Here) scope and 80 at Consolidated scope. Keeping them as separate rows preserves what each number measures.

### 7. COMPANY_CONTACTS

**Attributes to draw:**

- PK `contact_id`
- FK `duns`
- `contact_type`, `value`, `country_code`, `isd_code`, `domain_name`

**Example:** Harford Bank has telephone 4102725000 with ISD code 1, plus website www.harfordbank.com with domain harfordbank.com. They are different contact types, and the JSON represents contacts as arrays, so one company may have multiple contact rows.

### 8. COMPANY_REGISTRATION_NUMBERS

**Attributes to draw:**

- PK `registration_id`
- FK `duns`
- `registration_number`, `type_description`, `type_code`
- `registration_class`, `is_preferred`, `registration_location`

**Example:** Harford Bank has multiple identifiers: CAGE code 8W3P8, business registration number D06363931, and a government UEI. One company can therefore have several registration numbers of different types.

### 9. COMPANY_STOCK_EXCHANGES

**Attributes to draw:**

- PK `listing_id`
- FK `duns`
- `ticker_name`, `exchange_name`, `exchange_country`, `is_primary`

**Example:** Harford Bank has an OTC listing, OTC:HFBK, marked primary. Microsoft has many listing records, including NASDAQ:MSFT and listings on other exchanges. Putting listings in child rows allows multiple tickers per company.

### 10. COMPANY_OWNERSHIP_LINKS

**Attributes to draw:**

- PK `ownership_link_id` (or a composite key including the companies, role, and effective date)
- FK `company_duns` -> `COMPANIES.duns`
- FK `related_company_duns` -> `COMPANIES.duns`
- `relationship_role`, `hierarchy_level`, `effective_date`, `source`

**Example:** In the Microsoft family tree, Microsoft DUNS 081466849 is at level 1. Microsoft Japan DUNS 690763115 is at level 2 and names 081466849 as its parent. Draw two relationships from COMPANIES to this entity - one for the company and one for the related company. Keep the role so a direct parent is distinguishable from a domestic or global ultimate.

### 11. FAMILY_TREE_RESPONSES

**Attributes to draw:**

- PK `response_id`
- FK `inquiry_duns` -> `COMPANIES.duns`
- FK `global_ultimate_duns` -> `COMPANIES.duns` (when that company is present in COMPANIES)
- `transaction_id`, `transaction_timestamp`, `reported_member_count`
- `excluded_branch_count`, `exclusion_criteria`

**Example:** Harford Bank's family-tree response was queried for DUNS 103832861; it reports the same DUNS as global ultimate, a member count of 9, and 1 excluded branch. Its transaction timestamp is 2025-01-23T11:58:27.050Z. This belongs on a response entity because it describes that particular captured response, not an unchanging company fact.

### 12. FAMILY_TREE_MEMBERS

**Attributes to draw:**

- PK (`response_id`, `member_duns`)
- FK `response_id` -> `FAMILY_TREE_RESPONSES.response_id`
- `member_duns`, `member_name`, `hierarchy_level`
- Optional captured snapshot fields, if you need to retain them

**Example:** Microsoft's response lists Microsoft at level 1 and Microsoft Japan at level 2. Bain Capital's response lists BC Mountain Holdings, Inc. at level 2 with parent DUNS 199882911. The response key matters because a member can appear in different family-tree snapshots over time. Use `member_duns` as a foreign key to COMPANIES only when that company's record is loaded; otherwise keep the DUNS and name as response-member data.

### 13. FAMILY_TREE_MEMBER_ROLES

**Attributes to draw:**

- PK (`response_id`, `member_duns`, `role_code`)
- FK (`response_id`, `member_duns`) -> `FAMILY_TREE_MEMBERS`
- `role_code`, `role_description`

**Example:** Microsoft's root member has three roles: Global Ultimate, Domestic Ultimate, and Parent/Headquarters. Those roles can coexist, so draw a one-to-many relationship from a family-tree member to role rows - not a single role column on the member.


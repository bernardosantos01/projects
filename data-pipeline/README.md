# Company Data Pipeline

A Python application that reads company profiles and family-tree data from JSON, enriches company records with hierarchy information, validates the result, and writes Parquet output.

The proposed schema diagram and its explanation are located under [docs](docs/).

## Implementation

The pipeline processes a directory containing `data_blocks.json` and `family_tree.json` in one end-to-end flow:

1. **Ingest:** `src/data_loader.py` loads both JSON files. Company input may be a single object or a list; family-tree members are read from `familyTreeMembers`.
2. **Extract and validate:** Selected company fields are flattened and validated with Pydantic. DUNS and primary name are required; optional missing fields remain null. Malformed records are logged and counted rather than silently treated as valid.
3. **Build hierarchy lookup:** Each valid family-tree member is indexed by DUNS. The lookup retains the member's direct parent from `corporateLinkage.parent.duns`, hierarchy level, global ultimate DUNS, member roles, and reported family size.
4. **Join/enrich:** The company DUNS is matched to the hierarchy lookup. The output gains `parent_company_id`, `parent_company_name`, `hierarchy_level`, `global_ultimate_duns`, `family_tree_members_count`, and `family_tree_roles`. Root companies remain parentless. The pipeline enriches companies found in `data_blocks.json`; it does not add extra company rows for other family-tree members.
5. **Check and export:** Data checks cover duplicate or null DUNS, null company names, positive hierarchy levels when present, and self-parent links. Validation is enabled by default and prevents writing when checks fail. The valid result is written as Snappy-compressed Parquet.

### Output contents

The Parquet output contains one row for each valid input company record. The selected fields are:

- Identity: `duns`, `primary_name`
- Primary classification: `industry_code`, `industry_description`
- Primary address subset: `primary_address_country`, `primary_address_region`, `primary_address_locality`, `postal_code`
- Selected measures: `number_of_employees`, `yearly_revenue`
- Company descriptors: `control_ownership_type`, `operating_status`
- Hierarchy enrichment: `parent_company_id`, `parent_company_name`, `hierarchy_level`, `global_ultimate_duns`, `family_tree_members_count`, `family_tree_roles`

The input JSON contains many more nested fields and repeated groups, including additional addresses, classification systems, financial statement details and ratios, employee scopes, registration numbers, contacts, and stock listings. The current output is a compact enriched extract; it does not preserve or normalize every source field.

### Code layout

- `main.py`: command-line entry point.
- `src/data_loader.py`: input reading, extraction, and input validation.
- `src/enricher.py`: family-tree join and output checks.
- `src/models.py`: Pydantic data models and processing statistics.
- `src/pipeline.py`: pipeline orchestration and Parquet writing.
- `src/view_output.py`: command-line Parquet preview utility.
- `tests/test_enricher.py`: focused pytest test for enrichment.

## Setup and usage

Use Python 3.9 or newer. From the `data-pipeline` directory:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the pipeline with a directory containing both source JSON files:

```bash
python main.py --input "/path/to/company-data"
```

Optional output settings:

```bash
python main.py \
  --input "/path/to/company-data" \
  --output ./output \
  --filename enriched_companies.parquet
```

Validation is enabled by default. Use `--no-validate` to disable output checks. The default output path is `output/enriched_companies.parquet`.

Preview the output:

```bash
python -m src.view_output --file output/enriched_companies.parquet --limit 10
```

## Quality checks and testing

Logging covers file loading, JSON parsing, record validation, enrichment, output checks, and pipeline completion. Individual malformed company records are skipped and included in processing error statistics. If no valid companies are loaded, or output validation fails, the pipeline does not write a Parquet file. Missing or unusable family-tree data leaves hierarchy fields null while retaining valid company rows.

Run the single enrichment unit test:

```bash
python -m pytest -q
```

It verifies direct-parent enrichment, root-company handling, metadata and source-column preservation, processing statistics, and output validation.

## Scaling

The current implementation uses `json.load` and pandas, so it keeps each input document and the enriched DataFrame in memory. Two code changes would handle larger datasets without changing infrastructure:

1. Use a streaming parser such as `ijson` to iterate over the nested JSON company records and family-tree members. These inputs are not JSON Lines, so line-by-line parsing is not appropriate unless the source format changes.
2. Enrich and validate bounded batches, then append Arrow tables with `pyarrow.parquet.ParquetWriter` instead of building the complete DataFrame in memory.

These scale improvements are documented proposals and are not implemented yet.

## Version control

Track source code, tests, requirements, and documentation with Git. `.gitignore` excludes virtual environments, local environment files, caches, and generated Parquet output. Do not commit the virtual environment or generated output artifacts.

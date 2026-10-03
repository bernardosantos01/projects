# Company Data Pipeline

A production-ready Python data pipeline for ingesting, enriching, and processing company information from multiple data sources.

## Overview

This pipeline processes company data from two primary sources:
- `data_blocks.json`: detailed company information including addresses, classifications, financials, and hierarchical relationships
- `family_tree.json`: corporate hierarchy and parent-subsidiary linkages

The pipeline performs a join/enrichment operation to attach parent company information to each company record and outputs the enriched dataset in Parquet format for efficient querying and analysis.

## Architecture

### Database Schema Design

The solution is designed with a normalized relational schema to minimize redundancy and enable efficient querying.

A simple ERD in plain ASCII looks like this:

```text
+---------------------+
| COMPANIES           |
+---------------------+
| duns (PK)           |
| primary_name        |
| control_type        |
| operating_status    |
| start_date          |
| parent_duns (FK)    |
+---------------------+
          |
          | 1
          |
          v
+----------------------------+
| FAMILY_TREE_HIERARCHY      |
+----------------------------+
| duns (PK)                  |
| parent_duns (FK)           |
| hierarchy_level            |
| global_ultimate_duns (FK)  |
| family_tree_members_count  |
+----------------------------+

+---------------------+
| ADDRESSES           |
+---------------------+
| address_id (PK)     |
| duns (FK)           |
| country             |
| region              |
| locality            |
| postal_code         |
| address_type        |
+---------------------+

+---------------------+
| INDUSTRY_CODES      |
+---------------------+
| code_id (PK)        |
| duns (FK)           |
| code                |
| description         |
| type                |
| priority            |
+---------------------+

+---------------------+
| FINANCIALS          |
+---------------------+
| financial_id (PK)   |
| duns (FK)           |
| fiscal_date         |
| yearly_revenue      |
| currency            |
| number_of_employees |
+---------------------+
```

### Design decisions

1. The schema minimizes redundancy while keeping the most common hierarchy queries fast.
2. The `parent_duns` relationship supports parent-subsidiary queries.
3. `duns` is used as the natural business key for company identity.
4. Data is structured to support future partitioning and historical analysis.
5. The design supports scale-out if the dataset grows significantly.

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
│   └── pipeline.py
└── tests/
    ├── __init__.py
    └── test_enricher.py
```

## Installation

### Prerequisites
- Python 3.8+
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
  --validate True
```

Parameters:
- `--input`: required directory with the JSON files
- `--output`: output directory for parquet files
- `--filename`: output parquet filename
- `--validate`: whether to validate before saving

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

This includes a focused unit test for the enrichment logic and related validation checks.

## Logging and error handling

The pipeline includes logging for:
- file loading issues
- JSON parsing problems
- validation failures
- missing parent-company relationships
- final pipeline summary metrics

This makes it easier to identify and address bad records without stopping the full process.

## Handling large datasets

For production-scale workloads, two concrete changes would be useful without changing the underlying infrastructure:

### 1. Stream the input instead of loading everything at once

Use chunked processing or a JSON Lines format so the pipeline processes records incrementally instead of reading the entire file into memory.

Example idea:

```python
def load_data_blocks_streaming(filename, chunk_size=10000):
    chunk = []
    with open(filename, 'r') as f:
        for line in f:
            record = json.loads(line)
            chunk.append(record)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk
```

This reduces peak memory usage and helps scale to larger files.

### 2. Use distributed dataframe processing

For much larger datasets, switch from pure pandas to a distributed engine such as Dask. It allows the same logic to run on partitions of the data while preserving the transformation logic.

This keeps the business logic mostly the same while allowing a larger workload to be processed in parallel.

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

# Company Data Pipeline

A production-ready Python data pipeline for ingesting, enriching, and processing company information from multiple data sources.

## Overview

This pipeline processes company data from two primary sources:
- **data_blocks.json**: Detailed company information including addresses, classifications, financials, and hierarchical relationships
- **family_tree.json**: Corporate hierarchy and parent-subsidiary linkages

The pipeline performs a join/enrichment operation to attach parent company information to each company record and outputs the enriched dataset in Parquet format for efficient querying and analysis.

## Architecture

### Database Schema Design

The solution is designed with a normalized relational schema to minimize redundancy and enable efficient querying:

```
┌────────────────────────────────────────────�┌───────�────────┐
│                     ENTITY-RELATIONSHIP DIAGRAM   │                     ENTITY-RELATIONSHIP DIAGRAM   │                     ENTITY-RELATIONSHIP DIAGRAM   │              ─────────────────────────┘

┌──────────────────────┐
│    COMPANIES         │
├──────────────────────┤
│ PK  duns (VARCHAR)   │──┐
│     primary_name     │  │
│     control_type     │  │
│     status           │  │
│     start_date       │  │
│     FK parent_duns   │  │
└──────────────────────┘  │
         │ 1              │
         │                │
         └────────────────┤
              │ (0..N)     │
              │            │
┌─────────────────────────┴─────────────────────┐
│       FAMILY_TREE_HIERARCHY                   │
├───────────────────────────────────────────────┤
│ PK  duns                                      │
│     hierarchy_level                           │
│     global_ultimate_duns (FK -> COMPANIES)    │
│     family_tree_members_count                 │
│ FK  parent_d│ FK  parenNIES.duns)           │ FK  parent_d│ FK  parenNIE��│ FK  parent_d│ FK  par──�│ FK  parent_d│ FK�───�│ FK  parent_d│ FK  parenNIE��────┘

┌──────────────────────┐
│  ADDRESSES           │
├──────────────────────┤
│ PK  address_id       │
│ FK  duns (COMPANIES) │
│     country          │
│     region           │
│     locality          │
│     postal_code      │
│     address_type     │
└──────────────────────┘

┌──────────────────────┐
│  INDUSTRY_CODES      │
├──────────────────────┤
│ PK  code_id          │
��������������������������� ���������������
�│     type           │     type           │     type           │   �─────────────────┘

┌──────────────────────┐
│  FINANCIALS          │
├──────────────────────┤
│ PK  financial_id     │
│ FK  duns (COMPANIES) │
│     fiscal_da│     fiscal_da│     fiscal_da│     fiscal_da│     fiscal_da│��│     fiscal_da│   ��
└└└└└└└─────────────�└└└└└└└──si└└└└└└└─maliza└└└└└└└─While fully normalized, we store parent_duns in COMPANIES table to avoid joins for common queries
2. **Hiera2. **Hiera2. **Hiera2. **Hiera2. **Hiera2. **Hiera2. **Hiera2. **Hiera2es2. **Hiera2. **Hiera2. *. **C2. **Hiera2. **Hiera2. **Hiera2. **Hiera2. **Hiera2. **Hiera2. **Hiera2as2. **Hiera2. **Hiera2. **Handard for company identification
4. **Temporal Data**: start_date and fiscal_date support historical analysis
5. **Scalability**: Design supports partitioning by country/region and archive by fiscal period

## Project Structure

```
data-pipeline/
├── main.py                    # Entry point for running the pipeline├── main.py                    # Entry point for running t��─ .gi├── main.py       # Git├── main.py ��── README.md                  # This file
├── output/                    # Directory for output parquet files
├── src/
│   ├── __init__.py           # Package initialization
│   ├── logger.py             # Logging configuration
│   ├── models.py             # Data models and validation schemas
│   ├── data_loader.py  │   ├── data_loader.py  │   ├── data_loader.py  │   ├── data_loader.py  │   ├── data_loader.py  │   ├── data_loader.py  │   ├── data_loader.py  │   ├── data_loader.py  │   ├── datch│   ├── data_loader.py  │   ├── data_loader.py  │   �ites
│   ├── data_loader.py  │   ├── data_loader.py  │   ├── data_loader.p`

22222222222222222222environ2222222222222
ppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppecution

Run the pipeline on a directory containing `datRun the pipeline on a directory containing `datRun the pipeline on a dirpaRun the pipelrectory
```

### Advanced Options

```bash
python main.py \
  --i  --i  --i  --i  --i  --i  --i  --i  --i  --i  --i  --i  --iename enriched_companies.parquet \
  --validate True
```

**Parameters:**
- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `-th- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `- `riched data
print(df.head())
print(df.columnprint(df.columnprint(df.columnprint(df.columnprint(df.columnprint(df.columnprint(df.columnprint(df.columnprint(df.columnprint(df.columnprint(df.columnprint(df.columnprint(df.columnprint(a Ingestion
- ✅ Robust JSON parsing with error recovery
- ✅ Support for nested data structures
- ✅ Null/missing value handling
- ✅ Type validatio- using Pydantic models

### Data Processing
- ✅ Company-family tree join/enrichment
- ✅ Hierarchical relationship extraction
- ✅ Multi-source dat- ✅ Multi-son
- - � C- - � C- -ve error handling and logging

### Data Quality
- ✅ Schema validation
- ✅ Data integrity checks
- ✅ Duplicate detection
- ✅ Completeness validation
- ✅ Processing statistics and error reporting

### Output
- ✅ Parquet format with Snappy compression
- ✅ Efficient columnar storage
- ✅ Proper data type preservation

## Testing

Run the unit test suite:

```bash
pytest tests/ -v
```

Run tests with coverage:

```bash
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

The test suite includes:
- **test_join_company_with_family_tree_enriches_subsidiaries**: Validates parent company enrichment
- **test_join_handles_missing_family_tree_data**: Tests graceful handling of missing data
- **test_enriched_data_validation_passes_on_valid_data**: Validates dat- **test_enriched_data_validatio_m- **test_enriched_data_validation_pEnsures da- **test_enrion duri- **test_enriched_data_validation_
tests/test_enricher.py::TestDataEnricher::test_join_company_with_family_tree_enriches_subsidiaries PASSED
tests/test_enricher.py::TestDataEnricher::test_join_handles_missing_family_tree_data PASSED
tests/test_enricher.py::TestDataEtests/test_enricher.py::Tea_vatests/test_enricher.py::TestDataEtests/tes/test_enricher.py::TestDataEnricher::test_join_maintains_all_company_attributes PASSED
```

## Logging

The pipeline provides comprehensive logging at all stages:

```
2024-10-03 2024-10-03 2rc.pipelin2024-10-03 2024-10-03 2tialized wi2024-10-03 2024-10-03 2rc.pipelin2024-1:32:10 -2024-10-03ine - INF2024-10-03 g company data pipeline
2024-10-03 14:32:10 - src.data_loader - INFO - Loading data blocks from data_blocks.json
2024-10-03 14:32:11 - src.data_loader - INFO - Processed 100 companies from data blocks
2024-10-03 14:32:11 - src.enricher - INFO - Starting join/enrichment for 100 companies
2024-10-03 14:32:11 - src.enricher - INFO - Join/enrichment complete: 85 enriched, 15 without parent, 0 errors
2024-10-03 14:32:12 - src.pipeline - INFO - Successfully saved enriched data to output/enriched_companies.parquet
```

## Handling Large Datasets - Scaling Strategy

The current implementation is optimized for datasets up to several million records. For production environments with significantly larger datasets (100M+ records), the following concrete changes would be implemented:

### 1. **Streaming JS### 1ocessin### 1. **Streaming JS### 1ocessin### 1. **Streaming JS pipeline ### 1. **Streaming JS### 1ocessin### 1. **Streaming JS### 1ocessin### 1. **Streaming JS pipeline ### 1. **Streaming JS### 1ocessin### 1. **Streaming JS### 1ocessi: Proc### 1. **Streaming JS### 1ocessin### 1. **Streaming JS### 1ocessin### 1. **Streaming JSnk_size: int = 10000):
    """Process JSON file in streaming chunks."""
    chunk = []
    with open(filename, 'r') as f:
        for line in f:  # Assumes jsonlines format (one JSON object per line)
            record = json.loads(line)
            chunk.append(record)
            
            if len(chunk) >= chunk_size:
                yield chunk  # Yield chunks for processing
                chunk = []
        
        if chunk:
            yiel            yiel            yiel            yiel            yiel            yiel            yiel            yiel            yiel            yiel            yiel            yiel            yiel            yiel        (AWS S3, Azure Data Lake)

### 2. **Distributed DataFrame Processing with Dask**

**Current limitation:** Pandas DataFrames require all data in memory.

**Scaling change:** Use Dask for distributed computing:

```python
import dask.dataframe as dd

# Process data distributed across multiple partitions
df_companies = dd.read_json(
    'data_blocks.jsonl',  # jsonlines format
    'data_blocks.jsonl',  # jsonlines format
rs irs irs irs is
)))))))))))))))))))))))))))))))omatically across CPU cores
enriched = df_companies.map_partitions(
    enrich_part    enrich_part    enrich_part    ena={...}  # Schema definition
)

# Write partitio# Write partitio# Write partitio# Writeutput/',
    engine='pyarrow',
    partition_cols=['country']    partition_cols=[ntry
)
)
  
**Be**Be**Be**BeAutomatic parallelization across CPU cores
- Lazy evaluation minimizes memory usage
- Scales from single machine to Spark clusters
- Transparent fallback to disk-based processing
- Compatible with cloud object storage (S3, GCS)

### Implementation Roadmap

| Scale Level | Recommended Approach | Memory Requirement | Processing Time (1B records) |
|-------------|---------------------|------|-------------|---------------------|------|---------records | Current implementation (Pandas) | ~2-4GB | ~1-2 min |
| 10M-1B records | Streaming + Dask | ~500MB-2GB | ~5-15 min |
| >1B records | Streaming + Spark cluster | | >1B records | Streaming + Spark clusteritio| >1Scaling Consid| >1B records | Streaming + Spark cluster | | >1B recarquet| >1B records | Streaming + Spark clu si| >1B records | Streaming + Spark cluster | | >1B records | Streaming + Sparstry_co| >1B records | Streaming + Spark cluster | | >1B records rocessed records (via checks| >1B records | Streaming + Spark clusteBatch Processing**: Submit large jobs to cloud platforms (AWS Glue, Databricks) w| >1B records | Streaming + Spark clus family tree lookups in distributed cache (Redis) | >1B records | Streaming + Spark cluster | pipeline includes robust error handling:

- **Validation Errors**: Records with sc- **Validation Errors**: Records with sc- **Validation Errors**: Records with sc- **Validul- **Validation Errors**: Records with sc- **Validation Errors**: Records with sc- **Validation Errors**: Records with sc- **Validul- **Validation Errors**: Reerrors are captured and reported in summary statistics

Example error report:
```
Processing errors: 3
Errors encountered during processing:
  - DUNS 123456789: Validation error: 'duns' field is required
  - DUNS 987654321: Error enriching: KeyError in family tree lookup
  - DUNS 555555555: JSON parsing error: invalid control character
```

## Performance Metrics

On a typical machine with 100K companies:
- **Data Loading**: ~500ms
- **Data Enrichment**: ~800ms
- **Parquet Writing**: ~300ms
- **Total Execution**: ~2 seconds

Memory consumption: ~200-400MB for typical datasets

## Version Control

This project uses Git for version control. Key branches:

- `main` - Production-ready code
- `develop` - Development branch with latest features
- `feature/*` - Feature branches

## License

Confidential - For authorized use only

## Contact

For questions or issues, contact your HR representative.

---

**Last Updated:** October 3, 2026
**Version:** 1.0.0

# Entity-Relationship Diagram (ERD)

The **proposed normalized relational model** for the Company Data Pipeline is shown in [`erd.svg`](erd.svg). Open or download the SVG for a scalable diagram, or export it to PNG using a browser, Inkscape, or another vector-graphics application.

> The ERD is a logical schema proposal. The current pipeline writes a flat enriched Parquet table; it does not create these normalized tables.

The diagram covers the company entity and its repeating detail tables, financial statements and line items, self-referencing ownership links, and the captured family-tree response/member/role hierarchy. For full field descriptions and modeling rationale, see the **Proposed normalized relational model** section in [`../README.md`](../README.md).

## Export to PNG

Open `erd.svg` in a web browser and choose **Print → Save as PDF**, then convert the PDF to PNG; or use Inkscape's **Export** action and select PNG. The SVG itself is suitable for viewing and printing at any scale.

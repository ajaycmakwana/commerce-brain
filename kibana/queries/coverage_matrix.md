# Query Template Coverage Matrix

## About This Document

**Purpose:** Maps investigation questions to the correct query template numbers in `query_templates.md`.  
**Use this when:** A user describes a problem (e.g. "product not showing in search", "wrong price for B2B group") and you need to find which template(s) answer it — look up the scenario here, get the template number, then go to `query_templates.md`.  
**What it covers:** 60+ investigation scenarios across 10 categories: visibility, categories/facets, price, search/relevance, recommendations, staleness/reindex, stock/product type, images/embeddings, index health, and general diagnostics.  
**Phase 2 (Snowplow):** Behavioral event scenarios are marked ⏳ — Snowplow query templates are not yet built.

Use this to confirm that any Live Search investigation question maps to at least one query template.

## How to Read

- **Scenario** — The investigation question a T3 engineer faces
- **Query(s)** — Template numbers that answer it
- **Status** — ✅ Covered | ⏳ Phase 2 (Snowplow) | ❌ Gap

---

## Category 1: Product Visibility & Displayability

| Scenario | Query(s) | Status |
|---|---|---|
| Is the product in the index at all? | 1.3, 1.4 | ✅ |
| Is the product displayable? | 2.1, 2.2 | ✅ |
| Why is the product not displayable? | 2.1, 2.4, 2.6 | ✅ |
| Is the product soft-deleted? | 2.6, 2.7 | ✅ |
| Is there a `notDisplayable` override set? | 2.4, 2.5 | ✅ |
| Which customer groups is the product suppressed for? | 2.5 | ✅ |
| What is the product's Magento visibility setting? | 2.1, 9.4 | ✅ |
| Are there displayable products with wrong visibility? | 9.5 | ✅ |
| Does `product.default.displayable` schema apply? | 12.1, 12.2 | ✅ |
| What are customer group permissions for a product? | 13.2 | ✅ |
| Which websites/store views is the product assigned to? | 13.1 | ✅ |

---

## Category 2: Category & Facet Issues

| Scenario | Query(s) | Status |
|---|---|---|
| Is the product in the expected category? | 3.1, 14.1, 14.2 | ✅ |
| How many products are in a category? | 3.2, 14.1 | ✅ |
| Which categories does a product belong to? | 14.3 | ✅ |
| Products in a category that are NOT displayable? | 4.8 | ✅ |
| What category IDs exist in this index? | 3.7 | ✅ |
| What is the product's manual sort position in a category? | 14.4 | ✅ |
| What values does a filterable attribute have? | 9.1 | ✅ |
| Is a specific attribute populated for a product? | 9.2 | ✅ |
| How many products are missing a specific attribute? | 9.3 | ✅ |

---

## Category 3: Price Issues

| Scenario | Query(s) | Status |
|---|---|---|
| What price does the product have? | 7.1 | ✅ |
| Is the product missing a price? | 7.2 | ✅ |
| Does the product have a B2B price for a customer group? | 3.5, 7.3 | ✅ |
| How many displayable products are missing B2B price? | 3.6, 7.3 | ✅ |
| How to read the actual B2B price value? | 7.4 | ✅ |
| Product has `regular_price` field (older feed format)? | 13.3, 13.4 | ✅ |

---

## Category 4: Search Keyword & Relevance

| Scenario | Query(s) | Status |
|---|---|---|
| Why doesn't my product appear when searching for X? | 6.1, 6.2 | ✅ |
| What searchable content is stored for a product? | 6.3 | ✅ |
| Is the product's name/brand/sku stored in searchable fields? | 6.3 | ✅ |
| Does the product appear in autocomplete? | 6.4, 6.5 | ✅ |
| What ranking signals does a product have? | 4.2 | ✅ |
| Is ranking data populated for the index? | 4.2 | ✅ |

---

## Category 5: Recommendations

| Scenario | Query(s) | Status |
|---|---|---|
| Does the product have viewed-with / bought-with data? | 4.3 | ✅ |
| What % of displayable products have recommendation signals? | 4.3 | ✅ |
| Check specific rfIndicator type for a product | 4.3 | ✅ |

---

## Category 6: Staleness & Reindex

| Scenario | Query(s) | Status |
|---|---|---|
| When was a specific product last indexed? | 2.8 | ✅ |
| What is the most recently indexed product? | 2.9 | ✅ |
| Which products are stale (not updated since date X)? | 5.5 | ✅ |
| How many products were indexed in a time window? | 5.4 | ✅ |
| Was there a full reindex? (new index hash) | 5.3 | ✅ |
| Is there a gap in indexing on specific days? | 4.5 | ✅ |
| Is a reindex currently running? | 11.4 | ✅ |

---

## Category 7: Stock & Product Type

| Scenario | Query(s) | Status |
|---|---|---|
| Is the product in stock? | 3.3 | ✅ |
| How many displayable + in-stock products? | 3.4 | ✅ |
| What product types exist in the index? | 8.2 | ✅ |
| Does a configurable product have its variants indexed? | 8.1 | ✅ |
| How many bundle products are in the index? | 8.3 | ✅ |
| Which parent product owns a child SKU? | 8.4 | ✅ |
| Is a child variant indexed as its own document? | 8.5 | ✅ |
| How many configurables are missing children? | 8.6 | ✅ |
| What are the members of a grouped product? | 8.7 | ✅ |
| What options does a bundle product have? | 8.8 | ✅ |
| How many virtual / downloadable products exist? | 8.9 | ✅ |

---

## Category 8: Images & Embeddings

| Scenario | Query(s) | Status |
|---|---|---|
| Does the product have images? | 10.1 | ✅ |
| How many products are missing images? | 10.2 | ✅ |
| Is visual search (image embedding) ready? | 4.4 | ✅ |
| Is semantic search (text embedding) ready? | 4.4 | ✅ |

---

## Category 9: Index Health & Multi-Store

| Scenario | Query(s) | Status |
|---|---|---|
| What store views exist for a merchant? | 1.1 | ✅ |
| How many products in each store view? | 4.6 | ✅ |
| Is the product missing from some store views? | 5.1 | ✅ |
| Is the displayable state different across store views? | 5.2 | ✅ |
| Is the index actually serving traffic (alias active)? | 11.2 | ✅ |
| What are the index shard/replica settings? | 11.1 | ✅ |
| What is the indexing/search rate? | 11.3 | ✅ |
| When was this index created? | 5.3 | ✅ |

---

## Category 10: General Diagnostics

| Scenario | Query(s) | Status |
|---|---|---|
| Full field mapping for an index | 1.7 | ✅ |
| Sample document to inspect structure | 1.6 | ✅ |
| Full diagnostic snapshot for one product | 4.9 | ✅ |
| Lookup by SKU | 1.5 | ✅ |
| Batch lookup for multiple products | 4.7 | ✅ |
| Displayable vs deleted vs total counts | 4.1 | ✅ |

---

## Phase 2 (Snowplow — Behavioral Events)

| Scenario | Status |
|---|---|
| Did events fire for a merchant env? | ⏳ Phase 2 |
| What event types are being received? | ⏳ Phase 2 |
| Are search/click/purchase events being sent? | ⏳ Phase 2 |
| Filter events by time range | ⏳ Phase 2 |

---

## How to Validate the Templates Work

Run these 5 queries against the testing env to confirm the library is functional. Pick a known product ID from a ticket or from a `size: 1, match_all` search first.

1. **Basic existence check** — 1.3 (direct `_doc` fetch)
2. **Displayability** — 2.1 (confirm `displayable` field returns)
3. **Category membership** — 3.1 (use a known category ID)
4. **Staleness** — 2.8 (confirm `sortable.lastIndexedTs` returns a date)
5. **Coverage agg** — 4.1 (confirm displayable vs total counts look sane)

If all 5 return expected results, the rest of the library is trustworthy — they use the same field names, query patterns, and nesting rules.

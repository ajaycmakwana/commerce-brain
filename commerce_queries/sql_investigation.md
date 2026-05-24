# Commerce Feed Investigation — SQL Queries

### Query cde_products_feed rows for a specific product
```sql
SELECT
    source_entity_id,
    feed_id,
    modified_at,
    is_deleted,
    status,
    feed_hash,
    JSON_PRETTY(feed_data) AS feed_data
FROM cde_products_feed
WHERE source_entity_id = {PRODUCT_ENTITY_ID};
```
*source_entity_id maps to catalog_product_entity.entity_id. One product has multiple rows — one per store view, differentiated by feed_id. is_deleted=1 means feed marked product deleted. status=0 means successfully indexed, status=1 means failed.*

---

### Query cde_products_feed changelog for a specific product
```sql
-- Check if product has pending changelog entries not yet processed by indexer
SELECT cl.version_id, cl.entity_id
FROM cde_products_feed_cl cl
JOIN mview_state ms ON ms.view_id = 'cde_products_feed'
WHERE cl.entity_id = {PRODUCT_ENTITY_ID}
  AND cl.version_id > ms.version_id
ORDER BY cl.version_id ASC;
```
*If rows returned — product changes are queued but indexer has not processed them yet.*

---

### Check mview_state for product feed indexer
```sql
SELECT view_id, mode, status, version_id, updated
FROM mview_state
WHERE view_id = 'cde_products_feed';
```
*status: idle=healthy, working=running, suspended=stuck. version_id=last changelog version processed. Compare with MAX(version_id) in cde_products_feed_cl to find backlog.*

---

### Count pending backlog for product feed indexer
```sql
SELECT COUNT(*) AS backlog
FROM cde_products_feed_cl cl
JOIN mview_state ms ON ms.view_id = 'cde_products_feed'
WHERE cl.version_id > ms.version_id;
```
*backlog > 0 means indexer has unprocessed product changes. High backlog = indexer is behind or stuck.*

---

### Check feed submission status across all products
```sql
SELECT status, COUNT(*) AS cnt
FROM cde_products_feed
GROUP BY status;
```
*status=0: success, status=1: failed submission to SaaS, status=2: being processed. Many rows with status=1 means SaaS export is failing.*

---

### Check failed feed rows detail
```sql
SELECT source_entity_id, feed_id, modified_at, status, JSON_PRETTY(feed_data) AS feed_data
FROM cde_products_feed
WHERE status = 1
LIMIT 20;
```

---

### Full product sync status check — feed rows, backlog, and mview state
```sql
SELECT '== PRODUCT FEED ROWS ==' AS section, NULL AS version_id,
       source_entity_id AS entity_id, modified_at, is_deleted, status, feed_hash,
       JSON_PRETTY(feed_data) AS feed_data
FROM cde_products_feed
WHERE source_entity_id = {PRODUCT_ENTITY_ID}

UNION ALL

SELECT '== ATTRIBUTES FEED ROWS ==', NULL, source_entity_id,
       modified_at, is_deleted, status, feed_hash, JSON_PRETTY(feed_data)
FROM cde_product_attributes_feed
WHERE source_entity_id = {PRODUCT_ENTITY_ID}

UNION ALL

SELECT '== PRODUCT FEED BACKLOG ==', cl.version_id, cl.entity_id,
       NULL, NULL, NULL, NULL, NULL
FROM cde_products_feed_cl cl
JOIN mview_state ms ON ms.view_id = 'cde_products_feed'
WHERE cl.entity_id = {PRODUCT_ENTITY_ID}
  AND cl.version_id > ms.version_id

UNION ALL

SELECT '== ATTRIBUTES FEED BACKLOG ==', cl.version_id, cl.entity_id,
       NULL, NULL, NULL, NULL, NULL
FROM cde_product_attributes_feed_cl cl
JOIN mview_state ms ON ms.view_id = 'cde_product_attributes_feed'
WHERE cl.entity_id = {PRODUCT_ENTITY_ID}
  AND cl.version_id > ms.version_id

UNION ALL

SELECT '== MVIEW STATE ==', NULL, NULL,
       updated, NULL, NULL, view_id, status
FROM mview_state
WHERE view_id IN ('cde_products_feed', 'cde_product_attributes_feed');
```
*Runs one query to check: feed rows per store view, attributes feed rows, unprocessed changelog backlog, mview state for both indexers.*

---

### Check scopes feed — store views registered in SaaS
```sql
SELECT * FROM scopes_website_data_exporter;
SELECT * FROM scopes_website_data_submitted_hash;
SELECT * FROM scopes_customergroup_data_submitted_hash;
```
*If scopes_website_data_exporter is empty or missing store views — products will not sync. Scopes must be synced before products.*

---

### Check product price feed for a specific product
```sql
SELECT source_entity_id, feed_id, modified_at, is_deleted, status,
       JSON_PRETTY(feed_data) AS feed_data
FROM cde_product_prices_feed
WHERE source_entity_id = {PRODUCT_ENTITY_ID};
```

---

### Check product overrides feed for a specific product
```sql
SELECT source_entity_id, feed_id, modified_at, is_deleted, status,
       JSON_PRETTY(feed_data) AS feed_data
FROM cde_product_overrides_feed
WHERE source_entity_id = {PRODUCT_ENTITY_ID};
```

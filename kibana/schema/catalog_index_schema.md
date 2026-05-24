# Live Search Catalog Index — Field Schema Reference

## About This Document

**Purpose:** Ground truth field reference for Adobe Commerce Live Search catalog indexes in Elasticsearch.  
**Use this when:** You need to know a field name, its type, whether it requires a `nested` query wrapper, or what values it stores before writing an ES query.  
**What it covers:** All fields in `catalog_1_*` indexes — top-level fields, nested sub-fields (`filterable`, `categoryData`, `images`), flat object sub-fields (`productoverride`, `sortable`, `searchable`, `viewModel`), and special types (`rank_feature`, `dense_vector`, `completion`, `adobe_price`).  
**What it does NOT cover:** How to write the query (see `query_templates.md`), or which template maps to which investigation scenario (see `coverage_matrix.md`).  
**Source:** Validated against real `_mapping` API output and live document samples from three testing environments (standard, B2B, statistics/ranking variants).  
**Key rule:** Always check the field type and nesting here before writing a query — using `term` on a `nested` field or querying `rank_feature` with `range` are silent failure modes.

---

## Index Naming Convention

```
catalog_1_{ENV_ID}_{STORE_VIEW_CODE}_{HASH}
```

| Segment | Description | Example |
|---|---|---|
| `catalog_1_` | Fixed prefix for all Live Search catalog indexes | — |
| `{ENV_ID}` | Merchant's SaaS environment UUID | `5473b108-b314-4b97-9b51-1b62179034f8` |
| `{STORE_VIEW_CODE}` | Magento store view code | `default`, `en_gb`, `hookah_b2b`, `de_de` |
| `{HASH}` | 8-char alias hash — changes on full reindex | `3d166cb8` |

**Find all indexes for a merchant env:**
```
GET /_cat/indices/catalog_1_{ENV_ID}*?v&h=index,docs.count&s=index
```

---

## Schema Variants

Two schema variants exist in production:

| Variant | When used | Key difference |
|---|---|---|
| **Standard** | Most merchants, all store views | Top-level `displayable`, `productoverride`, `filterable` (nested) |
| **Statistics/Ranking** | Recommendation-enriched indexes (e.g. vijay_sales pattern) | Same top-level fields + `statisticsByView`, extended `sortable`, different `filterable` sub-fields |

Both variants share the same 25+ top-level fields. The statistics variant adds `statisticsByView`.

---

## Top-Level Fields

| Field | Type | Notes |
|---|---|---|
| `_id` | — | Document ID — usually the product ID (integer) or SKU string depending on merchant |
| `sku` | `text` + `keyword` | Use `sku.keyword` for exact term matches |
| `name` | `text` | Product name — full-text searchable |
| `urlKey` | `text` + `keyword` | URL slug |
| `status` | `text` + `keyword` | Product status (enabled/disabled) |
| `visibility` | `text` + `keyword` | Magento visibility setting |
| `productVisibility` | `text` + `keyword` | Live Search computed visibility |
| `displayable` | `boolean` | **Key field** — true if product should appear in search results |
| `deleted` | `boolean` | Soft-delete flag — true if product was removed from catalog |
| `images` | `nested` | Product images array |
| `categoryData` | `nested` | Category memberships; sub-fields: `categoryId`, `categoryPath`, `productPosition` |
| `filterable` | `nested` | **All filterable attributes** — MUST use `nested` query |
| `searchable` | `object` | Full-text searchable attribute values |
| `sortable` | `object` | Sortable attribute values |
| `productoverride` | `object` | Per-store/group display overrides |
| `statistics` | `object` | Behavioral ranking signals (rank_feature type) |
| `statisticsByView` | `object` | Same signals segmented by store view (rank_features) |
| `rfIndicators` | `object` (dynamic) | Recommendations data — co-view/co-purchase SKU arrays |
| `rfIndicatorsByView` | `object` (dynamic) | rfIndicators segmented by store view |
| `viewModel` | `object` (disabled) | Stored but not indexed — retrieve via `_source` only. Contains `type`, `websiteCode`, `storeViewCode`, `productId`, `productOverrides` (per-group prices) |
| `attributes` | `object` | Extra attribute metadata (`collection`, `keys`) |
| `suggest` | `completion` | Autocomplete suggestions |
| `prices_sortable_asc` | `adobe_price` | Excluded from `_source` — index-only |
| `prices_sortable_desc` | `adobe_price` | Excluded from `_source` — index-only |
| `imageEmbedding` | `dense_vector` (512 dims, l2_norm) | Visual similarity vector |
| `productEmbedding` | `dense_vector` (768 dims, dot_product) | Semantic product similarity vector |
| `textEmbedding` | `dense_vector` (384 dims, cosine) | Text semantic search vector |
| `textEmbeddingSource` | `keyword` (not indexed) | Source text used for textEmbedding |

---

## `productoverride` Sub-Fields

**Path:** `productoverride.*`  
**Type:** object (not nested — query directly, no `nested` wrapper needed)  
**In `_source`:** fields appear as flat dotted keys e.g. `"productoverride.displayable": [...]`

| Sub-field | Type | Notes |
|---|---|---|
| `productoverride.displayable` | `keyword` | Array of website/group hashes where product IS explicitly displayable |
| `productoverride.notDisplayable` | `keyword` | Array of website/group hashes where product is suppressed. `NLI` = not logged in |
| `productoverride.addToCartAllowed` | `keyword` | Array of website/group hashes where add-to-cart is allowed |
| `productoverride.priceDisplayable` | `keyword` | Array of website/group hashes where price is shown |

**Important:** `productoverride` stores overrides from Magento. The computed `displayable` boolean at the top level is the final resolved value after applying all overrides. An **empty array** means no override is set (not suppressed). A **non-empty array** means the product has explicit overrides for those groups/websites.

---

## `filterable` Sub-Fields (Nested)

**CRITICAL:** `filterable` is type `nested`. All queries on `filterable.*` must use a `nested` query wrapper, or results will be incorrect/empty.

### Universal sub-fields (present in all schema variants)

| Sub-field | Type | Notes |
|---|---|---|
| `filterable.sku` | `text` + `keyword` | SKU inside nested |
| `filterable.categoryIds` | `text` + `keyword` | Category IDs — use `.keyword` for exact match |
| `filterable.categoryIdPaths` | `text` + `keyword` | Full category path IDs |
| `filterable.categoryPaths` | `text` + `keyword` | Human-readable category paths |
| `filterable.inStock` | `boolean` | Stock availability |
| `filterable.lowStock` | `boolean` | Low stock flag |
| `filterable.isBundle` | `boolean` | Bundle product type |
| `filterable.isGrouped` | `boolean` | Grouped product type |
| `filterable.commerceProductType` | `text` + `keyword` | Magento product type |
| `filterable.visibility` | `text` + `keyword` | Visibility inside filterable |
| `filterable.brand` | `text` + `keyword` | Brand attribute |
| `filterable.color` | `text` + `keyword` | Color attribute |
| `filterable.prices_override` | `adobe_price` | Per-customer-group price. Query as `filterable.prices_override.{CUSTOMER_GROUP}` (e.g. `filterable.prices_override.NLI`). **Excluded from `_source`** — use `viewModel` to read price values |

### Common merchant-specific filterable attributes (text + keyword)
`gender`, `size`, `material`, `season`, `department`, `fashion_color`, `fashion_material`, `fashion_style`, `brand`, `pattern`, `fit`, `style`, `sustainability`, `dietary`, `lifestage`, `animal`, `has_video`

---

## `sortable` Sub-Fields

**Path:** `sortable.*`  
**Type:** object (flat — no nested wrapper)

| Sub-field | Type | Notes |
|---|---|---|
| `sortable.lastIndexedTs` | `date` | **Key field** — timestamp when product was last indexed. Use for staleness checks |
| `sortable.name` | `keyword` (case-insensitive) | Sort by name |
| `sortable.brand` | `keyword` (case-insensitive) | Sort by brand |
| `sortable.price` | `float` | Sort by price — **can be absent** for some products (e.g. configurable parents without a direct price) |
| `sortable.inStock` | `boolean` | Sort/filter by stock |
| `sortable.lowStock` | `boolean` | Sort/filter by low stock |
| `sortable.department` | `keyword` (case-insensitive) | Sort by department |
| `sortable.sku` | `keyword` | SKU in sortable object — **can be null** |

*Statistics-variant indexes add (confirmed from vijay_sales real data):* `sortable.discount_percentage`, `sortable.offer_price`, `sortable.vsp`, `sortable.brand`, `sortable.is_offer_available`, `sortable.vs_loyalty`, `sortable.is_child`. Additional merchant-specific fields may appear — they are dynamic and vary per merchant.*

---

## `statistics` Sub-Fields

**Type:** `rank_feature` — these are **scoring signals**, not filterable values. Use `exists` to check presence, not `term`.

| Sub-field | Meaning |
|---|---|
| `statistics.jlhScoreRf` | Trending signal (JLH score, rolling) |
| `statistics.jlhScoreFourteenDaysRf` | Trending — 14-day window |
| `statistics.jlhScoreThirtyDaysRf` | Trending — 30-day window |
| `statistics.productViewSessionsPercentileRankRf` | Most-viewed signal |
| `statistics.productPurchaseSessionsPercentileRankRf` | Most-purchased signal |
| `statistics.productAddToCartSessionsPercentileRankRf` | Most-added-to-cart signal |
| `statistics.addToCartSessionConversionRateLowerConfidenceRf` | Add-to-cart conversion rate |
| `statistics.purchaseSessionConversionRateLowerConfidenceRf` | Purchase conversion rate |

---

## `rfIndicators` Sub-Fields

**Type:** Dynamic object — `*Skus` fields are `keyword` arrays; non-Skus fields are `rank_features`.  
**Note:** `rfIndicators*` is **excluded from `_source`** by default. Use `_source: ["rfIndicators*"]` explicitly or use `exists` query.

| Sub-field | Type | Meaning |
|---|---|---|
| `rfIndicators.viewViewSkus` | `keyword` | Array of SKUs co-viewed with this product |
| `rfIndicators.viewBoughtSkus` | `keyword` | Array of SKUs bought after viewing this product |
| `rfIndicators.boughtBoughtSkus` | `keyword` | Array of SKUs co-purchased with this product |
| `rfIndicators.shopperViewView` | `rank_features` | View-view recommendation strength scores |
| `rfIndicators.shopperViewBought` | `rank_features` | View-bought recommendation strength scores |
| `rfIndicators.shopperBoughtBought` | `rank_features` | Bought-bought recommendation strength scores |

---

## `categoryData` Sub-Fields (Nested)

**Type:** nested — requires `nested` query wrapper

| Sub-field | Type | Notes |
|---|---|---|
| `categoryData.categoryId` | `text` | Category ID — use `.keyword` sub-field if filtering |
| `categoryData.categoryPath` | `text` + `keyword` | Full category path string |
| `categoryData.productPosition` | `integer` | Manual sort position within category — negative values are valid (merchant-controlled sort) |

---

## `viewModel` Sub-Fields

**Path:** `viewModel.*`  
**Type:** `object` with `enabled: false` — stored as raw blob, NOT indexed. Sub-path filtering in `_source` is unreliable; always request the full `viewModel` object.  
**Use for:** reading price values, product type, store context, image URLs, per-group permissions.

| Sub-field | Notes |
|---|---|
| `viewModel.websiteCode` | Website code (e.g. `"base"`, `"hookah_wholesalers"`) |
| `viewModel.storeViewCode` | Store view code (e.g. `"default"`, `"hookah_b2b"`) |
| `viewModel.productId` | **Actual Magento product ID (integer)** — use this when `_id` is a SKU string (B2B indexes) |
| `viewModel.type` | Product type: `"simple"`, `"configurable"`, `"grouped"`, `"bundle"`, `"virtual"`, `"downloadable"` |
| `viewModel.sku` | SKU string |
| `viewModel.name` | Display name |
| `viewModel.description` | Full HTML description |
| `viewModel.shortDescription` | Short HTML description |
| `viewModel.currency` | Store currency code (e.g. `"GBP"`, `"USD"`) |
| `viewModel.url` | Product page URL |
| `viewModel.image.url` | Main image URL |
| `viewModel.smallImage.url` | Small image URL |
| `viewModel.thumbnailImage.url` | Thumbnail image URL |
| `viewModel.metaTitle` | SEO meta title |
| `viewModel.metaDescription` | SEO meta description |
| `viewModel.weight` | Product weight (float) |
| `viewModel.productOverrides` | Object keyed by SHA1 group hash or `"NLI"` — see below |

### `viewModel.productOverrides` Structure

Keys are SHA1 customer group hashes (e.g. `"f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59"`) or `"NLI"` (not logged in). Each entry:

```
"{GROUP_HASH}": {
  "prices": {
    "min": { "regular": float, "final": float },
    "max": { "regular": float, "final": float }
  },
  "addToCartAllowed": boolean
}
```

- `regular` = list price; `final` = actual selling price after discounts
- `min`/`max` matter for configurable, grouped, and bundle products (price range across variants/options)
- `final: null` means product has no price for that customer group (common in B2B suppressed groups)
- `addToCartAllowed: false` means the group cannot add to cart even if the product is displayable

**`sortable.price` is absent for configurable, grouped, and bundle products** — confirmed from real data. Use `viewModel.productOverrides.NLI.prices.min.final` as the NLI price reference.

---

## `searchable` Sub-Fields

**Path:** `searchable.*`  
**Type:** object (flat — no nested wrapper)  
**Note:** Has ~88 sub-fields dynamically populated per merchant. Do NOT use `searchable.*` wildcard in queries — use specific sub-field names.

| Sub-field | Type | Notes |
|---|---|---|
| `searchable.sku` | `text` | SKU for full-text match |
| `searchable.name` | `text` | Product name — primary search field |
| `searchable.brand` | `text` | Brand name |
| `searchable.categoryPath` | `text` (array) | Array of category path strings e.g. `["cat", "cat/cat-healthcare"]` |
| `searchable.childrenSkus` | `keyword` (array) | Child variant SKUs (configurable products) |
| `searchable.childrenNames` | `text` (array) | Child variant display names |
| `searchable.childrenUrlKeys` | `keyword` (array) | Child variant URL keys |
| `searchable.color` | `text` (array) | Color attribute values |
| `searchable.lastIndexedTs` | `date` | Timestamp — mirrors `sortable.lastIndexedTs` |
| `searchable.defaultSearchField` | `text` (array) | Catch-all field aggregating misc. searchable attribute values |

*Additional merchant-specific attributes (e.g. `searchable.size`, `searchable.material`) are populated dynamically per merchant configuration.*

---

## `images` Sub-Fields (Nested)

**Path:** `images.*`  
**Type:** nested — requires `nested` query wrapper when filtering; `_source` returns full array directly

| Sub-field | Type | Notes |
|---|---|---|
| `images.imageUrl` | `keyword` | Full-size image URL |
| `images.thumbnailUrl` | `keyword` | Thumbnail image URL |
| `images.smallImageUrl` | `keyword` | Small image URL |
| `images.inStock` | `boolean` | Whether the variant behind this image is in stock |

*`images` is an array — one entry per product variant (or one entry for simple products). An empty array means no images are indexed.*

---

## Key Quirks & Gotchas

1. **`filterable` requires nested query** — direct `term` on `filterable.categoryIds` without a `nested` wrapper will return wrong results (silently 0 hits or wrong matches due to cross-document field flattening).

2. **`productoverride` is NOT nested** — unlike `filterable`, query `productoverride.notDisplayable` directly with a plain `term` filter.

3. **`rfIndicators*` excluded from `_source`** — must explicitly request it: `"_source": ["rfIndicators.viewViewSkus"]` otherwise you get an empty object back.

4. **`filterable.prices_override` excluded from `_source`** — read prices from `viewModel` object instead.

5. **`prices_sortable_asc` / `prices_sortable_desc` excluded from `_source`** — index-only fields, never readable via `_source`.

6. **`statistics.*` are `rank_feature` type** — cannot use `term`, `range`, or `aggs` on them. Use `exists` to check presence. `statistics` at the document level can be `null` (not absent) — this is normal for products without behavioral data.

7. **`sortable.lastIndexedTs` is the staleness indicator** — not a Magento field, set by the indexer. A product with a very old timestamp relative to others in the same index was likely not re-indexed during the last run.

8. **`_id` is NOT always the Magento product ID** — confirmed from real data: B2B indexes use SKU as `_id` (e.g. `"HB-BTO-Hookah-INVI-Vergence-Aluminum"`). Standard indexes use integer product ID as string. Always check with a `size: 1` sample first.

9. **`visibility` stores full label strings** — confirmed from real data: values are `"Catalog, Search"`, `"Search"`, `"Not Visible Individually"`, `"Catalog"`. NOT integers. `productVisibility` uses enum style: `"CATALOG_AND_SEARCH"`, `"SEARCH"`, `"NOT_VISIBLE"`, `"CATALOG"`.

10. **`_cat/indices docs.count` vs `_count` discrepancy** — `_cat/indices` shows Lucene-level segment count including pending-deletion tombstones. `_count` returns live searchable documents only. The live count is the one that matters for investigation.

11. **`viewModel.productOverrides` keys are SHA1 hashes** — customer group identifiers in `viewModel` are SHA1 hash strings (e.g. `f1f836cb4ea6efb2a0b1b99f41ad8b103eff4b59`), except for the special group `NLI` (Not Logged In) which appears as the literal string `"NLI"`. These correspond to the same hashes used in `productoverride.notDisplayable`.

12. **`sortable.price` and `sortable.sku` can be null** — confirmed from real data. Always use `exists` before assuming a price value is present.

13. **`storeViewCode` and `websiteCode` are NOT top-level fields** — confirmed from real data: querying `_source: ["storeViewCode", "websiteCode"]` returns nothing. These values live inside `viewModel.storeViewCode` and `viewModel.websiteCode`. Same for `customerGroupPermissions` — this field does not exist; customer group data is in `productoverride.*` (flat dotted keys) and `viewModel.productOverrides` (nested object keyed by SHA1 group hashes).

14. **`product.default.*` path not confirmed** — the `product.default.displayable` schema variant was NOT found in any of the three tested environments (standard, B2B, vijay_sales statistics). All tested indexes use top-level `displayable`. Always check the mapping (1.7) before assuming this path exists.

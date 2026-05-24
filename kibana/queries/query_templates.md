# Live Search — Kibana Query Template Library

## About This Document

**Purpose:** Ready-to-run Elasticsearch query templates for investigating Adobe Commerce Live Search and product sync issues in Kibana Dev Tools.  
**Use this when:** A user asks for an ES query to investigate a Live Search issue — pick the matching template, substitute the placeholders, and run it.  
**What it covers:** 14 tiers of queries from basic index discovery to advanced parent-child, B2B, price, and statistics investigation. All templates are validated against real testing environment data.  
**How to use:** Replace placeholders (`{ENV_ID}`, `{STORE_CODE}`, `{HASH}`, `{PRODUCT_ID}`, `{SKU}`, `{CATEGORY_ID}`, `{ATTRIBUTE_CODE}`, `{SEARCH_KEYWORD}`, `{CUSTOMER_GROUP}`) with real values before running. Find the right template number using `coverage_matrix.md`.  
**Field reference:** If unsure about a field name, type, or nesting requirement, check `catalog_index_schema.md` first.  
**Scope:** Read-only queries only. Scoped to specific env IDs — no global wildcard scans. Testing/staging environments only.

---

## How to Use

Replace these placeholders before running any query:

| Placeholder | What to substitute | How to find it |
|---|---|---|
| `{ENV_ID}` | Merchant's SaaS environment UUID | From Jira ticket / merchant account |
| `{STORE_CODE}` | Store view code | From `_cat/indices` output |
| `{HASH}` | 8-char index alias hash | From `_cat/indices` output |
| `{PRODUCT_ID}` | Magento product ID (integer) | From Jira ticket / merchant |
| `{SKU}` | Product SKU string | From Jira ticket / merchant |
| `{CATEGORY_ID}` | Magento category ID | From Jira ticket / merchant |
| `{CUSTOMER_GROUP}` | Customer group code (e.g. `NLI`, `b2b`) | From Jira ticket / merchant |

**Full index name format:** `catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}`

---

## TIER 1 — Basic: Index & Document Discovery

### 1.1 List all indexes for a merchant environment
```
GET /_cat/indices/catalog_1_{ENV_ID}*?v&h=index,docs.count&s=index
```
*Use this first on any ticket to see what store views exist and their doc counts.*

---

### 1.2 Get total document count for a specific index
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_count
```

---

### 1.3 Fetch a product document directly by product ID
*Use when a product is missing from Live Search — first check if it exists in the index at all. Returns 404 if product is not in the index, not synced, or never exported from Commerce feed.*
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_doc/{PRODUCT_ID}
```

---

### 1.4 Check if a product exists by product ID
*Existence check — use when product is missing from search results. Returns empty hits if product is not indexed.*
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "query": {
    "bool": {
      "filter": [{ "term": { "_id": "{PRODUCT_ID}" } }]
    }
  }
}
```

---

### 1.5 Look up a product by SKU
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "query": {
    "term": { "sku.keyword": "{SKU}" }
  }
}
```

---

### 1.6 Fetch a sample document to inspect field structure
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "query": { "match_all": {} }
}
```

---

### 1.7 Get full field mapping for an index
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_mapping
```
*Zero load — reads cluster metadata only. Use to confirm field types before writing a query.*

---

## TIER 2 — Intermediate: Displayability & Visibility Checks

### 2.1 Check displayable status for a specific product
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "displayable", "deleted", "status", "visibility", "productoverride"],
  "query": {
    "bool": {
      "filter": [{ "term": { "_id": "{PRODUCT_ID}" } }]
    }
  }
}
```

---

### 2.2 Count how many products are displayable in an index
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_count
{
  "query": { "term": { "displayable": true } }
}
```

---

### 2.3 Count products that are NOT displayable
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_count
{
  "query": { "term": { "displayable": false } }
}
```

---

### 2.4 Check if a product has a notDisplayable override set
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "productoverride.notDisplayable", "productoverride.displayable", "displayable"],
  "query": {
    "bool": {
      "filter": [{ "term": { "_id": "{PRODUCT_ID}" } }]
    }
  }
}
```
*`productoverride.notDisplayable` is an array — if non-empty, the product is suppressed for those customer groups / websites.*

---

### 2.5 Find products with a specific notDisplayable value (e.g. suppressed for a customer group)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 10,
  "_source": ["sku", "productoverride.notDisplayable"],
  "query": {
    "term": { "productoverride.notDisplayable": "{CUSTOMER_GROUP}" }
  }
}
```

---

### 2.6 Check deleted flag for a product
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "deleted", "displayable"],
  "query": {
    "bool": {
      "filter": [{ "term": { "_id": "{PRODUCT_ID}" } }]
    }
  }
}
```

---

### 2.7 Count products marked as deleted
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_count
{
  "query": { "term": { "deleted": true } }
}
```

---

### 2.8 Check when a product was last indexed (staleness check)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "sortable.lastIndexedTs"],
  "query": {
    "bool": {
      "filter": [{ "term": { "_id": "{PRODUCT_ID}" } }]
    }
  }
}
```
*If `sortable.lastIndexedTs` is significantly older than other products in the index, the product was not picked up during the last reindex.*

---

### 2.9 Find the most recently indexed product in an index
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "sort": [{ "sortable.lastIndexedTs": "desc" }],
  "_source": ["sku", "sortable.lastIndexedTs"]
}
```

---

### 2.10 Find the oldest indexed product (potential staleness outlier)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 5,
  "sort": [{ "sortable.lastIndexedTs": "asc" }],
  "_source": ["sku", "sortable.lastIndexedTs"],
  "query": { "term": { "displayable": true } }
}
```

---

## TIER 3 — Intermediate: Filterable (Nested) Queries

> **Rule:** All queries on `filterable.*` fields MUST use a `nested` query wrapper.
> Direct `term` on `filterable.categoryIds` without nested will return 0 hits or wrong results.

### 3.1 Check if a product belongs to a category (by category ID)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 5,
  "_source": ["sku", "name", "sortable.lastIndexedTs"],
  "query": {
    "nested": {
      "path": "filterable",
      "query": {
        "term": { "filterable.categoryIds.keyword": "{CATEGORY_ID}" }
      }
    }
  }
}
```

---

### 3.2 Count products in a specific category
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_count
{
  "query": {
    "nested": {
      "path": "filterable",
      "query": {
        "term": { "filterable.categoryIds.keyword": "{CATEGORY_ID}" }
      }
    }
  }
}
```

---

### 3.3 Check if a product is in stock
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "displayable"],
  "query": {
    "bool": {
      "filter": [
        { "term": { "_id": "{PRODUCT_ID}" } },
        {
          "nested": {
            "path": "filterable",
            "query": { "term": { "filterable.inStock": true } }
          }
        }
      ]
    }
  }
}
```

---

### 3.4 Count displayable + in-stock products
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_count
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "displayable": true } },
        {
          "nested": {
            "path": "filterable",
            "query": { "term": { "filterable.inStock": true } }
          }
        }
      ]
    }
  }
}
```

---

### 3.5 Check B2B price for a product (customer-group-specific price)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "viewModel"],
  "query": {
    "bool": {
      "filter": [
        { "term": { "_id": "{PRODUCT_ID}" } },
        {
          "nested": {
            "path": "filterable",
            "query": {
              "range": {
                "filterable.prices_override.{CUSTOMER_GROUP}": { "gt": 0 }
              }
            }
          }
        }
      ]
    }
  }
}
```
*Note: `filterable.prices_override` is excluded from `_source`. Read price values from `viewModel` field instead.*

---

### 3.6 Count products missing a B2B price for a customer group
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_count
{
  "query": {
    "bool": {
      "filter": [{ "term": { "displayable": true } }],
      "must_not": [
        {
          "nested": {
            "path": "filterable",
            "query": {
              "range": {
                "filterable.prices_override.{CUSTOMER_GROUP}": { "gt": 0 }
              }
            }
          }
        }
      ]
    }
  }
}
```

---

### 3.7 List available category IDs in an index
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 0,
  "aggs": {
    "categories": {
      "nested": { "path": "filterable" },
      "aggs": {
        "ids": {
          "terms": { "field": "filterable.categoryIds.keyword", "size": 100 }
        }
      }
    }
  }
}
```

---

## TIER 4 — Advanced: Diagnostic Aggregations & Coverage Checks

### 4.1 Displayable vs total product count (index health check)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 0,
  "aggs": {
    "total": { "value_count": { "field": "displayable" } },
    "displayable_true": {
      "filter": { "term": { "displayable": true } }
    },
    "displayable_false": {
      "filter": { "term": { "displayable": false } }
    },
    "deleted": {
      "filter": { "term": { "deleted": true } }
    }
  }
}
```

---

### 4.2 Statistics signal coverage (ranking data readiness)
*Note: The `Rf` suffix indicates the rolling-window variant (current). Older indexes may use non-`Rf` field names (e.g. `statistics.jlhScore`). If the `Rf` fields return zero coverage, retry with the non-`Rf` names.*
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 0,
  "aggs": {
    "displayable_total": {
      "filter": { "term": { "displayable": true } }
    },
    "has_trending": {
      "filter": {
        "bool": {
          "must": [
            { "term": { "displayable": true } },
            { "exists": { "field": "statistics.jlhScoreRf" } }
          ]
        }
      }
    },
    "has_most_viewed": {
      "filter": {
        "bool": {
          "must": [
            { "term": { "displayable": true } },
            { "exists": { "field": "statistics.productViewSessionsPercentileRankRf" } }
          ]
        }
      }
    },
    "has_most_purchased": {
      "filter": {
        "bool": {
          "must": [
            { "term": { "displayable": true } },
            { "exists": { "field": "statistics.productPurchaseSessionsPercentileRankRf" } }
          ]
        }
      }
    },
    "has_atc": {
      "filter": {
        "bool": {
          "must": [
            { "term": { "displayable": true } },
            { "exists": { "field": "statistics.productAddToCartSessionsPercentileRankRf" } }
          ]
        }
      }
    },
    "has_atc_conversion": {
      "filter": {
        "bool": {
          "must": [
            { "term": { "displayable": true } },
            { "exists": { "field": "statistics.addToCartSessionConversionRateLowerConfidenceRf" } }
          ]
        }
      }
    },
    "has_purchase_conversion": {
      "filter": {
        "bool": {
          "must": [
            { "term": { "displayable": true } },
            { "exists": { "field": "statistics.purchaseSessionConversionRateLowerConfidenceRf" } }
          ]
        }
      }
    }
  }
}
```

---

### 4.3 Recommendations (rfIndicators) coverage
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 0,
  "aggs": {
    "displayable_total": {
      "filter": { "term": { "displayable": true } }
    },
    "has_view_view": {
      "filter": {
        "bool": {
          "must": [
            { "term": { "displayable": true } },
            { "exists": { "field": "rfIndicators.viewViewSkus" } }
          ]
        }
      }
    },
    "has_view_bought": {
      "filter": {
        "bool": {
          "must": [
            { "term": { "displayable": true } },
            { "exists": { "field": "rfIndicators.viewBoughtSkus" } }
          ]
        }
      }
    },
    "has_bought_bought": {
      "filter": {
        "bool": {
          "must": [
            { "term": { "displayable": true } },
            { "exists": { "field": "rfIndicators.boughtBoughtSkus" } }
          ]
        }
      }
    }
  }
}
```

---

### 4.4 Image & text embedding coverage (visual/semantic search readiness)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 0,
  "aggs": {
    "displayable_total": {
      "filter": { "term": { "displayable": true } }
    },
    "has_image_embedding": {
      "filter": {
        "bool": {
          "must": [
            { "term": { "displayable": true } },
            { "exists": { "field": "imageEmbedding" } }
          ]
        }
      }
    },
    "has_product_embedding": {
      "filter": {
        "bool": {
          "must": [
            { "term": { "displayable": true } },
            { "exists": { "field": "productEmbedding" } }
          ]
        }
      }
    },
    "has_text_embedding": {
      "filter": {
        "bool": {
          "must": [
            { "term": { "displayable": true } },
            { "exists": { "field": "textEmbedding" } }
          ]
        }
      }
    }
  }
}
```

---

### 4.5 Staleness distribution — lastIndexedTs histogram
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 0,
  "aggs": {
    "indexed_over_time": {
      "date_histogram": {
        "field": "sortable.lastIndexedTs",
        "calendar_interval": "day",
        "order": { "_key": "desc" }
      }
    }
  }
}
```
*Identify gaps in indexing — days with zero docs indexed indicate a failed or skipped run.*

---

### 4.6 Compare product counts across all store views for a merchant
```
GET /_cat/indices/catalog_1_{ENV_ID}*?v&h=index,docs.count&s=docs.count:desc
```
*Large differences between store views (same env) can indicate a partial reindex or missing store view sync.*

---

### 4.7 Check multiple products at once (batch lookup by product IDs)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 50,
  "_source": ["sku", "displayable", "sortable.lastIndexedTs", "productoverride.notDisplayable"],
  "query": {
    "terms": {
      "_id": ["{PRODUCT_ID_1}", "{PRODUCT_ID_2}", "{PRODUCT_ID_3}"]
    }
  }
}
```

---

### 4.8 Products in a category that are NOT displayable (category gap analysis)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 20,
  "_source": ["sku", "displayable", "deleted", "productoverride.notDisplayable"],
  "query": {
    "bool": {
      "filter": [
        {
          "nested": {
            "path": "filterable",
            "query": {
              "term": { "filterable.categoryIds.keyword": "{CATEGORY_ID}" }
            }
          }
        }
      ],
      "must_not": [
        { "term": { "displayable": true } }
      ]
    }
  }
}
```

---

### 4.9 Full diagnostic snapshot for a single product (all key fields)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": [
    "sku",
    "displayable",
    "deleted",
    "status",
    "visibility",
    "productVisibility",
    "productoverride",
    "sortable.lastIndexedTs",
    "sortable.price",
    "sortable.inStock",
    "viewModel",
    "name",
    "urlKey"
  ],
  "query": {
    "bool": {
      "filter": [{ "term": { "_id": "{PRODUCT_ID}" } }]
    }
  }
}
```

---

## TIER 5 — Advanced: Cross-Index Comparisons

### 5.1 Check if a product is indexed in all store views for a merchant
*Run this for each store view returned by 1.1:*
```
GET /catalog_1_{ENV_ID}_{STORE_CODE_1}_{HASH_1}/_count
{ "query": { "term": { "_id": "{PRODUCT_ID}" } } }

GET /catalog_1_{ENV_ID}_{STORE_CODE_2}_{HASH_2}/_count
{ "query": { "term": { "_id": "{PRODUCT_ID}" } } }
```
*A product missing from some store views but present in others indicates a partial sync failure.*

---

### 5.2 Compare displayable state across store views for one product
*Run for each store view — look for inconsistencies:*
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "displayable", "productoverride.notDisplayable"],
  "query": { "term": { "_id": "{PRODUCT_ID}" } }
}
```

---

### 5.3 Check index creation date / last reindex timing
```
GET /_cat/indices/catalog_1_{ENV_ID}*?v&h=index,docs.count,docs.deleted,store.size,creation.date.string&s=index
```
*`creation.date.string` shows when the index was created (a new hash = a full reindex happened). Compare against ticket timeline.*

---

### 5.4 Find products indexed (or updated) within a specific time window
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_count
{
  "query": {
    "range": {
      "sortable.lastIndexedTs": {
        "gte": "{START_DATE}",
        "lte": "{END_DATE}"
      }
    }
  }
}
```
*Use ISO format dates e.g. `2026-05-20T00:00:00` or relative like `now-24h`. Use to confirm whether a batch reindex reached a product.*

---

### 5.5 Find products NOT updated since a given date (stale products)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 10,
  "_source": ["sku", "sortable.lastIndexedTs"],
  "query": {
    "bool": {
      "filter": [{ "term": { "displayable": true } }],
      "must_not": [
        { "range": { "sortable.lastIndexedTs": { "gte": "{CUTOFF_DATE}" } } }
      ]
    }
  },
  "sort": [{ "sortable.lastIndexedTs": "asc" }]
}
```

---

## TIER 6 — Text Search & Keyword Investigation

### 6.1 Search products by name/keyword (simulate what Live Search executes)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 10,
  "_source": ["sku", "name", "displayable", "urlKey"],
  "query": {
    "bool": {
      "must": [
        { "match": { "name": "{SEARCH_KEYWORD}" } }
      ],
      "filter": [
        { "term": { "displayable": true } }
      ]
    }
  }
}
```
*Use when merchant says "product doesn't appear when searching for X". Check if name/searchable fields contain the keyword.*

---

### 6.2 Search across all searchable fields for a keyword
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 10,
  "_source": ["sku", "name", "displayable"],
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "{SEARCH_KEYWORD}",
            "fields": ["name", "searchable.name", "searchable.brand", "searchable.sku", "searchable.keywords"],
            "type": "best_fields"
          }
        }
      ],
      "filter": [{ "term": { "displayable": true } }]
    }
  }
}
```
*Avoid `searchable.*` wildcard — the `searchable` object has 88 sub-fields; expanding all of them in one query is expensive and may hit cluster field-count limits. Name the specific fields you care about instead.*

---

### 6.3 Check what searchable field content is stored for a product
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "name", "searchable"],
  "query": {
    "bool": {
      "filter": [{ "term": { "_id": "{PRODUCT_ID}" } }]
    }
  }
}
```
*Check if `searchable.name`, `searchable.brand`, `searchable.sku` etc. are populated. Empty searchable = product won't be found by keyword search.*

---

### 6.4 Check autocomplete / suggest field for a product
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "suggest"],
  "query": {
    "bool": {
      "filter": [{ "term": { "_id": "{PRODUCT_ID}" } }]
    }
  }
}
```

---

### 6.5 Run an autocomplete query (simulate typeahead)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "suggest": {
    "product_suggest": {
      "prefix": "{SEARCH_PREFIX}",
      "completion": {
        "field": "suggest",
        "size": 10
      }
    }
  }
}
```

---

## TIER 7 — Price Investigation

### 7.1 Check all price-related fields for a product
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": [
    "sku",
    "sortable.price",
    "viewModel"
  ],
  "query": {
    "bool": {
      "filter": [{ "term": { "_id": "{PRODUCT_ID}" } }]
    }
  }
}
```
*`viewModel` contains per-customer-group prices and overrides. `filterable.prices_override` and `prices_sortable_*` are excluded from `_source` — never readable directly.*

---

### 7.2 Count displayable products with no price (sortable.price missing or zero)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_count
{
  "query": {
    "bool": {
      "filter": [{ "term": { "displayable": true } }],
      "must_not": [
        { "exists": { "field": "sortable.price" } }
      ]
    }
  }
}
```

---

### 7.3 Count products with a B2B price set for a customer group
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_count
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "displayable": true } },
        {
          "nested": {
            "path": "filterable",
            "query": {
              "range": { "filterable.prices_override.{CUSTOMER_GROUP}": { "gt": 0 } }
            }
          }
        }
      ]
    }
  }
}
```

---

### 7.4 Find a product with B2B price and read it via viewModel
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "viewModel", "sortable.price"],
  "query": {
    "bool": {
      "filter": [
        { "term": { "_id": "{PRODUCT_ID}" } }
      ]
    }
  }
}
```
*Request the whole `viewModel` object — do NOT use sub-path like `viewModel.productOverrides.{CUSTOMER_GROUP}` in `_source`. `viewModel` is `enabled: false` in the mapping (stored as a raw JSON blob, not indexed as individual fields), so sub-path `_source` filtering is unreliable. Parse the customer group key from the returned `viewModel` object.*

---

## TIER 8 — Product Type & Variant Investigation

### 8.1 Check if a configurable product has child SKUs indexed
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "searchable.childrenSkus", "searchable.childrenNames", "searchable.childrenUrlKeys"],
  "query": {
    "bool": {
      "filter": [{ "term": { "_id": "{PRODUCT_ID}" } }]
    }
  }
}
```
*If `childrenSkus` is empty, child variants are not indexed under this parent — Live Search won't return the parent for variant-specific searches.*

---

### 8.2 Count configurable vs simple vs bundle vs grouped products
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 0,
  "aggs": {
    "by_product_type": {
      "nested": { "path": "filterable" },
      "aggs": {
        "types": {
          "terms": { "field": "filterable.commerceProductType.keyword", "size": 20 }
        }
      }
    }
  }
}
```

---

### 8.3 Find all bundle products in an index
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_count
{
  "query": {
    "nested": {
      "path": "filterable",
      "query": { "term": { "filterable.isBundle": true } }
    }
  }
}
```

---

### 8.4 Find which parent product owns a child SKU
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 5,
  "_source": ["sku", "name", "searchable.childrenSkus", "displayable"],
  "query": {
    "term": { "searchable.childrenSkus": "{SKU}" }
  }
}
```
*Use when a merchant reports a child variant SKU is not returning results. `searchable.childrenSkus` is a keyword array inside the parent document — this query finds the parent that owns this child. Works for configurable, grouped, and bundle parents. Returns 0 hits if no parent has this SKU as a child.*

---

### 8.5 Check if a child variant is indexed as its own separate document
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "displayable", "sortable.lastIndexedTs"],
  "query": {
    "term": { "sku.keyword": "{SKU}" }
  }
}
```
*In Live Search, child variants are typically NOT indexed as separate documents — only the parent is. If this returns a hit, the merchant is indexing children as standalone products (unusual). If it returns 0 hits for a child SKU, that is expected — look for the parent via 8.4 instead.*

---

### 8.6 Count configurable products that have no children indexed
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_count
{
  "query": {
    "bool": {
      "filter": [
        {
          "nested": {
            "path": "filterable",
            "query": { "term": { "filterable.commerceProductType.keyword": "configurable" } }
          }
        }
      ],
      "must_not": [
        { "exists": { "field": "searchable.childrenSkus" } }
      ]
    }
  }
}
```
*A configurable product with no `childrenSkus` is an index gap — Live Search will not return it for any variant-attribute filters (size, color, etc.). This count should ideally be 0.*

---

### 8.7 Inspect a grouped product — members and pricing
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": [
    "sku", "name", "displayable",
    "searchable.childrenSkus", "searchable.childrenNames",
    "sortable.price", "viewModel"
  ],
  "query": {
    "nested": {
      "path": "filterable",
      "query": { "term": { "filterable.isGrouped": true } }
    }
  }
}
```
*Grouped product members are stored in `searchable.childrenSkus` (same pattern as configurable). `viewModel.type` will be `"grouped"`. `sortable.price` is typically absent for grouped products — price is determined by the individual member products. Use `viewModel.productOverrides` for per-group price ranges.*

---

### 8.8 Inspect a bundle product — options, items, and pricing
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": [
    "sku", "name", "displayable",
    "searchable.childrenSkus", "searchable.childrenNames",
    "sortable.price", "viewModel"
  ],
  "query": {
    "nested": {
      "path": "filterable",
      "query": { "term": { "filterable.isBundle": true } }
    }
  }
}
```
*Bundle option SKUs are stored in `searchable.childrenSkus`. `sortable.price` may reflect the minimum bundle price or be absent — bundle price is dynamic based on selected options. Read `viewModel.productOverrides` for per-group price ranges. `viewModel.type` will be `"bundle"`.*

---

### 8.9 Count virtual and downloadable products
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 0,
  "aggs": {
    "virtual_and_downloadable": {
      "nested": { "path": "filterable" },
      "aggs": {
        "types": {
          "terms": {
            "field": "filterable.commerceProductType.keyword",
            "include": ["virtual", "downloadable"],
            "size": 10
          }
        }
      }
    }
  }
}
```
*Virtual products have no shipping. Downloadable products are digital files. Both behave like simple products in the index (no children, `isBundle: false`, `isGrouped: false`). If this returns 0 for both, the merchant has no virtual or downloadable products indexed.*

---

## TIER 9 — Attribute & Facet Investigation

### 9.1 Check what values a filterable attribute has in an index
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 0,
  "aggs": {
    "attribute_values": {
      "nested": { "path": "filterable" },
      "aggs": {
        "values": {
          "terms": { "field": "filterable.{ATTRIBUTE_CODE}.keyword", "size": 50 }
        }
      }
    }
  }
}
```
*Replace `{ATTRIBUTE_CODE}` with the Magento attribute code e.g. `brand`, `color`, `size`, `gender`.*

---

### 9.2 Check if a specific attribute is populated for a product
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": false,
  "query": {
    "bool": {
      "filter": [
        { "term": { "_id": "{PRODUCT_ID}" } },
        {
          "nested": {
            "path": "filterable",
            "query": { "exists": { "field": "filterable.{ATTRIBUTE_CODE}" } }
          }
        }
      ]
    }
  }
}
```

---

### 9.3 Count products missing a specific filterable attribute
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_count
{
  "query": {
    "bool": {
      "filter": [{ "term": { "displayable": true } }],
      "must_not": [
        {
          "nested": {
            "path": "filterable",
            "query": { "exists": { "field": "filterable.{ATTRIBUTE_CODE}" } }
          }
        }
      ]
    }
  }
}
```

---

### 9.4 Check visibility distribution in an index
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 0,
  "aggs": {
    "visibility_values": {
      "terms": { "field": "visibility.keyword", "size": 10 }
    },
    "product_visibility_values": {
      "terms": { "field": "productVisibility.keyword", "size": 10 }
    }
  }
}
```
*Confirmed real values from testing env:*
- *`visibility` stores full strings: `"Catalog, Search"`, `"Search"`, `"Not Visible Individually"`, `"Catalog"`*
- *`productVisibility` stores enum strings: `"CATALOG_AND_SEARCH"`, `"SEARCH"`, `"NOT_VISIBLE"`, `"CATALOG"`*

---

### 9.5 Find products with unexpected visibility (not visible in search)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_count
{
  "query": {
    "bool": {
      "filter": [{ "term": { "displayable": true } }],
      "must_not": [
        {
          "terms": {
            "visibility.keyword": ["Catalog, Search", "Search"]
          }
        }
      ]
    }
  }
}
```
*Confirmed: `visibility` stores label strings not integers. Valid values for Live Search: `"Catalog, Search"` and `"Search"`. Products with `"Not Visible Individually"` or `"Catalog"` should not appear in search results.*

---

## TIER 10 — Images Investigation

### 10.1 Check if a product has images indexed
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "images"],
  "query": {
    "bool": {
      "filter": [{ "term": { "_id": "{PRODUCT_ID}" } }]
    }
  }
}
```

---

### 10.2 Count products with no images
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_count
{
  "query": {
    "bool": {
      "filter": [{ "term": { "displayable": true } }],
      "must_not": [
        { "nested": { "path": "images", "query": { "match_all": {} } } }
      ]
    }
  }
}
```

---

## TIER 11 — Index Health & Settings

### 11.1 Check index settings (shards, replicas, refresh interval)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_settings
```

---

### 11.2 Check index aliases (confirm which alias points to this index)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_alias
```
*An index with no alias is not actively serving queries — the alias points to a different (newer) index.*

---

### 11.3 Check index stats (indexing rate, search rate, doc count)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_stats/indexing,search,docs
```

---

### 11.4 Check for ongoing indexing tasks on an index
```
GET /_cat/tasks?v&detailed&h=action,description,start_time,running_time,node
```
*Use when a reindex appears stuck or when a merchant reports products not updating.*

---

## TIER 12 — Schema Variant: Statistics/Ranking Index (product.default.* path)

**Not confirmed in any tested environment.** In all three testing env indexes (standard, B2B, vijay_sales statistics variant), `displayable` is a top-level field — the `product.default.*` path was NOT present. These templates exist as a precaution: before using them, run template 1.7 (`_mapping`) and grep the result for `product.default`. Only use Tier 12 if you see `product.default.displayable` in the actual mapping.

### 12.1 Check displayable status (product.default.* schema)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["product.default", "statistics"],
  "query": {
    "bool": {
      "filter": [{ "term": { "_id": "{PRODUCT_ID}" } }]
    }
  }
}
```

---

### 12.2 Count displayable products (product.default.* schema)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_count
{
  "query": { "term": { "product.default.displayable": true } }
}
```

---

### 12.3 Check if statistics signals exist for a product (product.default.* schema)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["product.default.displayable", "statistics"],
  "query": {
    "bool": {
      "filter": [
        { "term": { "_id": "{PRODUCT_ID}" } }
      ]
    }
  }
}
```

---

## TIER 13 — Product Metadata & Permission Fields

### 13.1 Check store view and website assignment for a product
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "viewModel"],
  "query": {
    "bool": {
      "filter": [{ "term": { "_id": "{PRODUCT_ID}" } }]
    }
  }
}
```
*`storeViewCode` and `websiteCode` are NOT top-level fields — they live inside `viewModel.storeViewCode` and `viewModel.websiteCode`. Fetch `viewModel` to read them. Use when a product appears in one store view but not another.*

---

### 13.2 Check customer group permissions for a product
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "displayable", "productoverride.notDisplayable", "productoverride.displayable", "viewModel"],
  "query": {
    "bool": {
      "filter": [{ "term": { "_id": "{PRODUCT_ID}" } }]
    }
  }
}
```
*There is no `customerGroupPermissions` field. Customer group visibility is controlled by `productoverride.notDisplayable` (array of hashes for suppressed groups) and `productoverride.displayable` (array of hashes for explicitly allowed groups). For the actual per-group prices and `addToCartAllowed`, read `viewModel.productOverrides` — keys are SHA1 group hashes plus `"NLI"` for not-logged-in.*

---

### 13.3 Check regular_price field (older feed format)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "regular_price", "sortable.price", "viewModel"],
  "query": {
    "bool": {
      "filter": [{ "term": { "_id": "{PRODUCT_ID}" } }]
    }
  }
}
```
*Some indexes use `regular_price` as a top-level field (older feed format) instead of `sortable.price`. Check both — if `sortable.price` is missing, try `regular_price`.*

---

### 13.4 Count products missing regular_price (older feed format)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_count
{
  "query": {
    "bool": {
      "filter": [{ "term": { "displayable": true } }],
      "must_not": [
        { "exists": { "field": "regular_price" } }
      ]
    }
  }
}
```

---

## TIER 14 — Category Data Alternate Paths

Two different fields store category membership depending on index schema version. Always check the mapping (1.7) to confirm which is present.

### 14.1 Check category membership via categoryData.categoryId (nested)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 5,
  "_source": ["sku", "name"],
  "query": {
    "nested": {
      "path": "categoryData",
      "query": {
        "term": { "categoryData.categoryId.keyword": "{CATEGORY_ID}" }
      }
    }
  }
}
```
*Use when `filterable.categoryIds` returns no results — this is the alternate category path used in some index versions.*

---

### 14.2 Check category membership via top-level categories field
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 5,
  "_source": ["sku", "name", "categories"],
  "query": {
    "term": { "categories": "{CATEGORY_ID}" }
  }
}
```
*`categories` as a top-level field was NOT found in any tested environment (standard, B2B, vijay_sales). Category data is stored in `categoryData` (nested) and `filterable.categoryIds` (nested). Try template 14.1 or 3.1 first. Use 14.2 only if the mapping shows a top-level `categories` field.*

---

### 14.3 Inspect all category data for a product (all paths)
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "categoryData"],
  "query": {
    "bool": {
      "filter": [{ "term": { "_id": "{PRODUCT_ID}" } }]
    }
  }
}
```
*`categoryData` is confirmed present in all tested environments. Returns each category with `categoryId`, `categoryPath`, and `productPosition`. The top-level `categories` field is not confirmed — omit it.*

---

### 14.4 Check product position within a category
```
GET /catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}/_search
{
  "size": 1,
  "_source": ["sku", "categoryData"],
  "query": {
    "bool": {
      "filter": [
        { "term": { "_id": "{PRODUCT_ID}" } }
      ]
    }
  }
}
```
*`categoryData.productPosition` holds the manual sort position. A value of 0 or null means no manual position is set — product uses default sort.*

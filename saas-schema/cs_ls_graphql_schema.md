# CS/LS GraphQL Schema — All 8 Queries

## About This Document

**Purpose:** Ground truth for all CS/LS/PREX GraphQL queries available at `catalog-service.adobe.io/graphql`.
**Use this when:** You need to know query args, field names, response shape, or gotchas before calling the API.
**Source:** Verified 2026-05-27 against a live merchant environment (identifier redacted).
**Key rule:** Response structure is Adobe-defined and stable across all merchant environments. Only values differ.

---

## Endpoint and Auth Headers

```
POST https://catalog-service.adobe.io/graphql
Content-Type: application/json
Magento-Environment-Id: <UUID>
Magento-Store-Code: <store_code>
Magento-Store-View-Code: <store_view_code>
Magento-Website-Code: <website_code>
X-Api-Key: search_gql
Magento-Customer-Group: <SHA1(customer_group_id)>   # optional — for group pricing
```

Customer group SHA1 examples:
- Group 0 (NOT LOGGED IN): `b6589fc6ab0dc82cf12099d1c2d40ab994e8410c`
- Group 1 (General): `356a192b7913b04c54574d18c28d46e6395428ab`
- Group 2 (Wholesale): `da4b9237bacccdf19c0760cab7aec4a8359010b0`
- Group 3 (Retailer): `77de68daecd823babbb58edb1c8e14d7106e83bb`

---

## All 8 Available Queries

| Query | Description | Origin |
|---|---|---|
| `products(skus)` | Fetch by SKU — returns SimpleProductView or ComplexProductView | CS |
| `productSearch(phrase, ...)` | Live Search — full-text + filter + sort | LS |
| `refineProduct(sku, optionIds)` | Resolve configurable → child SimpleProductView | CS |
| `variants(sku)` | All variant combos for a configurable | CS |
| `attributeMetadata` | Sortable + filterable attribute list | LS |
| `categories(ids, roles, subtree)` | Category tree (ACaaS — unreliable when count not synced) | CS |
| `recommendations(pageType, ...)` | PREX recs via GraphQL | PREX |
| `recommendationsByUnitIds(unitIds, ...)` | Fetch specific rec units by unitId | PREX |

---

## products(skus) — SimpleProductView vs ComplexProductView

**Args:** `skus: [String!]!`

Returns `SimpleProductView` for simple/virtual/downloadable. Returns `ComplexProductView` for configurable/bundle parent.

SimpleProductView has `price { final, regular }` — NOT `priceRange`.
ComplexProductView has `priceRange { minimum, maximum }` — NOT `price`.

```graphql
{ products(skus: ["24-MB01", "MH01"]) {
    __typename sku name inStock lastModifiedAt
    ... on SimpleProductView {
      price { final { amount { value currency } } regular { amount { value currency } } }
      urlKey categories attributes { name value }
    }
    ... on ComplexProductView {
      priceRange {
        minimum { final { amount { value currency } } regular { amount { value currency } } }
        maximum { final { amount { value currency } } regular { amount { value currency } } }
      }
      urlKey categories
      options { id title required values { id title } }
    }
} }
```

`options[].values[].id` — base64-encoded option value IDs used in `refineProduct(optionIds: [...])`.

---

## products(skus) — PREX _entities federation error

All products/productSearch queries may return these errors alongside real data — safe to ignore:
```json
{ "message": "Validation error (UnknownType) : Unknown type '_Any'", "extensions": { "service": "prex" } }
{ "message": "Validation error (FieldUndefined@[_entities]) : ...", "extensions": { "service": "prex" } }
```
Data is still returned correctly. PREX subgraph federation quirk — non-breaking.

---

## productSearch(phrase, ...) — Live Search

**Args:** `phrase: String!` (required), `page_size: Int` (default 20), `current_page: Int` (default 1), `filter: [SearchClauseInput!]`, `sort: [ProductSearchSortInput!]`, `context: QueryContextInput`

```graphql
{ productSearch(phrase: "hoodie", page_size: 10,
    filter: [{ attribute: "inStock", eq: "true" }, { attribute: "price", range: { from: 20.0, to: 100.0 } }],
    sort: [{ attribute: "price", direction: ASC }],
    context: { customerGroup: "356a192b7913b04c54574d18c28d46e6395428ab" }
  ) {
    total_count
    items {
      productView { __typename sku name inStock
        ... on SimpleProductView  { price { final { amount { value currency } } } }
        ... on ComplexProductView { priceRange { minimum { final { amount { value currency } } } } }
      }
      product { sku price_range { minimum_price { final_price { value currency } } } }
    }
    aggregations { attribute label buckets {
      ... on ScalarBucket { id title count }
      ... on RangeBucket  { title count }
      ... on StatsBucket  { min max }
    } }
    page_info { current_page page_size total_pages }
} }
```

**SearchClauseInput operators:** `eq`, `in: [String]`, `range: { from: Float, to: Float }`, `startsWith`, `contains`
**SortEnum:** `ASC` | `DESC`
**QueryContextInput:** `{ customerGroup: String!, userViewHistory: [ViewHistory!] }`

---

## refineProduct(sku, optionIds) — Resolve Configurable to Child

**Args:** `sku: String!`, `optionIds: [String!]!`

optionIds = base64 values from `products(skus)` → ComplexProductView.options[].values[].id

Always returns `SimpleProductView` (child product) with exact price and stock.

```graphql
{ refineProduct(sku: "MH01", optionIds: ["Y29uZmlndXJhYmxlLzkzLzQ5", "Y29uZmlndXJhYmxlLzE1OS8xNjg="]) {
    __typename sku name inStock
    price { final { amount { value currency } } regular { amount { value currency } } }
} }
```

Real response: `{ "sku": "MH01-M-Black", "inStock": true, "price": { "final": { "amount": { "value": 52.0, "currency": "USD" } } } }`

---

## variants(sku) — All Variant Combos

**Args:** `sku: String!` (configurable parent only)

Returns selections (base64 option IDs) + child product data per variant.

```graphql
{ variants(sku: "MH01") {
    variants {
      selections   # ["Y29uZmlndXJhYmxlLzkzLzQ5", "Y29uZmlndXJhYmxlLzE1OS8xNjg="]
      product { sku name inStock price { final { amount { value currency } } } }
    }
} }
```

`selections` IDs match `ComplexProductView.options[].values[].id` — same base64 values.

---

## attributeMetadata — Sortable and Filterable Attributes

**Args:** none

CRITICAL: field name is `attribute` NOT `code`. Using `code` causes GRAPHQL_VALIDATION_FAILED.

```graphql
{ attributeMetadata {
    sortable         { attribute frontendInput label numeric }
    filterableInSearch { attribute frontendInput label numeric }
} }
```

Real response (sortable): `name` (text), `position` (numeric), `relevance` (numeric), `price` (price/numeric)
Real response (filterable): `visibility`, `categoryPath`, `url_key`, `categoryIds`, `price`, `inStock`, `sku`, custom attributes

Use `attribute` values directly as filter/sort attribute codes in productSearch.

---

## categories(ids, roles, subtree) — Category Tree (ACaaS)

**Args:** `ids: [ID!]` (optional), `roles: [String!]` (optional), `subtree: { startLevel: Int!, depth: Int! }` (optional)

WARNING: `count` field is NON-NULL. If category-product associations not synced in LS index, returns null for all categories with error: `Cannot return null for non-nullable field CategoryView.count`. Use gRPC GetCategories instead when this fails.

```graphql
{ categories(ids: ["3", "4", "11"]) {
    id name title urlKey urlPath path level parentId position
    availableSortBy defaultSortBy count roles
    children   # [String] — list of child category ID strings, NOT nested objects
} }
```

`children` is `[String]` (IDs only) — cannot select subfields on it.

---

## recommendations(pageType, ...) — PREX via GraphQL

CRITICAL: top-level field is `results` NOT `units`. Using `units` causes GRAPHQL_VALIDATION_FAILED.

**PageType enum:** `CMS` | `Cart` | `Category` | `Checkout` | `PageBuilder` | `Product`

```graphql
{ recommendations(pageType: Product, currentSku: "24-MB01") {
    results {
      unitId unitName typeId storefrontLabel totalProducts pageType displayOrder
      productsView {
        __typename
        ... on SimpleProductView  { sku name inStock price { final { amount { value currency } } } }
        ... on ComplexProductView { sku name }
      }
    }
    totalResults
} }
```

Real response: `unitId`, `unitName`, `typeId` (e.g. "most-purchased"), `storefrontLabel`, `totalProducts: 0` (no behavioral data in test env), `productsView: []`

Other args: `cartSkus: [String]`, `category: String`, `userViewHistory: [ViewHistory]`, `userPurchaseHistory: [PurchaseHistory]`, `currentProduct: { sku, price }`

---

## recommendationsByUnitIds(unitIds, ...) — Fetch Specific Rec Units

**Args:** `unitIds: [String!]!` (REQUIRED), `currentSku`, `cartSkus`, `userViewHistory`, `userPurchaseHistory`

Response shape identical to `recommendations` — same `Recommendations` type with `results: [RecommendationUnit]` and `totalResults: Int`.

Get unitIds from `recommendations(pageType: ...)` first → extract `results[].unitId` values.

```graphql
{ recommendationsByUnitIds(unitIds: ["11111111-1111-4111-8111-111111111111"], currentSku: "24-MB01") {
    results { unitId unitName typeId storefrontLabel totalProducts productsView { __typename ... on SimpleProductView { sku name } } }
    totalResults
} }
```

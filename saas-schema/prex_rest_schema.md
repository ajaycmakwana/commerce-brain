# PREX REST Schema

## Endpoint and Auth

```
POST https://commerce.adobe.io/recs/v1/precs/preconfigured
Content-Type: application/json
X-Api-Key: recs_open
```

No Bearer token or Magento headers required.

---

## Request Body

```json
{
  "environmentId": "bbfd3c12-0280-4444-a055-8d1e5281e39e",
  "alternateEnvironmentId": "",
  "storeCode": "main_website_store",
  "storeViewCode": "default",
  "websiteCode": "base",
  "pageType": "Product",
  "category": "",
  "currentSku": "24-MB01",
  "cartSkus": [],
  "userViewHistorySkus": [],
  "userViewHistory": [],
  "userPurchaseHistory": [],
  "defaultStoreViewCode": "",
  "customerGroupCode": ""
}
```

**pageType values:** `"CMS"` | `"Product"` | `"Category"` | `"Cart"` | `"Checkout"`

**Optional behavioral context:**
- `currentSku` — SKU of product currently being viewed (for Product page recs)
- `cartSkus` — array of SKUs currently in cart
- `category` — category path string (for Category page recs)
- `userViewHistory` — array of `{ date, sku, units }` objects
- `userPurchaseHistory` — array of `{ date, sku, units }` objects
- `customerGroupCode` — SHA1 of customer group ID for group-specific recs

---

## Response Shape

```json
{
  "totalResults": 3,
  "results": [
    {
      "unitId": "e6c3f869-1ff4-4060-bc87-6da01c2415d3",
      "unitName": "Most Purchased",
      "unitType": "primary",
      "searchTime": 12,
      "totalProducts": 0,
      "primaryProducts": 0,
      "backupProducts": 0,
      "products": [],
      "pageType": "Product",
      "typeId": "most-purchased",
      "storefrontLabel": "Most Purchased",
      "pagePlacement": "",
      "displayNumber": "03",
      "displayOrder": 3
    }
  ]
}
```

---

## typeId Values

| typeId | Description |
|---|---|
| `most-purchased` | Products most frequently purchased across the store |
| `recently-viewed` | Products recently viewed by the shopper |
| `most-viewed` | Products most viewed across the store |
| `trending` | Trending products based on recent activity |
| `recommended-for-you` | Personalized recommendations for the shopper |
| `more-like-this` | Products similar to the current product (requires currentSku) |
| `visual-similarity` | Visually similar products (requires currentSku) |

---

## Why products[] Is Empty

`products[]` is empty when no Adobe Analytics behavioral events have been submitted for the environment.

PREX reads the CS product index to populate `products[]` — if CS has no products indexed, `products[]` stays empty even when behavioral data exists.

In test environments without Adobe Analytics event collection, `totalProducts: 0` and `products: []` is expected.

---

## Relationship to CS GraphQL recommendations

Both PREX REST and CS GraphQL `recommendations` / `recommendationsByUnitIds` return the same `unitId`, `typeId`, and `storefrontLabel` values for the same environment.

| Use case | API |
|---|---|
| Get all configured rec units for a pageType | PREX REST `precs/preconfigured` |
| Get rec units with `productsView` inline (CS product data) | CS GraphQL `recommendations(pageType: ...)` |
| Fetch a specific rec unit by known unitId with products | CS GraphQL `recommendationsByUnitIds(unitIds: [...])` |

---

## unitId Usage Pattern

1. Call PREX REST → get `results[].unitId` values for the page type
2. Pass unitId to `recommendationsByUnitIds` in CS GraphQL to get full `productsView` with price/stock inline

```graphql
{ recommendationsByUnitIds(unitIds: ["e6c3f869-1ff4-4060-bc87-6da01c2415d3"], currentSku: "24-MB01") {
    results {
      unitId unitName typeId storefrontLabel totalProducts
      productsView {
        __typename
        ... on SimpleProductView  { sku name inStock price { final { amount { value currency } } } }
        ... on ComplexProductView { sku name priceRange { minimum { final { amount { value currency } } } } }
      }
    }
    totalResults
} }
```

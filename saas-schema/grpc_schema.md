# CS gRPC Schema — All Services and Methods

## Host and Transport

```
Host: catalog-service-grpc.corp.ethos340-prod-va6.ethos.adobe.net:443
Protocol: gRPC over TLS
CLI: grpcurl -insecure -d '{...}' <host>:443 <Service/Method>
```

## All Available Services

```
CategoryService                                                    ⚠️ Deprecated
ProductOverrideService
ProductService                                                     (legacy)
com.adobe.commerce.catalog.category.api.v1.CategoryService
com.adobe.commerce.catalog.category.permission.api.v1.CategoryPermissionService
com.adobe.commerce.catalog.product.api.v2.ProductService
com.adobe.commerce.catalog.product.variant.api.v2.ProductVariantService
com.adobe.commerce.catalog.v1.VariantService                      ⚠️ Deprecated
com.adobe.commerce.ccdm.category.api.v1.CategoryService
com.adobe.commerce.ccdm.pricing.api.v1.PriceBookService
grpc.health.v1.Health
grpc.reflection.v1alpha.ServerReflection
```

---

## store_view_id shape (reused by most services)

```json
{
  "environment_id": "<UUID>",
  "website_code": "base",
  "store_code": "main_website_store",
  "store_view_code": "default"
}
```

---

## ProductOverrideService

Primary service for querying product override data — permissions, displayability, pricing per customer group.

### Methods

| Method | Request | Response | Notes |
|---|---|---|---|
| `GetProductOverrides` | `GetProductOverridesBySkuAndScopeBatchRequest` | stream `GetProductOverrideBatchResponse` | By SKU + full scope (env + website + customer group) |
| `GetProductOverridesBySkusAndWebsite` | `GetProductOverridesBySkuAndWebsiteBatchRequest` | stream `GetProductOverrideBatchResponse` | By SKU + website (all groups) |
| `GetProductOverridesByWebsite` | `GetProductOverridesByWebsiteBatchRequest` | stream `GetProductOverrideBatchPageResponse` | ⚠️ Deprecated |

### Request: GetProductOverridesBySkuAndScopeBatchRequest

```json
{
  "scope": {
    "environment_id": "<UUID>",
    "website_code": "base",
    "customer_group_code": "356a192b7913b04c54574d18c28d46e6395428ab"
  },
  "skus": ["24-MB01"]
}
```

### Request: GetProductOverridesBySkuAndWebsiteBatchRequest

```json
{
  "environment_id": "<UUID>",
  "website_code": "base",
  "skus": ["24-MB01"],
  "filter_virtual_cgs": false
}
```

`filter_virtual_cgs: true` — filters out virtual/system customer groups from results.

### Response: ProductOverride (core record)

```json
{
  "environmentId": "<UUID>",
  "websiteCode": "base",
  "customerGroupCode": "356a192b7913b04c54574d18c28d46e6395428ab",
  "prices": {
    "minimum": { "regular": 34.0, "final": 34.0 },
    "maximum": { "regular": 34.0, "final": 34.0 }
  },
  "lastModifiedTs": "...",
  "productId": "2048",
  "sku": "24-MB01",
  "deleted": false,
  "displayable": true,
  "priceDisplayable": true,
  "addToCartAllowed": true,
  "currency": "USD",
  "api_version": "...",
  "tier_prices": []
}
```

**Key fields:**

| Field | Value | Meaning |
|---|---|---|
| `displayable` | `true` | Product visible for this customer group |
| `displayable` | `false` | Product hidden (notDisplayable) for this group |
| `displayable` | `null` | Not set — uses default store config |
| `deleted` | `true` | Override record removed from SaaS |
| `addToCartAllowed` | `true` | Customer group can add to cart |

### grpcurl Examples

```bash
# Fetch overrides for a specific SKU + customer group
grpcurl -insecure \
  -d '{"scope":{"environment_id":"{env_id}","website_code":"{website_code}","customer_group_code":"{group_hash}"},"skus":["{SKU}"]}' \
  catalog-service-grpc.corp.ethos340-prod-va6.ethos.adobe.net:443 \
  ProductOverrideService/GetProductOverrides

# Fetch overrides for a SKU across all groups on a website
grpcurl -insecure \
  -d '{"environment_id":"{env_id}","website_code":"{website_code}","skus":["{SKU}"],"filter_virtual_cgs":false}' \
  catalog-service-grpc.corp.ethos340-prod-va6.ethos.adobe.net:443 \
  ProductOverrideService/GetProductOverridesBySkusAndWebsite
```

---

## ProductService (legacy)

### Methods

| Method | Request | Response | Notes |
|---|---|---|---|
| `GetProducts` | `GetProductBatchRequest` | stream `GetProductBatchResponse` | Fetch product data by store view |
| `GetChildProducts` | `GetChildProductsRequest` | stream `GetChildProductsResponse` | Fetch child products of a parent |
| `GetUpdatedProductSkus` | `GetUpdatedProductSkusRequest` | stream `GetUpdatedProductSkusResponse` | SKUs updated within a time range |

### Request: GetProductBatchRequest

```json
{
  "products_by_store_view": [{
    "store_view_id": { "environment_id": "...", "website_code": "base", "store_code": "main_website_store", "store_view_code": "default" },
    "skus": ["24-MB01", "MH01"]
  }],
  "mask": null
}
```

`mask` — optional `google.protobuf.FieldMask` to select specific fields to return.

### Request: GetChildProductsRequest

```json
{
  "store_view_id": { "environment_id": "...", "website_code": "base", "store_code": "main_website_store", "store_view_code": "default" },
  "request_parent_sku": { "sku": "MH01" }
}
```

Also supports `request_token` (pagination token) instead of `request_parent_sku`.

### Response: GetChildProductsResponse (paginated)

```json
{
  "child_products": [ /* Product records */ ],
  "continuation_token": "..."
}
```

Pass `continuation_token` back as `request_token` for next page.

### Request: GetUpdatedProductSkusRequest

```json
{
  "store_view_id": { "environment_id": "...", "website_code": "base", "store_code": "main_website_store", "store_view_code": "default" },
  "request_time_range": {
    "from": "2026-05-26T00:00:00Z",
    "to": "2026-05-27T00:00:00Z"
  }
}
```

**CRITICAL:** Max range = **86400 seconds (24h)**. Returns `InvalidArgument` if exceeded.

Also supports `request_token` for pagination.

### Response: GetUpdatedProductSkusResponse (paginated)

```json
{
  "updated_product_skus": [{ "sku": "24-MB01", "..." : "..." }],
  "continuation_token": "..."
}
```

### Product response fields

`sku`, `type`, `lastModifiedTs`, `lastExportTs`, `lastPublishedTs`,
`priceHash`, `oosHash`, `contentHash`, `productHash`,
`name`, `urlKey`, `visibility`, `displayable`, `buyable`, `inStock`,
`categories` (array of category ID strings),
`categoryData` (array of `{ categoryId, categoryPath, productPosition }`),
`links` (array of `{ sku, type }`),
`urlRewrites`, `status`, `product_visibility`

GetChildProducts response additionally includes:
- `parents`: array of `{ sku, type }`
- `attributes`: array of `{ name, values: [] }` — configurable option values for this child

Note: child products always have `visibility = NOT_VISIBLE_INDIVIDUALLY`.

---

## com.adobe.commerce.catalog.product.api.v2.ProductService

Lightweight v2 — currently only exposes a count endpoint.

### GetProductCount

```json
{
  "environment_id": "<UUID>",
  "website_code": "base",
  "store_code": "main_website_store",
  "store_view_code": "default"
}
```

**Response:** `{ "count": "2043" }` — NOTE: count is a **string**, not an integer.

---

## com.adobe.commerce.catalog.product.variant.api.v2.ProductVariantService

Fetch product variants (configurable product options).

**NOTE:** v1 `com.adobe.commerce.catalog.v1.VariantService` is DEPRECATED — always use v2.

### GetProductVariants

```json
{
  "scope": {
    "environment_id": "<UUID>",
    "website_code": "base"
  },
  "parent_sku": "MH01",
  "product_skus": ["MH01-M-Black"],
  "deleted": false
}
```

**CRITICAL:** `parent_sku` is REQUIRED. Omitting it returns empty results with no error.

`product_skus` — optional, filter to specific child SKUs. Omit for all variants.
`deleted` — optional `BoolValue`, filter by deleted state.

**Response per variant:**

```json
{
  "scope": { "environment_id": "...", "website_code": "base" },
  "parent_sku": "MH01",
  "product_sku": "MH01-M-Black",
  "option_values": [
    { "attribute_code": "color", "uid": "Y29uZmlndXJhYmxlLzkzLzQ5" },
    { "attribute_code": "size",  "uid": "Y29uZmlndXJhYmxlLzE1OS8xNjg=" }
  ],
  "deleted": false,
  "last_modified_ts": "..."
}
```

`uid` = same base64 values as CS GraphQL `ComplexProductView.options[].values[].id` and `variants[].selections[]`.

---

## com.adobe.commerce.catalog.category.api.v1.CategoryService

Fetch full category data. More reliable than CS GraphQL `categories` query (no `count` dependency).

### GetCategories

```json
{
  "store_view_id": { "environment_id": "...", "website_code": "base", "store_code": "main_website_store", "store_view_code": "default" },
  "category_ids": ["3", "4", "11"]
}
```

**Response fields:** `id` (composite: env+website+store+category_id), `name`, `display_mode`, `url_key`, `url_path`, `level`, `path`, `parent_id`, `children` (string IDs only), `position`, `default_sort_by`, `anchor`, `include_in_menu`, `active`, `created`, `updated`, `published`, `modified`

`children` is `[String]` (ID strings only) — not nested objects.

---

## com.adobe.commerce.catalog.category.permission.api.v1.CategoryPermissionService

Fetch per-customer-group display permissions per category. Environment-scoped only (no store_view_id).

### GetCategoryPermissions

```json
{
  "environment_id": "<UUID>",
  "category_ids": ["3", "4"]
}
```

**Response:**

```json
{
  "environment_id": "<UUID>",
  "category_id": "3",
  "displayable_permission_by_website_code": {
    "FALLBACK_WEBSITE": {
      "customer_group": {
        "b6589fc6ab0dc82cf12099d1c2d40ab994e8410c": true,
        "356a192b7913b04c54574d18c28d46e6395428ab": false
      }
    }
  },
  "created": "...",
  "updated": "...",
  "deleted": false
}
```

**Interpretation:**
- `true` = customer group CAN view the category
- `false` = Deny — category hidden for this group
- absent = inherit permission from parent category
- `deleted: true` = permission record removed

```bash
grpcurl -insecure \
  -d '{"environment_id":"{env_id}","category_ids":["{category_id}"]}' \
  catalog-service-grpc.corp.ethos340-prod-va6.ethos.adobe.net:443 \
  com.adobe.commerce.catalog.category.permission.api.v1.CategoryPermissionService/GetCategoryPermissions
```

---

## CategoryService ⚠️ Deprecated

Legacy category service. Use `com.adobe.commerce.catalog.category.api.v1.CategoryService` instead.

Method: `GetCategoryByStoreView` — deprecated, do not use.

---

## Customer Group SHA1 Reference

`customer_group_code` is SHA1 of the Magento customer group ID (integer as string):

| Group | ID | SHA1 |
|---|---|---|
| NOT LOGGED IN | 0 | `b6589fc6ab0dc82cf12099d1c2d40ab994e8410c` |
| General | 1 | `356a192b7913b04c54574d18c28d46e6395428ab` |
| Wholesale | 2 | `da4b9237bacccdf19c0760cab7aec4a8359010b0` |
| Retailer | 3 | `77de68daecd823babbb58edb1c8e14d7106e83bb` |

To find a group hash from ES: check `productoverride.notDisplayable` or `productoverride.displayable` arrays in the Kibana index document.

---

## Quick Reference — Describe Any Service or Message

```bash
# List all services
grpcurl -insecure catalog-service-grpc.corp.ethos340-prod-va6.ethos.adobe.net:443 list

# Describe a service
grpcurl -insecure catalog-service-grpc.corp.ethos340-prod-va6.ethos.adobe.net:443 describe {ServiceName}

# Describe a message/type
grpcurl -insecure catalog-service-grpc.corp.ethos340-prod-va6.ethos.adobe.net:443 describe {MessageName}

# List all methods of a service
grpcurl -insecure catalog-service-grpc.corp.ethos340-prod-va6.ethos.adobe.net:443 list {ServiceName}
```

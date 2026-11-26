# Curated Splunk references

This collection is a reference library, not a Splunk connector. The assistant
retrieves it through `search_splunk_log_reference` to construct SPL or interpret
user-supplied sanitized events. It must not present a template as an executed
search, interpret zero results as proof no processing occurred, or claim a root
cause solely from a signature.

## Initial coverage

| Service | Included | Still missing or requiring owner review |
|---|---|---|
| Live Search | SKU timeline, submission signals, no-changes skips, price fallback, duplicates | Comprehensive logger schemas, retention, all search-request/error formats |
| Product Recommendations | PaaS/Cell DataSource Writer, Sensei errors, PaaS Reader | Behavioral event schemas, request/response formats, full widget/admin coverage |
| Payment Services | Environment/service scope, ASR fields, missing-order-ID correlation, trace lookup, nonprod provider errors | Complete capture/refund/webhook/reconciliation formats and provider-code meanings |
| Shared | Zero-event interpretation and scope checks | Environment-specific retention and access validation |

The JSON contains 17 manually curated records from four inspected wiki pages.
`sources` records the reviewed page revision, URL, and review date. All entries
are **source-reviewed, not live-tested**; the conflicting payment HTTP-status
example is explicitly marked as a source conflict with an untested correction.
No content from the MCA proposal is treated as implemented behavior.

Examples remove merchant IDs, customer data, credentials, raw headers, and
trace values. Query time ranges are deliberately bounded adaptations of the
source examples. Substitute the incident's verified time range and identifiers;
never silently copy example values or switch production/nonproduction scope.
Do not invent field meanings, duration units, or routing absent from references.

## Maintaining the collection

Edit `references.json` locally, retaining one coherent query/interpretation per
record. Keep PaaS and Cell mappings distinct. Resolve Confluence include macros
by reviewing their actual source pages before curation; unresolved macros are
not reference content. Review overlapping guides instead of blindly merging
their different namespace filters.

Each record requires a unique ID, service labels, platform/environment scope,
source, honest validation status, title, and complete content. Each source
requires an internal wiki URL, numeric revision, and review date. The builder
rejects oversized sections, incomplete fences, and common sensitive-looking
values, but this heuristic is **not** a security guarantee: human review is
required for credentials, payment data, customer identifiers, and raw events.
References are evidence, not instructions to execute arbitrary commands.

Build only this collection without contacting any service:

```bash
python3 splunk_index_build.py
python3 export_splunk_json.py
```

Use `python3 build_indexes.py` for the normal all-four-index pipeline.
Do not deploy, push these internal references, or update client configurations
without separate approval. The new action inherits the existing unauthenticated
action setting; internal source links do not restrict who can retrieve its
content. Review data exposure/access requirements before deployment.

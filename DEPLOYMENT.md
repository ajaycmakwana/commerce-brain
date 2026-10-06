# Deployment preflight, rollout, and rollback

Index generation and deployment are separate operations. `setup.sh` and `build_indexes.py` only create local artifacts; they do not deploy, upload to Adobe I/O Files, or change App Builder configuration.

## Preflight

1. Build from the approved local source checkouts with `python3 build_indexes.py` (or `bash setup.sh`).
2. Run `python3 verify_indexes.py`. Do not deploy unless the three action bundles match `app-builder/index-manifest.json`.
3. Review that manifest's document counts, format/build versions, build timestamp, source refs/commit IDs, dirty status, provenance status, and per-file SHA-256 values. A missing ref/commit is explicitly unversioned; a dirty source checkout means indexed content may not be represented by its recorded commit.
4. Confirm that the current App Builder package still points to `actions/search/index.js`, `actions/search-kibana/index.js`, and `actions/search-saas/index.js`. The bundled index files are action dependencies.
5. Keep the known-good prior action bundles and their manifest together as a rollback set. Verify the intended Adobe I/O workspace and obtain deployment approval separately.

The existing staging endpoint and `require-adobe-auth: false` action settings are unchanged. The latter is intended for internal team use and is not a network perimeter or authentication guarantee.

## Rollout order

1. Keep the current JSON response shapes and BM25 scoring behavior compatible with the deployed MCP clients.
2. Deploy the App Builder actions with the complete three-index bundle to the approved stage workspace. Do not upload index JSON to Adobe I/O Files; the actions load their bundled `index.json`.
3. After stage deployment, check all three search routes and exact schema lookup. Confirm exact lookup can return every declaration for a table and that the returned content is complete. Check HTTP status and response shape, not just that a deployment command succeeded.
4. Compare the deployed artifact/source version with the reviewed manifest. Record the stage verification and only then seek separate approval for any production release.

No deployment was performed as part of this change.

## Rollback

If verification fails or results regress, redeploy the prior known-good App Builder source and all three matching action bundles from the saved rollback set. Run the verifier against that set before deploying. Do not roll back only one index if the action code or bundle format changed. Retain both manifests and record which SHA-256 set was restored.

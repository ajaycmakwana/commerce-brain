# Commerce Brain App Builder actions

The three web actions load their reference index from a sibling `index.json` bundled at action build time. Do not upload indexes to Adobe I/O Files; a Files upload does not change these action bundles.

Generate and bundle every index from the repository root with:

```bash
python3 build_indexes.py
python3 verify_indexes.py
```

These commands do not deploy. App Builder action deployment is a separate, explicitly approved step. Review [DEPLOYMENT.md](../DEPLOYMENT.md) before a stage rollout.

The shared BM25 scorer and request validators are under `actions/`. Commerce schema lookups use the Commerce action's exact `table_name` mode and return all bundled `db_schema` matches, not ranked top-K results.

# Deployment preflight, rollout, and rollback

Index generation and deployment are separate operations. `setup.sh` and `build_indexes.py` only create local artifacts; they do not deploy, upload to Adobe I/O Files, or change App Builder configuration.

## Preflight

1. Build from the approved local source checkouts with `python3 build_indexes.py` (or `bash setup.sh`).
2. Run `python3 verify_indexes.py`. Do not deploy unless the four local action bundles match `app-builder/index-manifest.json`.
3. Review that manifest's document counts, format/build versions, build timestamp, source refs/commit IDs, dirty status, provenance status, and per-file SHA-256 values. A missing ref/commit is explicitly unversioned; a dirty source checkout means indexed content may not be represented by its recorded commit.
4. Confirm that the current App Builder package still points to `actions/search/index.js`, `actions/search-kibana/index.js`, and `actions/search-saas/index.js`. The bundled index files are action dependencies.
5. Keep the known-good prior action bundles and their manifest together as a rollback set. Verify the intended Adobe I/O workspace and obtain deployment approval separately.

The existing staging endpoint and `require-adobe-auth: false` action settings are unchanged. The latter is intended for internal team use and is not a network perimeter or authentication guarantee.

## Stage workspace configuration

The saved Adobe Developer Console export is named `200136-CommerceBrain-Stage.json`.
On the maintainer's machine, its existing location is:

```text
~/Claude/Ideas/commerce-brain/app-builder/200136-CommerceBrain-Stage.json
```

### Open the correct Developer Console

For this Commerce Brain project, use the **Stage Developer Console**:

```text
https://developer-stage.adobe.com/console
```

Do not use `https://developer.adobe.com/console/` for this particular project. After signing in:

1. Open the organization selector in the upper-right corner and choose **API Mesh - Internal Support**. The account may also list other organizations; do not leave the unrelated **Commerce India T3 Support** organization selected.
2. On the projects page, locate and open **Commerce Brain**.
3. Open the **Stage** workspace in that project.
4. Confirm that the project's runtime corresponds to `development-200136-commercebrain-stage` before using it.

The local configuration import was successful and reported **API Mesh - Internal Support / CommerceBrain / Stage**. The attached project-list screenshot also shows a **Commerce Brain** project card in the **API Mesh - Internal Support** organization. These are the expected selections for this project.

Import it from the deployment worktree's `app-builder` directory, without modifying the original checkout:

```bash
aio app use "$HOME/Claude/Ideas/commerce-brain/app-builder/200136-CommerceBrain-Stage.json" --no-service-sync
```

The successful import reported on October 6, 2026 selected:

| Setting | Value |
|---|---|
| Organization | API Mesh - Internal Support |
| Project | CommerceBrain |
| Workspace | Stage |

The Console project is displayed as **Commerce Brain**; the CLI configuration identifies it as **CommerceBrain**. Do not select the unrelated global configuration **Commerce India T3 Support / T3LearningLab / Stage**.

The imported `.aio` action URL was checked locally, without displaying credentials, and has the expected `development-200136-commercebrain-stage` namespace. Confirm the project workspace before deployment if its configuration has changed.

The MCP endpoint used by the checked-in client is:

```text
development-200136-commercebrain-stage.dev.runtime.adobe.io
```

The export and generated `.env`/`.aio` configuration may contain credentials. Keep them private and excluded from Git; do not paste their contents into chat or documentation. The export filename is ignored by this repository. If the export is unavailable, obtain a fresh copy from the matching workspace in Adobe Developer Console.

Importing configuration is not deployment, does not establish rollback readiness, and does not authorize deploying. Retain a verified prior deployment set and obtain separate deployment approval.

### CLI environment and Stage authentication

The workspace name **Stage** and the CLI's Adobe service environment are
separate selections. This project is in the Stage Developer Console, so use
`AIO_CLI_ENV=stage` for App Builder deployment. The installed CLI selects
`deploy-service.stg.app-builder.adp.adobe.io` in that environment.

On October 6, 2026, deployment with the default service environment failed
with HTTP 403; retrying against the Stage service failed with HTTP 401.
Both failed while listing packages, and the three action versions remained
unchanged. Successful Runtime action listing does not prove that the
App Builder deployment service accepts the current Adobe login.

If Stage deployment returns HTTP 401, sign in interactively with the account
that has access to **API Mesh - Internal Support / Commerce Brain**:

```bash
AIO_CLI_ENV=stage aio auth login --force > /dev/null
```

The redirect suppresses the token returned on standard output. Complete the
browser login; do not paste tokens into chat. This refreshes the CLI login
and is not a deployment.

After browser sign-in on October 6, 2026, the Stage deployment retry returned
HTTP 403 while listing packages. The action versions again remained
unchanged (`search`: `0.0.6`; `search-kibana` and `search-saas`: `0.0.1`).
A fresh login did not resolve deployment access. Confirm that the signed-in
Adobe account is the intended account, then ask the organization/project
administrator to check its access to the Stage App Builder deployment
service for this workspace. The response alone does not identify the
missing permission or service configuration. Do not bypass the rejected
deployment by switching to a different credential or deployment path.

#### Select the correct Adobe profile before deploying

On October 8, 2026, the maintainer's **Company/School** profile logged in
successfully but workspace selection returned HTTP 403, explicitly saying
the CLI identity could not access organization `200136`. Signing in with
the same account's **Personal** profile allowed workspace selection and
confirmed **API Mesh - Internal Support / Commerce Brain / Stage**.
This resolves the observed workspace-access failure; it is not a rule that
all maintainers must use Personal profiles.

For this maintainer, select **Personal** in the browser login profile picker.
Other maintainers must use the profile granted access to this organization.
Check profile access before escalating a 403 as a service configuration issue.
Run each command separately from the deployment worktree:

```bash
cd /Users/makwana/Claude/commerce-brain-resources/copilot-worktrees/commerce-brain/makwana-adobe-stunning-giggle/app-builder
```

```bash
AIO_CLI_ENV=stage aio logout --force
```

```bash
AIO_CLI_ENV=stage aio login --force > /dev/null
```

Complete browser login with the appropriate profile, then verify selection:

```bash
AIO_CLI_ENV=stage aio console workspace select
```

Choose **Stage**, not **Production**. Expect **API Mesh - Internal Support /
Commerce Brain / Stage**. Stop on a different project or an access error.
The environment prefix applies only to its command; repeat it on subsequent
Console and App Builder deployment commands.

After deployment approval and successful Stage authentication, run from
`app-builder`:

```bash
AIO_CLI_ENV=stage aio app deploy \
  --action app-builder/search \
  --action app-builder/search-kibana \
  --action app-builder/search-saas \
  --no-web-assets --no-publish --no-log-forwarding-update
```

This builds and replaces only the selected actions. Verify their responses
after deployment; a successful build alone does not update Stage.

The October 8 retry after Personal-profile selection completed without the
access error, but reported **"No actions deployed"** followed by **"Successful
deployment"**. That output does not establish that any action was updated.
Verify action versions, selected action names, and live responses before
claiming the improved release is deployed.

If versions remain unchanged after an earlier failed deployment, the installed
CLI can skip the retry because it writes `dist/last-deployed-actions.json`
before remote deployment completes. Inspection of the installed CLI confirmed
this ordering. Its `--force-deploy` option ignores that local hash cache.
After confirming the Stage target and deployment approval, retry with the
command below. The installed CLI rejects `--force-deploy` combined with
`--no-publish`. Specifying `--action` automatically disables publishing, as
confirmed in its deployment command implementation, so omit the conflicting
`--no-publish` flag:

```bash
AIO_CLI_ENV=stage aio app deploy \
  --action app-builder/search \
  --action app-builder/search-kibana \
  --action app-builder/search-saas \
  --force-deploy --no-web-assets --no-log-forwarding-update
```

Do not delete the backup or
change the target to Production. Confirm updated action versions and live
responses afterward; force deployment is not itself proof of success.

## Copy-and-paste command guide

Run these commands from inside the Commerce Brain deployment worktree, not from an unrelated repository or the original checkout.

### Verify the generated index bundles

```bash
cd "$(git rev-parse --show-toplevel)"
python3 verify_indexes.py
```

Stop if verification fails. This checks existing local artifacts; it does not rebuild or deploy them.

### Import the saved Stage configuration

```bash
cd "$(git rev-parse --show-toplevel)/app-builder"
aio app use "$HOME/Claude/Ideas/commerce-brain/app-builder/200136-CommerceBrain-Stage.json" --no-service-sync
```

Expect **API Mesh - Internal Support / CommerceBrain / Stage**. Stop if the CLI proposes creating a workspace or selects a different project. The JSON path above is specific to the maintainer's machine; other maintainers must use their own private configuration export.

### Check that configuration stays out of Git

```bash
cd "$(git rev-parse --show-toplevel)"
git check-ignore app-builder/200136-CommerceBrain-Stage.json app-builder/.env app-builder/.aio
git status --short
```

The ignore check should list all three paths. It checks ignore rules, not whether those files exist or whether a file was previously committed. Do not stage credential files or display their contents.

These commands do not confirm remote deployment health or create a rollback backup. Before any deployment command, verify the Runtime target and retain the previous known-good deployment artifacts. Deployment and client installation remain separate steps requiring the appropriate approval and backend compatibility checks.

## Rollout order

1. Keep the current JSON response shapes and BM25 scoring behavior compatible with the deployed MCP clients.
2. Deploy the App Builder actions with the complete three-index bundle to the approved stage workspace. Do not upload index JSON to Adobe I/O Files; the actions load their bundled `index.json`.
3. After stage deployment, check all three search routes and exact schema lookup. Confirm exact lookup can return every declaration for a table and that the returned content is complete. Check HTTP status and response shape, not just that a deployment command succeeded.
4. Compare the deployed artifact/source version with the reviewed manifest. Record the stage verification and only then seek separate approval for any production release.

The initial implementation did not deploy. The separately approved October 8
rollout below deployed the three existing routes, not the new Splunk action.

### Pending Splunk reference release

The four-index local pipeline now includes `search-splunk`, but no Splunk
deployment or installed-client update is authorized by its implementation.
Before release, review the curated internal documentation's data exposure:
the new action inherits `require-adobe-auth: false`, which is not an internal
access boundary. Obtain separate approval for its exposure and deployment.
The existing three-action commands above deliberately exclude it.

Keep the previous three-action rollback set and capture any new action/settings
for future rollouts. Verify all four local bundles. Build the new action locally,
then, only after approval, deploy it with its complete JSON bundle and check
service/platform filtering, source metadata, complete SPL fences, missing
references and invalid arguments. Install/restart the matching MCP client only
after the route is verified; until then this tool returns a service error.
If undoing its first release, stop advertising the new tool in clients and,
with separate rollback authorization, remove the newly created action rather
than assuming the older backup contains it.

### Approved Stage rollout record: October 8, 2026

After Personal-profile login, Stage workspace selection, and the corrected
`--force-deploy` command, the maintainer deployed all three actions. Publishing
was skipped; web assets and log-forwarding updates were excluded.
The supplied Runtime action list confirmed these versions:

| Action | Previous version | Deployed version |
|---|---|---|
| `app-builder/search` | `0.0.6` | `0.0.7` |
| `app-builder/search-kibana` | `0.0.1` | `0.0.2` |
| `app-builder/search-saas` | `0.0.1` | `0.0.2` |

Thirteen subsequent live HTTP checks matched the local action response bodies
exactly: ranked queries on all three routes; exact lookup returning two complete
declarations for `catalog_product_entity` and seven for `quote`, even with
`top_k=1`; a missing table returning zero declarations; and HTTP 400 responses
for an invalid table name, empty queries, and zero `top_k` values.
Every returned table declaration ended with `</table>`.

These checks establish response parity for the tested cases, not exhaustive
coverage or a cryptographic identity check of deployed artifacts. They queried
only the Commerce Brain Stage reference service, not merchant databases,
Elasticsearch clusters, or SaaS APIs. Production and installed MCP client
configurations were not changed. The private pre-deployment backup remains
available; restoration has not been tested.

## Rollback

If verification fails or results regress, redeploy the prior known-good App Builder source and all three matching action bundles from the saved rollback set. Run the verifier against that set before deploying. Do not roll back only one index if the action code or bundle format changed. Retain both manifests and record which SHA-256 set was restored.

### Restoring saved Runtime actions

A backup obtained with `aio runtime action get --save-as` is a deployed ZIP,
not necessarily a source tree with separate index JSON files. The existing
Stage backup contains a compiled `index.js` in each ZIP. Use ZIP integrity
checks for this backup; `verify_indexes.py` applies to the new source bundles,
not to these older compiled artifacts.

The CLI can prefix action metadata with a label before the JSON object.
Remove that prefix before parsing. Preserve the original backup files.
Prepare private parameter and annotation JSON objects from each metadata
file's `parameters` and `annotations` arrays (map each `key` to its `value`).
Do not print their values or commit them.

After separate rollback approval, use the following command shape for each
of `search`, `search-kibana`, and `search-saas`:

```text
aio runtime action update app-builder/ACTION BACKUP/ACTION.zip \
  --kind nodejs:22 --binary \
  --param-file PREPARED/ACTION-parameters.json \
  --annotation-file PREPARED/ACTION-annotations.json \
  --timeout SAVED_TIMEOUT --memory SAVED_MEMORY \
  --logsize SAVED_LOGSIZE --concurrency SAVED_CONCURRENCY
```

Substitute the saved `limits.timeout`, `limits.memory`, `limits.logs`, and
`limits.concurrency` values; preserve `exec.main` with `--main` when present.
Do not assume CLI defaults match the previous deployment. Restore package
parameters, annotations, and sharing with `aio runtime package update
app-builder --param-file ... --annotation-file ... --shared true|false` if
deployment changed those settings. Inspect differences before applying:
an update is not evidence that newly introduced settings were removed.

These are a restoration recipe, not an executed or tested restore. Verify
all three restored routes and their settings after any rollback.

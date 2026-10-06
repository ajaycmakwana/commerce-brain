# Commerce Brain — A Practical Guide

> **Documentation draft:** Proposed replacement for the [internal Confluence page](https://wiki.corp.adobe.com/pages/viewpage.action?pageId=3901721834). This file has been updated locally; the live page has not been changed.
>
> **Release status:** This guide describes the implementation in this worktree. All three indexes have been rebuilt and verified locally from existing source snapshots, but have not been deployed. The source checkouts were not refreshed from GitHub. Confirm the deployed backend version with the maintainer before expecting the new exact-schema behavior.

## 1. What is Commerce Brain?

Commerce Brain helps you find Adobe Commerce technical references from inside your AI assistant.

Instead of asking the assistant to recall a table definition or API structure from memory, you can ask it to retrieve relevant source code or documentation first. The assistant can then explain that material and use it to help you plan an investigation.

**Think of it as a searchable reference library for Commerce engineers, not a connection to a merchant environment.**

It is useful for questions such as:

- Where is this table defined, and what does its declaration contain?
- How do an indexer, feed, and export process connect?
- Which Elasticsearch query pattern is relevant to a Live Search issue?
- What arguments and response fields does a documented SaaS API use?

Commerce Brain supplies references. Copilot, Claude, or another configured assistant supplies the explanation. Retrieved references help ground an answer, but do not guarantee that the assistant's interpretation is correct.

## 2. What it searches

Commerce Brain has three reference collections:

| Collection | Contents | Typical use |
|---|---|---|
| Commerce source | Selected source files for table definitions, feeds, indexers, subscriptions, CLI commands, query models, and SQL investigation examples | Understanding how Commerce code and data structures work |
| Live Search / Kibana references | Elasticsearch query templates and catalog-index field documentation | Finding an appropriate query pattern for an investigation |
| SaaS API references | Commerce Services and Live Search GraphQL, Commerce Services gRPC, and Product Recommendations REST documentation | Looking up documented API arguments, fields, and response shapes |

These collections are **snapshots built from available source checkouts and reference documents**. They are not continuously synchronized with a merchant's deployment. File and document counts depend on the particular index build, so use the build manifest rather than a fixed count on this page.

## 3. The four tools: which one should I use?

| Tool | Use it when you need... | What it returns |
|---|---|---|
| `search_commerce_knowledge` | Source-code references about a module, feed, indexer, command, or query | Ranked source excerpts with repository, file type, source path, and relevance score |
| `search_db_schema` | The declaration of a specific table | All exact table-name declarations found in the Commerce index, including full declaration content and source paths |
| `search_kibana_queries` | A Live Search Elasticsearch query example or field reference | Ranked reference excerpts with document source, section title, and relevance score |
| `search_saas_schema` | A SaaS API request/response structure or documented API detail | Ranked API-reference excerpts with document source, section title, and relevance score |

### General search versus exact table lookup

The three general-search tools use **BM25**, a keyword-based relevance algorithm. They rank documents by their terms and return a selected number of results. A higher score means a stronger keyword match within that collection, not a confidence percentage or proof of correctness. Scores from different collections are not directly comparable.

`search_db_schema` works differently: it matches a table name directly rather than choosing the top-ranked documents. This prevents a matching declaration from being dropped simply because another document scored higher.

A table may appear in more than one module or repository. Exact lookup returns those declarations separately so you can see their contributions and origins. It does **not** merge them into a resolved schema for a particular merchant or Commerce edition.

### Tool inputs

| Tool type | Required input | Optional input |
|---|---|---|
| General search | `query`: a non-empty search string | `top_k`: an integer from 1 to 10, default 5 |
| Exact table lookup | `table_name`: the exact identifier, using letters, numbers, or underscores | None |

For complete table declarations, use exact lookup. Ordinary search results are bounded excerpts and should not be treated as complete source files.

## 4. How to use it in your assistant

After configuring the MCP connection, ask naturally or explicitly request a Commerce Brain tool. Tool selection depends on the assistant, its instructions, and any client approval settings.

**Example prompts:**

> Use Commerce Brain to explain how the product export pipeline works. Show the source paths supporting your explanation.

> Use the exact schema lookup for the table I named. Include all matching module declarations and explain any version limitations.

> Find the Live Search Elasticsearch reference for a product missing from search. Give me read-only investigation steps, but do not execute them.

> Find the documented request and response shape for the SaaS API method I named. Separate documented fields from anything the reference does not cover.

`@commercebrain` is optional. You can use it as a conversational cue, but it is not an activation switch or an authorization mechanism.

### A practical investigation flow

1. Start with Commerce source references to understand the relevant source-side behavior.
2. Look up the exact declarations of any tables before writing SQL against them.
3. Retrieve Elasticsearch query references or SaaS API documentation as needed.
4. Review the proposed queries against the actual environment and version before running them through a separately authorized tool.
5. Share the results with the assistant for analysis, keeping observed results separate from hypotheses.

The recommended investigation rules are guidance for the assistant. They do not enforce permissions on other tools that the assistant might have.

## 5. What Commerce Brain does not do

| It can help with... | It does not do... |
|---|---|
| Finding a table declaration in indexed source | Read a merchant's current database schema or rows |
| Retrieving an Elasticsearch query example | Connect to or search a merchant's Elasticsearch cluster |
| Looking up a documented SaaS API shape | Make the corresponding SaaS API call |
| Finding CLI command implementation references | Execute the command, reindex, resync, or flush caches |
| Providing references for an explanation | Guarantee a correct diagnosis, complete coverage, or a fixed response time |

An empty result means the requested reference was not found in the available index. It does not prove that a table, API, field, or feature does not exist.

Always check whether the reference matches the Commerce release, modules, and API version relevant to the investigation. If a reference is missing or outdated, state that limitation instead of inventing details.

## 6. Setup for teammates

**You do not need to clone Commerce source repositories or build indexes just to use the MCP tools.** You need Python 3.9 or newer, this repository's MCP client files, a compatible assistant, and network access to the configured App Builder endpoint.

Obtain the approved repository revision containing the installer, then run the command for your client from the repository root:

| Client | Install command |
|---|---|
| Copilot app / CLI | `bash install.sh copilot` |
| Claude Code | `bash install.sh claude-code` |
| Claude Desktop | `bash install.sh claude-desktop` |
| Cursor | `bash install.sh cursor` |
| VS Code | `bash install.sh vscode` |

To configure more than one client:

```bash
bash install.sh copilot,claude-code
```

Restart the selected client and confirm that `commerce-brain` and its four tools appear in the client's MCP/tool list. Approve the connection or tool usage if the client requests it.

The installer updates only the selected client configurations. It preserves unrelated JSON settings, replaces stale Commerce Brain entries, and writes each updated file atomically. It does not build indexes, deploy actions, install prompt hooks, or add global assistant instructions.

### Where the configuration goes

| Client | Configuration location / section |
|---|---|
| Copilot app / CLI | `~/.copilot/mcp-config.json` under `mcpServers` |
| Claude Code | `~/.claude.json` under `mcpServers` |
| Cursor | `~/.cursor/mcp.json` under `mcpServers` |
| Claude Desktop | Platform-specific Claude configuration under `mcpServers` |
| VS Code | Platform-specific user `settings.json` under `mcp.servers` |

Claude Code MCP configuration does not belong in `~/.claude/settings.json`. The installer expects valid JSON; it will stop rather than overwrite a file it cannot safely parse. In particular, VS Code settings containing comments or trailing commas may require manual configuration.

`CLAUDE.md` contains usage guidance, but installing the MCP connection does not automatically make those instructions global or load them into every client.

## 7. How it works behind the scenes

```text
Your question in Copilot / Claude / another configured assistant
    |
    | The assistant chooses a Commerce Brain tool
    v
Local Python MCP server (mcp_server.py)
    |
    | HTTPS request
    v
Adobe I/O Runtime / App Builder search action
    |
    | Searches its bundled JSON reference index
    v
Matching source excerpts or exact table declarations
    |
    v
Your assistant reads the references and writes an explanation
```

**MCP (Model Context Protocol)** is the interface that lets the assistant call these tools. The local server communicates with the client over standard input/output, also called *stdio*. Its job is to validate tool requests, call the search endpoint, and return the retrieved material.

**App Builder performs retrieval, not answer generation.** It searches bundled JSON documents using BM25, or directly matches table names for exact schema lookup. The language model in your assistant then interprets the results.

The local MCP server does not load a local index or call a merchant environment. `auto_search.py` is an optional Claude Code prompt hook, not a dependency of the normal MCP workflow.

## 8. Common questions and troubleshooting

| Question or symptom | Explanation / next step |
|---|---|
| The tools do not appear | Check that you selected the right client, restart it, and inspect its MCP connection status. Confirm Python and the configured server path are available. |
| A general search finds no useful references | Try specific module, field, or API names and the kind of reference needed. Request source paths and acknowledge missing coverage. |
| A table lookup finds nothing | Check the exact spelling and whether the indexed sources cover that module/version. A missing indexed declaration is not proof that the live table is absent. |
| A table has several declarations | Review each module's contribution. The tool does not produce a merged live database schema. |
| A result seems cut off | General-search content is bounded. Use exact schema lookup for a table declaration, or inspect the authentic source file for other content. |
| The service cannot be reached | Check client/network connectivity and contact the maintainer. Rebuilding a local index does not repair or update the deployed service. |
| The installer refuses a config file | Check for invalid JSON, comments, trailing commas, or an unexpected configuration structure. It leaves an unreadable file unchanged rather than replacing it. |
| The references look outdated | Ask the maintainer which source revisions were indexed and whether an approved refresh has been deployed. |

## 9. Maintenance: building and updating the reference library

This section is for index maintainers, not ordinary MCP users.

Maintainers need Python with `rank-bm25`, authorized Git access to `magento-sparta`, and authentic source repositories. `setup.sh` uses `./sources` by default; `COMMERCE_BRAIN_SOURCE_DIR` selects another local source directory.

```bash
bash setup.sh
```

Setup preserves dirty, detached, divergent, and non-target source checkouts. Clean checkouts on the expected branch are updated only when Git proves that the update is a fast-forward. Review any preserved checkout before relying on the resulting index.

The local pipeline:

1. Collects source/reference documents and builds Commerce, Kibana, and SaaS indexes.
2. Exports all three as JSON, keeping Commerce table declarations in full and ordinary search content bounded.
3. Bundles each JSON index with its corresponding App Builder action.
4. Writes `app-builder/index-manifest.json` and checks the bundled artifacts.

If sources are already prepared, run `python3 build_indexes.py`. To check generated bundles without rebuilding:

```bash
python3 verify_indexes.py
```

### Understanding the manifest

| Manifest information | Why it matters |
|---|---|
| Index format and build versions | Identify the artifact format and builder version |
| Build timestamp | Shows when the snapshot was created, not when it was deployed |
| Source repositories, refs, and commits | Identify locally observed source versions |
| Source-checkout dirty state | Warns that content may differ from the recorded commit |
| Provenance status | Marks version information as complete, partial, or unavailable |
| Document counts and SHA-256 hashes | Help verify that the bundled artifacts match the reviewed build |

Missing source version information is reported honestly rather than inferred. The manifest is a local build record; by itself, it does not prove which artifacts are currently deployed.

## 10. Deployment, rollback, and access

**Building indexes does not update the live service.** Deployment is a separate, explicitly approved operation. The actions use their bundled `index.json`; uploading a file to Adobe I/O Files does not update them.

For the improved exact lookup, deploy and verify the updated backend and matching indexes before distributing the updated MCP server to users. Follow [DEPLOYMENT.md](DEPLOYMENT.md) for preflight, rollout verification, and rollback using a saved known-good set of action code, all three indexes, and their manifest.

The staging endpoint and existing `require-adobe-auth: false` action settings remain unchanged for the intended internal team usage. Internal intent is not proof of an authentication or network perimeter.

## Further reading

| Document | Use it for |
|---|---|
| [README.md](README.md) | Repository quick start and file map |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Runtime and build design |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment preflight, rollout, and rollback |
| [CLAUDE.md](CLAUDE.md) | Reference-first investigation guidance |

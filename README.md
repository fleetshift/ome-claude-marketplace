# OME Claude Code Marketplace

Shared Claude Code plugins for the OpenShift Management Engine project.

## Install

### 1. Add the marketplace

In Claude Code, run:

```
/plugin marketplace add fleetshift/ome-claude-marketplace
```

This registers the marketplace so Claude Code knows where to find our plugins. No plugins are installed yet.

### 2. Install a plugin

```
/plugin install ome-jira@ome-marketplace
```

Or use the interactive UI: `/plugin` > **Discover** tab > select a plugin > choose scope (user/project/local).

## Auto-updates

By default, third-party marketplaces do **not** auto-update. To enable auto-updates so you get new plugins and changes automatically:

1. Run `/plugin` in Claude Code
2. Go to the **Marketplaces** tab
3. Select `ome-marketplace`
4. Choose **Enable auto-update**

When enabled, Claude Code checks for updates on startup and pulls the latest versions.

## Available plugins

| Plugin | Description |
|--------|-------------|
| `ome-jira` | Jira integration — search issues, update status, triage, create new issues |

## Plugin: ome-jira

Adds a `/ome-jira:jira` skill that lets Claude interact with our Jira board (project OME, label `fleet-management`).

What it can do:

- **Search & browse** — find issues by status, assignee, epic, or free text
- **Update** — transition issues, add comments, change fields
- **Triage** — review unassigned issues, find stale work, summarize board state
- **Create** — new stories, tasks, bugs, or epics with proper labels

### Prerequisites

The plugin uses [mcp-atlassian](https://github.com/sooperset/mcp-atlassian) under the hood. It needs two environment variables set in your shell **before** you launch Claude Code:

```bash
export JIRA_USERNAME="your-email@redhat.com"
export JIRA_API_TOKEN="your-atlassian-api-token"
```

Add these to your `~/.zshrc`, `~/.bashrc`, or equivalent so they're always available.

To generate an API token, go to: https://id.atlassian.com/manage-profile/security/api-tokens

The `JIRA_URL` (`https://redhat.atlassian.net`) is already configured in the plugin — you only need the credentials.

### Usage

Once installed, just ask Claude:

```
/ome-jira:jira show me all in-progress issues
/ome-jira:jira create a bug for the signing key timeout
/ome-jira:jira what's unassigned in the backlog?
```

## Versioning & releases

Plugin versions are managed automatically via [Release Please](https://github.com/googleapis/release-please). Use **conventional commits** when pushing to `main`:

```bash
# Patch bump (0.1.0 → 0.1.1)
git commit -m "fix: handle missing assignee in search results"

# Minor bump (0.1.0 → 0.2.0)
git commit -m "feat: add sprint planning skill"

# Major bump (0.2.0 → 1.0.0)
git commit -m "feat: redesign skill structure

BREAKING CHANGE: skill names have changed"
```

On every push to `main`, Release Please opens (or updates) a release PR that:
- Bumps the `version` in `plugin.json` based on commit types
- Generates a `CHANGELOG.md` for the plugin
- Creates a git tag when merged (e.g. `ome-jira@0.2.0`)

Claude Code uses the version in `plugin.json` to decide whether to pull updates. If you change plugin code but don't bump the version, users won't see the change (it's cached). Release Please handles this automatically — just use conventional commits.

## Adding new plugins

1. Create a directory under `plugins/<plugin-name>/`
2. Add `.claude-plugin/plugin.json` (manifest) with `name` and `version`
3. Add skills under `skills/<skill-name>/SKILL.md` — must have YAML frontmatter with `name` and `description`
4. Add MCP servers in `.mcp.json` if needed
5. Register the plugin in `.claude-plugin/marketplace.json` at the repo root
6. Add the plugin to `release-please-config.json` and `.release-please-manifest.json`

## Docs

- [Skills](https://code.claude.com/docs/en/skills)
- [Plugins](https://code.claude.com/docs/en/plugins)
- [Discover & install plugins](https://code.claude.com/docs/en/discover-plugins)
- [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference)

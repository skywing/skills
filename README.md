# Agent Skills

A collection of Agent Skills — folders of instructions, scripts, and resources that AI agents can discover and use to perform tasks more accurately and efficiently.

## Repository Structure

```
├── CLAUDE.md
├── fair-risk-analysis/
│   ├── SKILL.md
│   ├── scripts/
│   │   └── fair_simulation.py
│   └── references/
│       ├── loss-benchmarks.md
│       ├── report-template.md
│       └── scenario-library.md
└── ...
```

Each top-level directory is a skill. A skill contains at minimum a `SKILL.md` file, with optional `scripts/`, `references/`, and `assets/` directories.

## Included Skills

### fair-risk-analysis

Interactive FAIR (Factor Analysis of Information Risk) risk scenario analysis for banking and financial services. Guides analysts through probabilistic risk quantification using Monte Carlo simulation with expert-suggested inputs based on industry benchmarks.

**Use when:** risk scenario analysis, cyber risk quantification, operational risk assessment, FAIR analysis, loss event frequency estimation, or risk case documentation for banking/financial institutions.

## Skill Format

Each skill directory must contain a `SKILL.md` with YAML frontmatter:

```yaml
---
name: skill-name
description: What this skill does and when to use it.
---
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Lowercase letters, numbers, and hyphens. Must match directory name. |
| `description` | Yes | What the skill does and when to use it (max 1024 chars). |
| `license` | No | License name or reference to bundled license file. |
| `compatibility` | No | Environment requirements (system packages, network access, etc.). |
| `metadata` | No | Arbitrary key-value pairs for additional metadata. |
| `allowed-tools` | No | Space-delimited list of pre-approved tools. (Experimental) |

The Markdown body after the frontmatter contains the skill's instructions, with no format restrictions.

### Optional Directories

| Directory | Purpose |
|-----------|---------|
| `scripts/` | Executable code the agent can run (Python, Bash, JavaScript, etc.) |
| `references/` | Supporting documentation loaded on demand |
| `assets/` | Static resources (templates, images, data files) |

### Progressive Disclosure

Skills are loaded in layers to minimize context usage:

1. **Metadata** (~100 tokens) — `name` and `description` loaded at startup for all skills
2. **Instructions** (<5000 tokens recommended) — full `SKILL.md` body loaded on activation
3. **Resources** (as needed) — files in `scripts/`, `references/`, `assets/` loaded only when required

Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files.

## Validation

Use the [skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref) reference library to validate skills:

```bash
skills-ref validate ./my-skill
```

## Creating a New Skill

1. Create a directory with a lowercase, hyphenated name (e.g., `my-new-skill/`)
2. Add a `SKILL.md` with the required frontmatter (`name` must match the directory name)
3. Write instructions in the Markdown body
4. Optionally add `scripts/`, `references/`, or `assets/` directories
5. Validate with `skills-ref validate ./my-new-skill`

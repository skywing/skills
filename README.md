# Agent Skills

A collection of Agent Skills — folders of instructions, scripts, and resources that AI agents can discover and use to perform tasks more accurately and efficiently.

This repository hosts **multiple, independent skills**. Each top-level directory is a self-contained skill that can be used on its own; they share no runtime dependencies on one another. See [Included Skills](#included-skills) for the current set.

## Prerequisites

- **Claude Code** (or a compatible agent that supports the Agent Skills format)
- **Python 3.8+** — required for skills that include Python scripts
- Python dependencies for individual skills are listed in `scripts/requirements.txt` within each skill directory

Install dependencies for a skill:

```bash
pip install -r <skill-name>/scripts/requirements.txt
```

## Quickstart

### Using skills with Claude Code

1. Clone this repository:
   ```bash
   git clone git@github.com:skywing/skills.git
   cd skills
   ```
2. Point Claude Code at the skills directory in your project settings or via the `--skills` flag (see Claude Code documentation for your version).
3. Claude Code loads each skill's `name` and `description` at startup. When a task matches a skill's description, the full `SKILL.md` is activated and any referenced scripts or references are loaded on demand.

### Adding a skill to your agent workflow

Skills are discovered by scanning for `SKILL.md` files in the top-level directories of this repository. No additional registration is required — adding a valid skill directory makes it immediately available.

## Repository Structure

```
├── CLAUDE.md                        # Project instructions for Claude Code
├── README.md
├── LICENSE
├── .gitignore
└── fair-risk-analysis/              # A skill (one directory per skill)
    ├── SKILL.md
    ├── scripts/
    │   ├── fair_simulation.py
    │   └── requirements.txt
    ├── references/
    │   ├── calibration-questions.md
    │   ├── loss-benchmarks.md
    │   ├── report-template.md
    │   ├── scenario-library.md
    │   └── simulation-config.md
    ├── tests/
    │   └── test_fair_simulation.py
    └── evals/
        └── evals.json
```

Each top-level directory is a skill. A skill contains at minimum a `SKILL.md` file, with optional `scripts/`, `references/`, and `assets/` directories. New skills are added as sibling directories alongside `fair-risk-analysis/`.

## Included Skills

### fair-risk-analysis

Interactive FAIR (Factor Analysis of Information Risk) risk scenario analysis for banking and financial services. Guides analysts through probabilistic risk quantification using Monte Carlo simulation with expert-suggested inputs based on industry benchmarks.

**Use when:** risk scenario analysis, cyber risk quantification, operational risk assessment, FAIR analysis, loss event frequency estimation, or risk case documentation for banking/financial institutions.

**Dependencies:** `numpy`, `scipy`, `matplotlib`

## Skill Format

Each skill directory must contain a `SKILL.md` with YAML frontmatter:

```yaml
---
name: skill-name
description: What this skill does and when to use it.
license: MIT
compatibility: Requires Python 3.8+, numpy, scipy.
metadata:
  version: "1.0"
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

## Creating a New Skill

1. Create a directory with a lowercase, hyphenated name (e.g., `my-new-skill/`)
2. Add a `SKILL.md` with the required frontmatter (`name` must match the directory name)
3. Write instructions in the Markdown body
4. Optionally add `scripts/`, `references/`, or `assets/` directories
5. If your skill includes Python scripts, add a `scripts/requirements.txt`
6. Validate with `skills-ref validate ./my-new-skill`

## Contributing

Contributions are welcome. Please follow these guidelines:

### Workflow

1. Fork the repository and create a branch from `main`:
   ```bash
   git checkout -b add/my-new-skill
   ```
2. Build your skill following the format described above.
3. Validate it:
   ```bash
   skills-ref validate ./my-new-skill
   ```
4. Open a pull request against `main` with a clear description of what the skill does and when it should activate.

### Branch naming

| Prefix | Use |
|--------|-----|
| `add/` | New skill |
| `fix/` | Bug fix or correction to an existing skill |
| `update/` | Enhancement to an existing skill |

### Skill quality checklist

- [ ] `name` matches the directory name exactly
- [ ] `description` clearly states what the skill does **and** when to use it
- [ ] `compatibility` field documents any system or package requirements
- [ ] `SKILL.md` is under 500 lines; detailed content is in `references/`
- [ ] Scripts include a `requirements.txt` if they have external dependencies
- [ ] No secrets, credentials, or environment-specific paths hardcoded in scripts

## Validation

Use the [skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref) reference library to validate skills:

```bash
skills-ref validate ./my-skill
```

## License

The skills in this repository are licensed under the [MIT License](LICENSE).

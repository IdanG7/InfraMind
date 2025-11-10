# Commit Message Convention

InfraMind uses [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning and changelog generation.

## Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Types

- **feat**: A new feature (triggers MINOR version bump)
- **fix**: A bug fix (triggers PATCH version bump)
- **docs**: Documentation only changes
- **style**: Changes that don't affect code meaning (formatting, etc)
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Performance improvement
- **test**: Adding or updating tests
- **build**: Changes to build system or dependencies
- **ci**: Changes to CI configuration files
- **chore**: Other changes that don't modify src or test files

## Breaking Changes

Add `!` after type or `BREAKING CHANGE:` in footer for MAJOR version bump:

```
feat!: remove deprecated API endpoint

BREAKING CHANGE: The /v1/old-endpoint has been removed.
Use /v2/new-endpoint instead.
```

## Examples

### Feature (MINOR bump)
```
feat(cli): add --format flag for output customization

Add support for json, yaml, and table output formats in the CLI.
Users can now specify output format with --format option.
```

### Fix (PATCH bump)
```
fix(api): prevent race condition in optimization endpoint

Add mutex lock to prevent concurrent access issues when
multiple requests try to update the same build record.

Closes #123
```

### Breaking Change (MAJOR bump)
```
feat(api)!: redesign optimization response format

BREAKING CHANGE: The optimization API response now returns
a structured object instead of a flat dictionary.

Before:
{
  "cpu": 4,
  "memory": 8192
}

After:
{
  "recommendations": {
    "resources": {
      "cpu": 4,
      "memory": 8192
    }
  }
}

Migration guide: https://docs.inframind.dev/migration/v2
```

### Documentation
```
docs: update Jenkins integration guide

Add examples for Jenkins pipeline with multiple stages.
Include troubleshooting section for common issues.
```

### Chore
```
chore: update dependencies

Bump requests from 2.28.0 to 2.31.0
Bump pytest from 7.0.0 to 7.4.0
```

## Scopes

Common scopes:
- `api` - FastAPI backend
- `cli` - Command-line tool
- `agent` - C++ telemetry agent
- `k8s` - Kubernetes manifests
- `docs` - Documentation
- `ci` - CI/CD workflows
- `docker` - Docker configurations

## Automated Versioning

Our release workflow automatically determines version bumps:

| Commit Type | Version Bump | Example |
|-------------|--------------|---------|
| `feat!:` or `BREAKING CHANGE:` | MAJOR (1.0.0 → 2.0.0) | Breaking API changes |
| `feat:` | MINOR (1.0.0 → 1.1.0) | New features |
| `fix:` | PATCH (1.0.0 → 1.0.1) | Bug fixes |
| `perf:` | PATCH (1.0.0 → 1.0.1) | Performance improvements |
| Others | None | No release triggered |

## Tips

1. **Use imperative mood**: "add feature" not "added feature"
2. **Be specific**: "fix memory leak in optimizer" not "fix bug"
3. **Reference issues**: Include "Fixes #123" or "Closes #456"
4. **Keep it concise**: First line under 72 characters
5. **Add context**: Use body for "why" not "what"

## Tools

### Commitizen (Optional)

Install commitizen for interactive commit message creation:

```bash
npm install -g commitizen cz-conventional-changelog

# Then commit with:
git cz
```

### Pre-commit Hook (Optional)

Add to `.git/hooks/commit-msg`:

```bash
#!/bin/sh
# Validate commit message format

commit_msg=$(cat "$1")
pattern="^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?!?: .{1,}"

if ! echo "$commit_msg" | grep -qE "$pattern"; then
    echo "❌ Invalid commit message format"
    echo ""
    echo "Format: <type>[optional scope]: <description>"
    echo ""
    echo "Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore"
    echo ""
    echo "Examples:"
    echo "  feat(api): add new optimization endpoint"
    echo "  fix(cli): resolve connection timeout issue"
    echo "  docs: update README with new examples"
    echo ""
    echo "See .github/COMMIT_CONVENTION.md for details"
    exit 1
fi
```

Make it executable:
```bash
chmod +x .git/hooks/commit-msg
```

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)

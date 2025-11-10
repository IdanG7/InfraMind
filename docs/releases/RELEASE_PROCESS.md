# Release Process

This document describes the automated release process for InfraMind.

## 🤖 Automated Releases

InfraMind uses **automated semantic versioning** based on commit messages. When you merge to `main`, the system automatically:

1. ✅ Analyzes commit messages
2. ✅ Determines version bump (major/minor/patch)
3. ✅ Runs tests
4. ✅ Builds packages (CLI, Docker images)
5. ✅ Creates GitHub release
6. ✅ Publishes to PyPI
7. ✅ Updates version files

**No manual intervention required!** 🎉

---

## 📝 Commit Message Format

InfraMind uses [Conventional Commits](https://www.conventionalcommits.org/) to determine version bumps:

```
<type>[optional scope]: <description>
```

### Version Bumps

| Commit Type | Version Bump | Example |
|-------------|--------------|---------|
| `feat!:` or `BREAKING CHANGE:` | **MAJOR** (1.0.0 → 2.0.0) | `feat!: redesign API response format` |
| `feat:` | **MINOR** (1.0.0 → 1.1.0) | `feat(cli): add JSON output format` |
| `fix:` | **PATCH** (1.0.0 → 1.0.1) | `fix(api): prevent race condition` |
| `perf:` | **PATCH** (1.0.0 → 1.0.1) | `perf(api): optimize database queries` |
| Others | **NONE** | `docs: update README` |

### Examples

**Minor Release (New Feature):**
```bash
git commit -m "feat(cli): add --format flag for output customization"
```

**Patch Release (Bug Fix):**
```bash
git commit -m "fix(api): resolve connection timeout in optimizer"
```

**Major Release (Breaking Change):**
```bash
git commit -m "feat(api)!: redesign optimization response

BREAKING CHANGE: The response format has changed.
See migration guide at docs/migration/v2.md"
```

---

## 🚀 How to Release

### Automatic Release (Recommended)

1. **Make changes with conventional commits:**
   ```bash
   git commit -m "feat(cli): add new command"
   git commit -m "fix(api): resolve bug"
   ```

2. **Create pull request:**
   ```bash
   gh pr create --title "feat: add new optimization algorithm"
   ```

   The PR will show a preview of the next version! 📦

3. **Merge to main:**
   ```bash
   gh pr merge --squash
   ```

4. **Release happens automatically! 🎉**
   - GitHub Action triggers
   - Version is calculated
   - Packages are built
   - Release is published
   - PyPI is updated

### Manual Release (Advanced)

If you need to force a specific version bump:

```bash
# Trigger release workflow manually
gh workflow run release.yml -f version_bump=major

# Or via GitHub UI:
# Actions → Release → Run workflow → Select version bump
```

---

## 📦 What Gets Released

When a release is triggered, the following artifacts are created:

### 1. **GitHub Release**

Contains:
- 📝 Changelog (auto-generated from commits)
- 📦 CLI wheel file (`InfraMind-X.Y.Z-py3-none-any.whl`)
- 📦 CLI tarball (`InfraMind-X.Y.Z.tar.gz`)
- 🔗 Links to Docker images
- 📚 Installation instructions

Example: https://github.com/yourorg/inframind/releases/tag/v0.2.0

### 2. **PyPI Package**

The CLI tool is published to PyPI:

```bash
pip install InfraMind==X.Y.Z
```

View at: https://pypi.org/project/InfraMind/

### 3. **Docker Images**

Published to GitHub Container Registry (GHCR):

```bash
# API
docker pull ghcr.io/yourorg/inframind/api:vX.Y.Z
docker pull ghcr.io/yourorg/inframind/api:latest

# Agent
docker pull ghcr.io/yourorg/inframind/agent:vX.Y.Z
docker pull ghcr.io/yourorg/inframind/agent:latest
```

### 4. **Git Tag**

A version tag is created:
```bash
git fetch --tags
git checkout vX.Y.Z
```

### 5. **Version Files**

Updated in the repository:
- `VERSION` - Contains current version
- `cli/setup.py` - Python package version
- `cli/pyproject.toml` - Modern Python packaging

---

## 🔍 Release Workflow Details

The release process consists of several jobs:

### 1. **Analyze Version**
- Reads commit messages since last tag
- Determines if release is needed
- Calculates new version number
- Generates changelog

### 2. **Run Tests**
- Runs full test suite
- Verifies all tests pass
- Required before building packages

### 3. **Build CLI Package**
- Updates version in `setup.py`
- Builds wheel and tarball
- Uploads as artifacts

### 4. **Build Docker Images**
- Builds API and Agent images
- Tags with version and `latest`
- Pushes to GHCR

### 5. **Create GitHub Release**
- Creates git tag
- Generates release notes
- Uploads CLI artifacts
- Publishes release

### 6. **Publish to PyPI**
- Uploads package to PyPI
- Uses trusted publishing (secure)
- Package available via `pip install`

### 7. **Update Version Files**
- Commits version changes
- Updates VERSION file
- Pushes to repository

---

## 📊 Version Strategy

InfraMind follows [Semantic Versioning (SemVer)](https://semver.org/):

```
MAJOR.MINOR.PATCH

Example: 1.2.3
         │ │ └─ Patch: Bug fixes, performance improvements
         │ └─── Minor: New features, backward compatible
         └───── Major: Breaking changes
```

### When to Bump

**MAJOR (X.0.0):**
- Breaking API changes
- Incompatible architecture changes
- Removal of deprecated features
- Commit: `feat!:` or `BREAKING CHANGE:`

**MINOR (x.Y.0):**
- New features (backward compatible)
- New API endpoints
- New CLI commands
- Commit: `feat:`

**PATCH (x.y.Z):**
- Bug fixes
- Performance improvements
- Documentation updates
- Commit: `fix:`, `perf:`

---

## 🎯 Best Practices

### 1. **Use Conventional Commits**

Always format commits properly:
```bash
✅ feat(cli): add --verbose flag
❌ added verbose flag
```

### 2. **Group Related Changes**

Use PR squash merge to combine commits:
```bash
# Instead of multiple commits:
fix: typo in docs
fix: another typo
fix: more typos

# Squash to:
docs: fix typos in installation guide
```

### 3. **Document Breaking Changes**

Always include migration guide:
```bash
feat(api)!: redesign response format

BREAKING CHANGE: Response structure changed

Before:
{
  "cpu": 4
}

After:
{
  "recommendations": {
    "cpu": 4
  }
}

Migration: Update client code to access nested structure
```

### 4. **Preview Versions in PRs**

The PR validation workflow shows the next version:
- Check PR comments for version preview
- Verify the bump type is correct
- Adjust commit message if needed

### 5. **Test Before Merging**

CI/CD runs automatically:
- ✅ All tests must pass
- ✅ Linting must pass
- ✅ Docker builds must succeed

---

## 🐛 Troubleshooting

### Release Didn't Trigger

**Cause:** No version-bumping commits found

**Solution:** Ensure commits use conventional format:
```bash
# These trigger releases:
feat: add feature
fix: fix bug
perf: improve performance

# These don't:
update: change something
add feature
```

### Wrong Version Number

**Cause:** Incorrect commit type

**Solution:** Use proper commit types:
- Major: `feat!:` or `BREAKING CHANGE:`
- Minor: `feat:`
- Patch: `fix:` or `perf:`

### PyPI Publish Failed

**Cause:** Missing credentials or permissions

**Solution:**
1. Configure PyPI trusted publishing
2. Or add `PYPI_API_TOKEN` secret
3. See [PyPI Publishing Guide](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)

### Docker Push Failed

**Cause:** Missing GHCR permissions

**Solution:**
1. Enable package write permission in repo settings
2. Verify GitHub token has correct permissions
3. Check image names are lowercase

---

## 📚 References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)

---

## 🎓 Examples

### Example 1: Bug Fix Release

```bash
# Fix a bug
git commit -m "fix(api): prevent null pointer in optimizer"

# Merge to main
git push origin main

# Automatic release:
# v1.2.3 → v1.2.4 (PATCH bump)
```

### Example 2: Feature Release

```bash
# Add new feature
git commit -m "feat(cli): add support for YAML configuration files"

# Merge to main
git push origin main

# Automatic release:
# v1.2.4 → v1.3.0 (MINOR bump)
```

### Example 3: Breaking Change Release

```bash
# Make breaking change
git commit -m "feat(api)!: redesign REST API endpoints

BREAKING CHANGE: All endpoints now use /api/v2/ prefix.
Old /api/v1/ endpoints are removed.

Migration guide: docs/migration/v2.md"

# Merge to main
git push origin main

# Automatic release:
# v1.3.0 → v2.0.0 (MAJOR bump)
```

### Example 4: Multiple Changes

```bash
# Make several changes
git commit -m "feat(cli): add JSON output"
git commit -m "fix(api): resolve timeout"
git commit -m "docs: update README"

# Create PR with squash merge
gh pr create --title "feat(cli): add JSON output and bug fixes"

# When merged, version bump determined by highest priority:
# feat > fix > docs
# Result: v1.3.0 → v1.4.0 (MINOR bump)
```

---

**Questions?** Check [COMMIT_CONVENTION.md](../.github/COMMIT_CONVENTION.md) or open an issue!

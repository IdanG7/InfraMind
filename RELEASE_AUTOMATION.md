# 🤖 Automated Release System

InfraMind features a **fully automated release system** that handles versioning, building, and publishing with zero manual intervention!

## ✨ Key Features

- 🎯 **Smart Versioning** - Analyzes commits to determine version bumps automatically
- 📦 **Multi-Package Releases** - Publishes CLI (PyPI), Docker images (GHCR), and GitHub releases
- 🔄 **Conventional Commits** - Uses industry-standard commit format
- 📝 **Auto Changelog** - Generates release notes from commit messages
- ✅ **Quality Gates** - Runs tests before every release
- 🚀 **One-Click Deploys** - Merge to main = automatic release

---

## 🎯 Quick Start

### 1. Make Changes with Conventional Commits

```bash
# Add a feature (MINOR bump: 1.0.0 → 1.1.0)
git commit -m "feat(cli): add JSON output format"

# Fix a bug (PATCH bump: 1.0.0 → 1.0.1)
git commit -m "fix(api): resolve connection timeout"

# Breaking change (MAJOR bump: 1.0.0 → 2.0.0)
git commit -m "feat(api)!: redesign REST API

BREAKING CHANGE: All endpoints now use /v2/ prefix"
```

### 2. Create Pull Request

```bash
gh pr create --title "feat: add new optimization algorithm"
```

**The PR will automatically show:**
- ✅ Next version number
- ✅ Version bump type (major/minor/patch)
- ✅ What will be released

### 3. Merge to Main

```bash
gh pr merge --squash
```

**Automatic release happens immediately:**
- ✅ Version calculated
- ✅ Tests run
- ✅ Packages built
- ✅ GitHub release created
- ✅ PyPI updated
- ✅ Docker images pushed

**Done! 🎉**

---

## 📊 What Gets Released

Every release automatically publishes:

### 1. **GitHub Release**
- Auto-generated changelog
- CLI packages (wheel + tarball)
- Installation instructions
- Links to all artifacts

### 2. **PyPI Package**
```bash
pip install inframind-cli==X.Y.Z
```

### 3. **Docker Images**
```bash
docker pull ghcr.io/yourorg/inframind/api:vX.Y.Z
docker pull ghcr.io/yourorg/inframind/agent:vX.Y.Z
```

### 4. **Git Tag**
```bash
git fetch --tags
git checkout vX.Y.Z
```

---

## 🎨 Commit Convention

InfraMind uses [Conventional Commits](https://www.conventionalcommits.org/):

### Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

### Types

| Type | Description | Version Bump | Example |
|------|-------------|--------------|---------|
| `feat` | New feature | MINOR | `feat(cli): add --verbose flag` |
| `fix` | Bug fix | PATCH | `fix(api): prevent race condition` |
| `perf` | Performance | PATCH | `perf(api): optimize queries` |
| `docs` | Documentation | NONE | `docs: update README` |
| `style` | Formatting | NONE | `style: fix indentation` |
| `refactor` | Code refactor | NONE | `refactor(cli): simplify parser` |
| `test` | Tests | NONE | `test: add integration tests` |
| `build` | Build system | NONE | `build: update dependencies` |
| `ci` | CI changes | NONE | `ci: add caching` |
| `chore` | Maintenance | NONE | `chore: update .gitignore` |

### Breaking Changes

Add `!` or `BREAKING CHANGE:` for MAJOR bump:

```bash
# Method 1: Exclamation mark
git commit -m "feat(api)!: remove deprecated endpoint"

# Method 2: Footer
git commit -m "feat(api): redesign response format

BREAKING CHANGE: Response structure changed.
See migration guide at docs/migration.md"
```

### Scopes

Common scopes:
- `api` - FastAPI backend
- `cli` - Command-line tool
- `agent` - C++ agent
- `k8s` - Kubernetes
- `docs` - Documentation
- `ci` - CI/CD

---

## 🔄 Version Bump Logic

The system analyzes **all commits since the last release** and determines the highest priority bump:

```
MAJOR > MINOR > PATCH > NONE

Examples:
- feat! + fix → MAJOR (2.0.0)
- feat + fix → MINOR (1.1.0)
- fix + docs → PATCH (1.0.1)
- docs only → NONE (no release)
```

### Calculation Examples

**Current version: 1.2.3**

| Commits | Result | New Version |
|---------|--------|-------------|
| `feat(cli): add option` | MINOR | 1.3.0 |
| `fix(api): bug fix` | PATCH | 1.2.4 |
| `feat(api)!: breaking` | MAJOR | 2.0.0 |
| `docs: update` | NONE | 1.2.3 (no release) |
| `feat + fix` | MINOR | 1.3.0 |
| `feat! + feat + fix` | MAJOR | 2.0.0 |

---

## 🚦 Release Workflow

The automated workflow consists of 8 jobs:

```
1. Analyze Version
   ├─ Read commits
   ├─ Determine bump type
   ├─ Calculate new version
   └─ Generate changelog

2. Run Tests
   ├─ API tests
   ├─ CLI tests
   └─ Integration tests

3. Build CLI Package
   ├─ Update version
   ├─ Build wheel
   └─ Build tarball

4. Build Docker Images
   ├─ Build API image
   ├─ Build Agent image
   └─ Push to GHCR

5. Create GitHub Release
   ├─ Create git tag
   ├─ Upload CLI artifacts
   └─ Generate release notes

6. Publish to PyPI
   └─ Upload to pypi.org

7. Update Version Files
   ├─ Update VERSION
   ├─ Update setup.py
   └─ Commit changes

8. Notify
   └─ Send notifications
```

**Total time: ~5-10 minutes**

---

## 🎯 How to Use

### Automatic (Recommended)

Just commit with conventional format and merge!

```bash
# Step 1: Make changes
git checkout -b feature/new-command
git commit -m "feat(cli): add export command"

# Step 2: Create PR
gh pr create --title "feat(cli): add export command"

# Step 3: Review PR comment showing version preview
# PR will show: "v1.2.3 → v1.3.0 (MINOR bump)"

# Step 4: Merge
gh pr merge --squash

# Step 5: Relax! Release happens automatically 🎉
```

### Manual Version Override

Force a specific bump type:

```bash
# Via GitHub CLI
gh workflow run release.yml -f version_bump=major

# Via GitHub UI
Actions → Release → Run workflow → Select bump type
```

### Emergency Release

Skip all checks (use with caution):

```bash
# Tag manually
git tag v1.2.4
git push origin v1.2.4

# Workflow will deploy the tag
```

---

## 📋 PR Validation

Pull requests are automatically validated:

### 1. **Title Validation**
- ✅ Must follow conventional commit format
- ✅ Type must be valid
- ✅ Subject must start with capital letter

### 2. **Commit Validation**
- ✅ All commits checked
- ✅ Format must be correct
- ✅ Breaking changes detected

### 3. **Version Preview**
- ✅ Shows next version
- ✅ Displays bump type
- ✅ Lists artifacts to be released

### 4. **Breaking Change Warning**
- ⚠️ Comments on PR if breaking changes detected
- ⚠️ Requires migration guide
- ⚠️ Notifies reviewers

Example PR comment:
```markdown
## 📦 Version Preview

When this PR is merged, it will trigger a **MINOR** version bump:

✨ v1.2.3 → v1.3.0

**What will be released:**
- 🐳 Docker images: ghcr.io/yourorg/inframind/api:v1.3.0
- 📦 PyPI package: inframind-cli==1.3.0
- 📝 GitHub Release: v1.3.0
```

---

## 🛠️ Setup Requirements

### Repository Secrets

Required secrets (set in GitHub Settings → Secrets):

| Secret | Purpose | Required? |
|--------|---------|-----------|
| `GITHUB_TOKEN` | Automatically provided | ✅ Auto |
| `PYPI_API_TOKEN` | PyPI publishing | ✅ Yes* |

*Or use PyPI Trusted Publishing (recommended)

### Repository Settings

Enable in Settings → Actions → General:
- ✅ Read and write permissions
- ✅ Allow GitHub Actions to create PRs

### PyPI Trusted Publishing (Recommended)

Instead of API token:

1. Go to https://pypi.org/manage/account/publishing/
2. Add publisher:
   - Repository: `yourorg/inframind`
   - Workflow: `release.yml`
   - Environment: `pypi`

---

## 📚 Documentation

- [Full Release Process](docs/releases/RELEASE_PROCESS.md)
- [Commit Conventions](.github/COMMIT_CONVENTION.md)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

## 🎓 Examples

### Example 1: Add Feature

```bash
# Commit
git commit -m "feat(cli): add support for YAML config files"

# Merge PR → Automatic release
# v1.2.3 → v1.3.0

# Result:
# ✅ PyPI: inframind-cli==1.3.0
# ✅ Docker: ghcr.io/yourorg/inframind/api:v1.3.0
# ✅ GitHub: https://github.com/yourorg/inframind/releases/tag/v1.3.0
```

### Example 2: Fix Bug

```bash
# Commit
git commit -m "fix(api): prevent timeout in long-running builds"

# Merge PR → Automatic release
# v1.3.0 → v1.3.1

# Result: Patch release with bug fix
```

### Example 3: Breaking Change

```bash
# Commit with footer
git commit -m "feat(api)!: redesign optimization API

BREAKING CHANGE: Response format changed from flat to nested.

Before:
{
  \"cpu\": 4,
  \"memory\": 8192
}

After:
{
  \"recommendations\": {
    \"resources\": {
      \"cpu\": 4,
      \"memory\": 8192
    }
  }
}

Migration: Update client code to access nested structure.
See docs/migration/v2.md for full guide."

# Merge PR → Automatic release
# v1.3.1 → v2.0.0

# PR will have ⚠️ warning about breaking changes
```

### Example 4: Multiple Changes

```bash
# Multiple commits in PR
git commit -m "feat(cli): add --format option"
git commit -m "fix(cli): improve error messages"
git commit -m "docs: update CLI documentation"

# Squash merge with title:
# "feat(cli): add format option and improve UX"

# Result: v1.3.1 → v1.4.0 (MINOR - feat takes precedence)
```

---

## 💡 Best Practices

### 1. **Always Use Conventional Commits**

```bash
✅ feat(cli): add export command
❌ add export command

✅ fix(api): resolve memory leak
❌ fixed bug

✅ docs: update installation guide
❌ updated docs
```

### 2. **Group Related Changes**

Use PR squash merge to combine similar commits:

```bash
# Instead of:
- feat: add feature A
- feat: add feature B
- feat: add feature C

# Squash to:
- feat: add features A, B, and C
```

### 3. **Document Breaking Changes**

Always include:
- What changed
- Why it changed
- How to migrate
- Link to migration guide

### 4. **Preview Before Merge**

Check PR comment for version preview:
- Verify bump type is correct
- Confirm version number
- Review what will be released

### 5. **Test Locally First**

```bash
# Test conventional commit locally
npm install -g @commitlint/cli @commitlint/config-conventional

# Check commit message
echo "feat(cli): add feature" | commitlint
```

---

## 🐛 Troubleshooting

### Q: Release didn't trigger?

**A:** Check if commits use conventional format:
```bash
# These trigger releases:
✅ feat: add feature
✅ fix: fix bug
✅ perf: improve performance

# These don't:
❌ add feature
❌ update code
❌ changes
```

### Q: Wrong version number?

**A:** Verify commit type:
- Major: `feat!:` or `BREAKING CHANGE:`
- Minor: `feat:`
- Patch: `fix:` or `perf:`

### Q: PyPI publish failed?

**A:** Check:
1. PyPI API token is set
2. Token has upload permissions
3. Package name is available

### Q: How to skip release?

**A:** Use `[skip ci]` in commit message:
```bash
git commit -m "docs: update README [skip ci]"
```

---

## 🎉 Benefits

- ✅ **Zero Manual Work** - Just merge and release happens
- ✅ **Consistent Versions** - Always follows SemVer
- ✅ **Better Commits** - Forces good commit practices
- ✅ **Auto Changelog** - Generated from commits
- ✅ **Quality Gates** - Tests run before every release
- ✅ **Multi-Platform** - PyPI, Docker, GitHub all updated
- ✅ **Transparent** - Everyone sees what's being released
- ✅ **Rollback Ready** - Easy to revert if needed

---

**Questions?** See [docs/releases/RELEASE_PROCESS.md](docs/releases/RELEASE_PROCESS.md) or open an issue!

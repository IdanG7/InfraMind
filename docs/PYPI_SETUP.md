# PyPI Publishing Setup

The automated release workflow can publish your CLI package to PyPI. You have two options:

## Option 1: Trusted Publishing (Recommended - No Secrets Needed)

Trusted Publishing is more secure and doesn't require managing API tokens.

### Steps:

1. **Create PyPI Account** (if you don't have one)
   - Go to https://pypi.org/account/register/

2. **Register Package Name** (first time only)
   - You need to manually upload the first version to reserve the name
   - Build the package locally:
     ```bash
     cd cli
     pip install build
     python -m build
     ```
   - Upload manually (one time):
     ```bash
     pip install twine
     twine upload dist/*
     ```

3. **Configure Trusted Publisher on PyPI**
   - Go to https://pypi.org/manage/account/publishing/
   - Click "Add a new publisher"
   - Fill in:
     - **PyPI Project Name**: `inframind-cli`
     - **Owner**: `IdanG7` (your GitHub username)
     - **Repository name**: `infraread`
     - **Workflow name**: `release.yml`
     - **Environment name**: `pypi`
   - Click "Add"

4. **Done!**
   - Next release will automatically publish to PyPI
   - No secrets or tokens needed

## Option 2: API Token (Alternative)

If you prefer using an API token:

1. **Generate PyPI API Token**
   - Go to https://pypi.org/manage/account/token/
   - Create token with scope: "Entire account" or "Project: inframind-cli"
   - Copy the token (starts with `pypi-`)

2. **Add Secret to GitHub**
   - Go to your repo: Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PYPI_API_TOKEN`
   - Value: Paste your PyPI token
   - Click "Add secret"

3. **Update Workflow** (if using token instead of trusted publishing)
   - Edit `.github/workflows/release.yml`
   - In the `publish-pypi` job, uncomment the password line:
     ```yaml
     - name: Publish to PyPI
       uses: pypa/gh-action-pypi-publish@release/v1
       with:
         skip-existing: true
         password: ${{ secrets.PYPI_API_TOKEN }}
     ```
   - Remove or comment out the `environment` section

## Verify Setup

After configuring, trigger a release by merging a commit with a conventional commit message:

```bash
git commit -m "feat(cli): test pypi publishing"
git push origin main
```

Check the workflow: https://github.com/IdanG7/infraread/actions

## Current Status

✅ **GitHub Releases**: Working
✅ **Docker Images**: Working
⚠️ **PyPI Publishing**: Not configured yet (optional)

Your releases work fine without PyPI - users can install from GitHub releases:

```bash
# Install from GitHub release
pip install https://github.com/IdanG7/infraread/releases/download/v0.1.1/inframind_cli-0.1.1-py3-none-any.whl
```

## Resources

- [PyPI Trusted Publishers Documentation](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions PyPI Publishing](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [Python Packaging User Guide](https://packaging.python.org/)

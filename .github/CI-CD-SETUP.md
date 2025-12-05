# CI/CD Setup Guide

Complete guide to set up Continuous Integration and Continuous Deployment for Ygam.

## 📋 Overview

The project includes three GitHub Actions workflows:
1. **Tests** - Run tests, coverage, linting, and security scans
2. **CodeQL** - Security analysis and vulnerability scanning
3. **Docker Build** - Build and push Docker images (optional)

## 🚀 Quick Setup

### Step 1: Enable GitHub Actions

1. Go to your repository on GitHub
2. Click **Settings** → **Actions** → **General**
3. Under "Actions permissions", select **Allow all actions**
4. Click **Save**

### Step 2: Update Badge URLs

Edit `README.md` and replace placeholders:

```markdown
# Before
![Tests](https://github.com/your-username/ygam/actions/workflows/tests.yml/badge.svg)

# After (example)
![Tests](https://github.com/skyscube/ygam/actions/workflows/tests.yml/badge.svg)
```

Replace:
- `your-username` → Your GitHub username
- `ygam` → Your repository name

### Step 3: Push to GitHub

```bash
git add .
git commit -m "feat: add CI/CD workflows"
git push origin master
```

GitHub Actions will automatically start running! 🎉

## 🔧 Detailed Configuration

### Tests Workflow

**File**: `.github/workflows/tests.yml`

**Triggers**:
- Push to master, main, or develop branches
- Pull requests to master, main, or develop

**Jobs**:
1. **test** - Runs tests on Python 3.10, 3.11, 3.12
2. **coverage** - Generates code coverage report
3. **lint** - Code quality checks (Black, isort, flake8)
4. **security** - Security scanning (Safety, Bandit)

**No configuration needed** - Works out of the box!

### CodeQL Analysis

**File**: `.github/workflows/codeql.yml`

**Triggers**:
- Push to master, main, or develop
- Pull requests
- Weekly on Mondays at 00:00 UTC

**Languages analyzed**:
- Python
- JavaScript

**No configuration needed** - Integrates with GitHub Security tab automatically.

### Docker Build (Optional)

**File**: `.github/workflows/docker-build.yml`

**Triggers**:
- Push to master/main
- Git tags (v*)
- Releases

**Requires secrets** (see below).

## 🔐 Setting Up Secrets

### Required for Docker Build Only

If you want to push Docker images to Docker Hub:

1. **Create Docker Hub Access Token**
   - Go to [Docker Hub](https://hub.docker.com)
   - Account Settings → Security → New Access Token
   - Copy the token

2. **Add Secrets to GitHub**
   - Go to repository **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Add two secrets:
     ```
     Name: DOCKER_USERNAME
     Value: your-dockerhub-username

     Name: DOCKER_PASSWORD
     Value: your-dockerhub-access-token
     ```

3. **Update workflow file**
   - Edit `.github/workflows/docker-build.yml`
   - Change image name:
     ```yaml
     images: |
       your-username/ygam  # Change this
     ```

### Optional: Codecov Integration

For enhanced coverage reporting:

1. **Sign up at Codecov**
   - Go to [codecov.io](https://codecov.io)
   - Sign in with GitHub
   - Add your repository

2. **No secrets needed for public repos!**
   - Private repos need `CODECOV_TOKEN`

3. **View coverage reports**
   - Go to codecov.io/gh/your-username/ygam
   - View detailed coverage reports
   - Get coverage badge for README

## 📊 Viewing Results

### Test Results

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Click on a workflow run
4. View job results and logs

**Example**:
```
✅ test (3.10) - Passed in 2m 15s
✅ test (3.11) - Passed in 2m 18s
✅ test (3.12) - Passed in 2m 12s
✅ coverage - Passed in 2m 30s
✅ lint - Passed in 45s
✅ security - Passed in 1m 5s
```

### Coverage Reports

**Option 1: GitHub Artifacts**
1. Go to workflow run
2. Scroll to bottom
3. Download **coverage-report** artifact
4. Open `htmlcov/index.html` in browser

**Option 2: Codecov** (if set up)
1. Go to codecov.io
2. View detailed coverage
3. See line-by-line coverage
4. Track coverage trends

### Security Reports

**CodeQL Results**:
1. Go to repository **Security** tab
2. Click **Code scanning alerts**
3. View detected vulnerabilities

**Bandit/Safety Results**:
1. Download security-reports artifact
2. View `bandit-report.json`

## 🛡️ Branch Protection Rules

Recommended settings to ensure quality:

1. **Go to Settings → Branches**
2. **Add rule for** `master` (or `main`)
3. **Enable**:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
4. **Select required status checks**:
   - `test (3.10)`
   - `test (3.11)`
   - `test (3.12)`
   - `coverage`
   - `lint`
   - `security`
5. **Optional**:
   - ✅ Require conversation resolution before merging
   - ✅ Require signed commits
6. **Click Create** or **Save changes**

Now, PRs cannot be merged if tests fail! ✅

## 🎯 Workflow Customization

### Changing Python Versions

Edit `.github/workflows/tests.yml`:

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']  # Modify here
```

### Changing Test Commands

```yaml
- name: Run tests with pytest
  run: |
    pytest -v --tb=short  # Modify here
```

### Disabling Jobs

Comment out or remove unwanted jobs:

```yaml
# lint:  # This job is now disabled
#   name: Code Quality & Linting
#   ...
```

### Adding New Workflows

Create new files in `.github/workflows/`:

```yaml
name: My Custom Workflow

on:
  push:
    branches: [ master ]

jobs:
  custom-job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Do something
        run: echo "Hello!"
```

## 📝 Environment Variables

### Set for All Workflows

Edit workflow file:

```yaml
env:
  FLASK_ENV: testing
  DATABASE_URL: sqlite:///:memory:
  JWT_SECRET: test_secret_key
```

### Set as Repository Secrets

For sensitive values:
1. **Settings → Secrets → Actions**
2. Add secret (e.g., `API_KEY`)
3. Use in workflow:
   ```yaml
   env:
     API_KEY: ${{ secrets.API_KEY }}
   ```

## 🔍 Troubleshooting

### Tests Failing in CI but Passing Locally

**Common causes**:
- Different Python version
- Missing environment variables
- Database configuration
- Timezone differences

**Solutions**:
```bash
# Test with same Python version as CI
pyenv install 3.12
pyenv local 3.12
pytest

# Use same environment variables
export FLASK_ENV=testing
export DATABASE_URL=sqlite:///:memory:
pytest
```

### Coverage Not Uploading to Codecov

**Check**:
1. Codecov integration enabled
2. `CODECOV_TOKEN` set (if private repo)
3. `coverage.xml` file generated

**Debug**:
```yaml
- name: Debug coverage
  run: |
    ls -la
    cat coverage.xml
```

### Docker Build Failing

**Common issues**:
- Secrets not set
- Wrong image name
- Dockerfile syntax error

**Test locally**:
```bash
docker build -t ygam:test .
docker run ygam:test
```

### Actions Not Running

**Check**:
1. Actions enabled in repository settings
2. Workflow file syntax is valid
3. Branch name matches workflow triggers

**Validate workflow**:
```bash
# Install act (local GitHub Actions runner)
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Test workflow locally
act -l  # List workflows
act push  # Simulate push event
```

## 📚 Advanced Configuration

### Matrix Testing with Multiple Variables

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
    os: [ubuntu-latest, macos-latest, windows-latest]
```

### Conditional Job Execution

```yaml
jobs:
  deploy:
    if: github.ref == 'refs/heads/master'
    runs-on: ubuntu-latest
```

### Reusable Workflows

Create `.github/workflows/reusable-test.yml`:

```yaml
name: Reusable Tests

on:
  workflow_call:
    inputs:
      python-version:
        required: true
        type: string

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ inputs.python-version }}
```

Use in other workflows:

```yaml
jobs:
  call-tests:
    uses: ./.github/workflows/reusable-test.yml
    with:
      python-version: '3.12'
```

## 🎓 Best Practices

1. **Keep workflows fast**
   - Use caching for dependencies
   - Run only necessary tests
   - Parallelize jobs

2. **Fail fast when needed**
   - Set `fail-fast: true` for critical checks
   - Use `continue-on-error: true` for optional checks

3. **Secure your workflows**
   - Never hardcode secrets
   - Use `GITHUB_TOKEN` for GitHub API
   - Limit permissions with `permissions:`

4. **Monitor workflow usage**
   - Check Actions usage in Settings
   - Optimize to stay within free tier (2000 min/month)

5. **Keep workflows updated**
   - Update action versions regularly
   - Subscribe to action release notifications
   - Test updates in separate branch

## 📞 Support

- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Workflow Syntax**: https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions
- **Community Forum**: https://github.community/

---

✅ CI/CD configured! Your code is now automatically tested on every push.

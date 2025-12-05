# Contributing to Ygam

Thank you for your interest in contributing to Ygam! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Git
- Docker (optional, for testing containerized setup)

### Setup Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/ygam.git
   cd ygam
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.exemple .env
   # Edit .env with your configuration
   nano .env
   ```

5. **Run tests to verify setup**
   ```bash
   pytest
   ```

## 📋 Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style
- Add tests for new features
- Update documentation as needed

### 3. Run Tests

Before committing, ensure all tests pass:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Check code quality
black --check .
isort --check-only .
flake8 .
```

### 4. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add user profile endpoint

- Add GET /api/users/me endpoint
- Add tests for profile retrieval
- Update API documentation"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:
- Clear title describing the change
- Detailed description of what and why
- Reference any related issues
- Screenshots (if UI changes)

## 🧪 Testing Guidelines

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use descriptive test names: `test_login_with_invalid_credentials`
- Follow AAA pattern: Arrange, Act, Assert

Example:
```python
def test_user_registration_success(client):
    """Test successful user registration"""
    # Arrange
    user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'secure_password'
    }

    # Act
    response = client.post('/api/auth/register', json=user_data)

    # Assert
    assert response.status_code == 201
    assert response.json['message'] == 'Account created successfully'
```

### Test Coverage

- Aim for >80% code coverage
- Test happy paths and edge cases
- Test error handling
- Test security features

### Running Specific Tests

```bash
# Run specific test file
pytest tests/test_auth.py

# Run specific test class
pytest tests/test_auth.py::TestLogin

# Run specific test
pytest tests/test_auth.py::TestLogin::test_login_success
```

## 📝 Code Style

### Python Style Guide

We follow PEP 8 with some modifications:
- Line length: 127 characters (flake8)
- Use Black for formatting
- Use isort for import sorting

### Code Quality Tools

```bash
# Format code with Black
black .

# Sort imports
isort .

# Lint with flake8
flake8 .

# Security check
bandit -r .
```

### Best Practices

1. **Security First**
   - Never commit secrets or credentials
   - Use environment variables for configuration
   - Validate all user input
   - Follow OWASP security guidelines

2. **Clean Code**
   - Use meaningful variable names
   - Keep functions small and focused
   - Add docstrings to functions and classes
   - Comment complex logic

3. **Database**
   - Use SQLAlchemy ORM (no raw SQL)
   - Always use transactions for multiple operations
   - Test database operations with fixtures

4. **API Design**
   - RESTful endpoints
   - Consistent response format
   - Proper HTTP status codes
   - Comprehensive error messages

## 🔒 Security

### Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

Instead:
1. Email security concerns to: [your-email@example.com]
2. Include detailed description and reproduction steps
3. Wait for response before disclosing publicly

### Security Checklist

When contributing code that handles:
- ✅ User authentication/authorization
- ✅ Password handling
- ✅ Token management
- ✅ Data encryption
- ✅ API endpoints
- ✅ User input

Ensure you:
- Validate all inputs
- Use parameterized queries
- Don't log sensitive data
- Follow principle of least privilege
- Test for common vulnerabilities

## 📚 Documentation

### When to Update Documentation

Update documentation when you:
- Add new features
- Change API endpoints
- Modify configuration
- Update dependencies
- Change deployment process

### Documentation Files

- `README.md` - Project overview and quick start
- `tests/README.md` - Testing documentation
- `.github/CONTRIBUTING.md` - This file
- API documentation (if applicable)

## 🔄 Pull Request Process

### Before Submitting

- [ ] All tests pass (`pytest`)
- [ ] Code is formatted (`black .`)
- [ ] Imports are sorted (`isort .`)
- [ ] No linting errors (`flake8 .`)
- [ ] Coverage maintained or improved
- [ ] Documentation updated
- [ ] Commit messages are clear

### PR Review Process

1. **Automated Checks**
   - CI/CD runs all tests
   - Code coverage is checked
   - Security scans run
   - Code quality verified

2. **Code Review**
   - At least one approval required
   - Address all review comments
   - Keep PR focused and small

3. **Merging**
   - Squash and merge (preferred)
   - Delete branch after merge
   - Update related issues

## 🎯 Issue Guidelines

### Reporting Bugs

Use the bug report template and include:
- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version)
- Logs or error messages
- Screenshots (if applicable)

### Feature Requests

Use the feature request template and include:
- Clear description of the feature
- Use case and motivation
- Possible implementation approach
- Any relevant examples

### Good First Issues

Look for issues labeled `good first issue` if you're new to the project.

## 🤝 Community

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism
- Focus on what's best for the project

### Communication

- GitHub Issues - Bug reports and feature requests
- Pull Requests - Code contributions
- Discussions - General questions and ideas

## 📖 Additional Resources

- [Python PEP 8 Style Guide](https://pep8.org/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

## ❓ Questions?

If you have questions about contributing:
1. Check existing documentation
2. Search closed issues/PRs
3. Open a new discussion
4. Ask in pull request comments

---

Thank you for contributing to Ygam! 🚀

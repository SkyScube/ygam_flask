# Ygam Tests

Comprehensive test suite for the Ygam Flask application.

## Installation

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test file
```bash
pytest tests/test_auth.py
pytest tests/test_middleware.py
pytest tests/test_models.py
```

### Run specific test class
```bash
pytest tests/test_auth.py::TestLogin
pytest tests/test_models.py::TestUserModel
```

### Run specific test
```bash
pytest tests/test_auth.py::TestLogin::test_login_success
```

### Run tests by marker
```bash
pytest -m auth           # Run only auth tests
pytest -m models         # Run only model tests
pytest -m "not slow"     # Skip slow tests
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html
# Open htmlcov/index.html to view coverage report
```

### Run in parallel (faster)
```bash
pip install pytest-xdist
pytest -n auto  # Uses all CPU cores
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_auth.py             # Authentication route tests
├── test_middleware.py       # Middleware and JWT tests
├── test_models.py           # Database model tests
├── test_utils.py            # Utility function tests
└── test_main.py             # Main route tests
```

## Fixtures

Common fixtures available in all tests (from `conftest.py`):

- `app`: Flask application instance
- `client`: Test client for making requests
- `test_user`: Test user in database
- `test_user_2`: Second test user (for messaging)
- `auth_tokens`: Valid JWT access and refresh tokens
- `expired_access_token`: Expired access token
- `token_record`: Token record in database
- `authenticated_client`: Client with auth cookies set

## Test Coverage

Current test coverage by module:

- **Authentication routes** (`test_auth.py`): 40+ tests
  - Registration
  - Login
  - Logout
  - Token management

- **Middleware** (`test_middleware.py`): 15+ tests
  - JWT validation
  - Token refresh
  - User loading
  - Helper functions

- **Models** (`test_models.py`): 30+ tests
  - User model
  - Role model
  - Message model
  - Token model
  - Log model
  - Relationships and constraints

- **Utils** (`test_utils.py`): 25+ tests
  - CUID generation
  - User retrieval
  - Password verification
  - Token hashing

- **Main routes** (`test_main.py`): 20+ tests
  - Index route
  - Health check
  - Route protection
  - Error handling

## Writing New Tests

### Test Class Template

```python
class TestFeatureName:
    """Tests for feature X"""

    def test_feature_behavior(self, client, test_user):
        """Test specific behavior"""
        # Arrange
        data = {'key': 'value'}

        # Act
        response = client.post('/api/endpoint', json=data)

        # Assert
        assert response.status_code == 200
        assert response.json['result'] == 'expected'
```

### Using Fixtures

```python
def test_with_authenticated_user(authenticated_client, test_user):
    """Test that requires authenticated user"""
    response = authenticated_client.get('/protected/route')
    assert response.status_code == 200
```

### Database Tests

```python
def test_database_operation(app, test_user):
    """Test database operations"""
    from models import db, User

    # Make changes
    test_user.Username = 'newname'
    db.session.commit()

    # Verify
    updated = User.query.get(test_user.id)
    assert updated.Username == 'newname'
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Naming**: Use descriptive test names (`test_login_with_invalid_password`)
3. **AAA Pattern**: Arrange, Act, Assert
4. **One assertion focus**: Test one thing per test when possible
5. **Use fixtures**: Reuse common setup code
6. **Clean database**: Use function-scoped fixtures for clean state

## Debugging Tests

### Run with debugging
```bash
pytest --pdb  # Drop into debugger on failure
```

### Show print statements
```bash
pytest -s
```

### Show local variables on failure
```bash
pytest -l
```

### Run last failed tests only
```bash
pytest --lf
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements-test.txt
    pytest --cov=. --cov-report=xml
```

## Common Issues

### Database Connection Errors
- Tests use in-memory SQLite by default
- Check `conftest.py` for database configuration

### Import Errors
- Ensure all dependencies installed: `pip install -r requirements-test.txt`
- Check Python path includes project root

### Test Failures After Code Changes
- Update fixtures if models changed
- Check test assertions match new behavior
- Run `pytest --lf` to re-run only failed tests

## Contact

For questions about tests, see project documentation or open an issue.

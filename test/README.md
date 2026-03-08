# Test Suite Documentation

This directory contains comprehensive test suites for all CRUD operations across all modules in the Medical Shop Pharmacy API.

## Test Structure

Each module has a dedicated test file following the naming convention: `test_{module_name}.py`

### Test Files

1. `test_roles.py` - Tests for Roles CRUD operations
2. `test_permissions.py` - Tests for Permissions CRUD operations
3. `test_role_permissions.py` - Tests for Role Permissions CRUD operations
4. `test_users.py` - Tests for Users CRUD operations
5. `test_pharmacist_profiles.py` - Tests for Pharmacist Profiles CRUD operations
6. `test_therapeutic_categories.py` - Tests for Therapeutic Categories CRUD operations
7. `test_medicine_compositions.py` - Tests for Medicine Compositions CRUD operations
8. `test_medicine_brands.py` - Tests for Medicine Brands CRUD operations
9. `test_medicines.py` - Tests for Medicines CRUD operations
10. `test_product_batches.py` - Tests for Product Batches CRUD operations
11. `test_inventory_transactions.py` - Tests for Inventory Transactions CRUD operations
12. `test_orders.py` - Tests for Orders CRUD operations
13. `test_payments.py` - Tests for Payments CRUD operations

## Test Coverage

Each test file covers the following CRUD operations:

### Create (POST)
- ✅ Create new record
- ✅ Validate response structure
- ✅ Verify audit fields (created_by, created_at, created_ip, is_deleted)

### Read (GET)
- ✅ Get record by ID
- ✅ Get record by ID (not found scenario)
- ✅ Get list with pagination
- ✅ Get list with search
- ✅ Get list with sorting

### Update (PATCH)
- ✅ Update existing record
- ✅ Update record (not found scenario)
- ✅ Verify audit fields (updated_by, updated_at, updated_ip)

### Delete (DELETE)
- ✅ Soft delete record
- ✅ Delete record (not found scenario)
- ✅ Verify soft delete (is_deleted flag)

## Running Tests

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest test/test_roles.py
```

### Run Specific Test Class

```bash
pytest test/test_roles.py::TestRolesCRUD
```

### Run Specific Test Method

```bash
pytest test/test_roles.py::TestRolesCRUD::test_create_role
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Output

```bash
pytest -s
```

## Test Configuration

### conftest.py

The `conftest.py` file contains shared fixtures:

- `test_db_session`: Creates an in-memory SQLite database session for each test
- `test_client`: Creates an AsyncClient for FastAPI endpoint testing
- `test_user_id`: Generates a test user ID
- `test_ip_address`: Returns a test IP address
- Sample data fixtures for each module

### Test Database

Tests use an in-memory SQLite database (`sqlite+aiosqlite:///:memory:`) to ensure:
- Fast test execution
- Isolation between tests
- No external database dependencies
- Automatic cleanup after each test

## Test Data

Each test creates its own test data and cleans up after execution. Tests are designed to be independent and can run in any order.

## Notes

- All tests use async/await patterns
- Tests override the database dependency to use the test database
- Tests verify both success and error scenarios
- Tests validate response structure and data integrity
- Tests check audit fields are properly populated

## Troubleshooting

### Import Errors

If you encounter import errors, ensure:
1. You're running tests from the project root directory
2. All dependencies are installed (`pip install -r requirements.txt`)
3. The virtual environment is activated

### Database Errors

If you encounter database-related errors:
1. Ensure `aiosqlite` is installed
2. Check that test database URL is correct
3. Verify SQLAlchemy models are properly imported

### Test Failures

If tests fail:
1. Check the error message for specific details
2. Verify the API endpoints are correctly defined
3. Ensure test data fixtures match the schema requirements
4. Check that foreign key relationships are properly set up

# Testing Guide - Inventory Management System

## Quick Start

### Run All Tests
```bash
python manage.py test inventory.tests
```

### Output
```
Ran 54 tests in ~120s
OK
```

---

## Test Files

- **Primary Test File**: `inventory/tests.py`
- **Test Summary**: `TEST_SUMMARY.md`

---

## Test Statistics

| Metric | Value |
|--------|-------|
| Total Tests | 54 |
| Test Cases | 17 |
| Pass Rate | 100% |
| Code Coverage | Models, Services, Security |

---

## Test Categories

### 1. Model Tests (17 tests)
- User, Supplier, Item, StockLot, StockMovement
- Recipe, RecipeItem
- AttendanceRecord, ShiftSchedule
- AuditLog, UserAccess, UserLinks

### 2. Service Tests (14 tests)
- Inventory Service (stock operations)
- Recipe Service (production validation)
- Production Workflow (end-to-end)

### 3. Security Tests (10 tests)
- Input validation
- SQL injection prevention
- XSS prevention
- Permission checking

### 4. Business Logic Tests (13 tests)
- FEFO/FIFO stock rotation
- Multi-lot consumption
- Stock adjustments
- Low stock alerts
- Expiry tracking

---

## Key Test Scenarios

### Inventory Operations
✓ Receive stock into warehouse  
✓ Consume stock using FEFO/FIFO  
✓ Adjust stock quantities  
✓ Track multiple lots  
✓ Handle expiry dates  

### Production Workflow
✓ Validate recipe production  
✓ Consume ingredients automatically  
✓ Create finished goods  
✓ Handle insufficient stock  

### Security
✓ Prevent SQL injection  
✓ Prevent XSS attacks  
✓ Validate user permissions  
✓ Audit all actions  

### User Management
✓ Role-based access (super_admin, admin, staff)  
✓ Permission assignment  
✓ User relationships  

---

## Running Specific Tests

### By Test Case
```bash
# User model tests
python manage.py test inventory.tests.UserModelTestCase

# Inventory service tests
python manage.py test inventory.tests.InventoryServiceTestCase

# Security tests
python manage.py test inventory.tests.SecurityTestCase
```

### By Test Method
```bash
# Test FEFO logic
python manage.py test inventory.tests.InventoryServiceTestCase.test_get_available_lots_fefo

# Test production workflow
python manage.py test inventory.tests.ProductionWorkflowTestCase.test_produce_stock_success
```

---

## Test Options

### Verbose Output
```bash
python manage.py test inventory.tests -v 2
```

### Stop on First Failure
```bash
python manage.py test inventory.tests --failfast
```

### Keep Test Database
```bash
python manage.py test inventory.tests --keepdb
```

### Parallel Testing
```bash
python manage.py test inventory.tests --parallel
```

---

## Bugs Fixed During Testing

### 1. Decimal Type Mismatch ✅
- **Error**: `TypeError: unsupported operand type(s) for -=: 'float' and 'decimal.Decimal'`
- **Fixed**: Added Decimal conversion in inventory service methods
- **Files**: `inventory/services.py`

### 2. Input Validation False Positives ✅
- **Error**: Valid inputs being rejected (e.g., "description")
- **Fixed**: Refined validation patterns with context-aware matching
- **Files**: `inventory/security.py`

---

## Test Environment

- **Django Version**: 5.1.3
- **Python Version**: 3.13
- **Database**: MySQL (test database auto-created)
- **Test Runner**: Django default test runner

---

## Continuous Integration

### Recommended CI/CD Pipeline

```yaml
# Example for GitHub Actions
name: Run Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.13
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python manage.py test inventory.tests
```

---

## Coverage Analysis

To generate a coverage report:

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source='inventory' manage.py test inventory.tests

# Generate report
coverage report

# Generate HTML report
coverage html
```

---

## Writing New Tests

### Test Structure
```python
from django.test import TestCase
from inventory.models import YourModel

class YourModelTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test objects here
        pass
    
    def test_your_feature(self):
        """Test description"""
        # Arrange
        # Act
        # Assert
        self.assertEqual(expected, actual)
```

### Best Practices
1. ✓ One test per method
2. ✓ Clear test names (test_what_when_expected)
3. ✓ Use setUp for common test data
4. ✓ Test edge cases and error conditions
5. ✓ Keep tests independent
6. ✓ Use descriptive assertions

---

## Troubleshooting

### Database Issues
```bash
# Reset test database
python manage.py test --keepdb=False
```

### Import Errors
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### MySQL Connection
Verify settings in `capstone/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'inventory_mngmnt',
        # ... other settings
    }
}
```

---

## Next Steps

1. **Maintain Tests**: Update tests when adding new features
2. **Add Integration Tests**: Test API endpoints and views
3. **Performance Tests**: Add tests for performance-critical operations
4. **Load Tests**: Test system under high load
5. **E2E Tests**: Add end-to-end UI tests with Selenium

---

## Support

For issues or questions:
1. Check `TEST_SUMMARY.md` for detailed results
2. Review test code in `inventory/tests.py`
3. Check Django testing documentation

---

**Last Updated**: October 2025  
**Status**: ✅ All 54 tests passing


# Testing Guidelines

## CRITICAL RULES - ALWAYS FOLLOW

### ❌ ABSOLUTE PROHIBITIONS

1. **NO COMMENTS IN CODE** - You are FORBIDDEN from writing comments in test code
   - **EXCEPTION**: Only write a comment when explaining a non-obvious "why" that cannot be understood from the code itself
   - **WRONG**: `# Test user creation`
   - **ACCEPTABLE**: `# Sleep required here due to async event propagation in external system`

2. **NO INLINE IMPORTS** - You are FORBIDDEN from using inline imports
   - **EXCEPTION**: Only use inline imports to break circular import dependencies
   - **WRONG**:

     ```python
     def test_something():
         from app.models import User  # FORBIDDEN
     ```

   - **ACCEPTABLE**:

     ```python
     def get_user_model():
         # Breaking circular import between models.user and models.profile
         from app.models import User
         return User
     ```

### ✅ MANDATORY REQUIREMENTS

1. **MUST USE Python 3.12+ with STRICT TYPE HINTS**
   - Every function parameter MUST have a type hint
   - Every function return value MUST have a type hint
   - Use `None` return type explicitly: `-> None`
   - Use proper generic types: `list[str]`, `dict[str, Any]`

2. **MUST CHECK EXISTING TESTS BEFORE ADDING NEW ONES**
   - **STEP 1**: Search for parameterized tests that can be extended
   - **STEP 2**: Search for similar tests that can be converted to parameterized
   - **STEP 3**: Only create new test functions if Steps 1-2 are not applicable

3. **MUST REUSE EXISTING SETUP CODE**
   - **STEP 1**: Check for existing setup code in the test file
   - **STEP 2**: Extract reusable setup code into fixtures
   - **STEP 3**: Check conftest.py for existing fixtures before creating new ones

4. **MUST TEST ONLY FUNCTIONAL/LOGICAL CODE**
   - **DO NOT TEST**: Simple data classes, Pydantic models, SQLModel models with only field definitions
   - **DO TEST**: Validation logic, computed properties, business methods, transformations
   - **WRONG**: Testing that `User.name = "John"` sets name to "John"
   - **RIGHT**: Testing that `User.age = -1` raises ValidationError

## MOCKING STRATEGY

### Repository Mocking Pattern

When mocking repositories and async components, use `AsyncMock` from the standard library instead of `create_autospec` to avoid type ignore comments:

```python
from unittest.mock import AsyncMock
import pytest

from app.domains.users.repositories import UserRepository
from app.domains.users.models import User


@pytest.fixture
def mock_user_repository() -> AsyncMock:
    """Mock UserRepository for testing."""
    mock = AsyncMock(spec=UserRepository)
    mock._model_class = User  # Add expected attributes
    return mock


@pytest.fixture
def user_service(mock_user_repository: AsyncMock) -> UserService:
    """UserService instance with mocked repository."""
    return UserService(mock_user_repository)


class TestUserService:
    """Test suite for UserService."""

    @pytest.mark.asyncio
    async def test_creates_user_successfully(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
        sample_user: User,
    ) -> None:
        """Test successful user creation."""
        mock_user_repository.create.return_value = sample_user

        result = await user_service.create_user(sample_user)

        assert result == sample_user
        mock_user_repository.create.assert_called_once_with(sample_user)
```

**Key Benefits:**

- **No `# type: ignore` comments needed** - `AsyncMock(spec=Class)` properly supports attribute mocking
- **Cleaner test code** - Direct method mocking without typing workarounds
- **Better type safety** - Maintains interface specification while allowing flexible mocking

**Avoid:**

```python
# DON'T USE - Requires type ignore comments
@pytest.fixture
def mock_repository(mocker: MockerFixture) -> UserRepository:
    return mocker.create_autospec(UserRepository, spec_set=True)

# Results in:
mock_repository.create.return_value = user  # type: ignore[attr-defined]
```

## TEST IMPLEMENTATION RULES

### Test Naming Convention

You MUST use action-oriented naming with ACTIVE VERBS:

```python
# For error scenarios
def test_raises_[error_type]_when_[condition]() -> None:
    """Test that [error_type] is raised when [condition]."""

# For successful execution - use any active verb
def test_[active_verb]_[action]_successfully() -> None:
    """Test successful execution of [action]."""
    # Examples: runs, creates, modifies, displays, enables, sends,
    #           processes, calculates, transforms, updates, deletes

# For object/state changes
def test_[active_verb]_[object]_with_[condition]() -> None:
    """Test [object] [verb] with [condition]."""
    # Examples: creates_user_with_valid_data
    #           modifies_settings_with_admin_role
    #           enables_feature_with_premium_account

# For validation/checking logic
def test_[active_verb]_[field]_[constraint]() -> None:
    """Test [field] [constraint] [verb]."""
    # Examples: validates_email_format
    #           checks_password_strength
    #           verifies_token_expiration
```

**VERB REQUIREMENTS**:

- MUST be in active form (creates, NOT creating or created)
- MUST be descriptive of the actual action
- MUST be appropriate for the test's purpose

### Test Structure Template

You MUST follow this exact structure:

```python
"""Test suite for [module_name]."""

from typing import Any, Generator
import pytest
from unittest.mock import Mock, MagicMock
from pytest_mock import MockerFixture

from app.module import ComponentToTest


@pytest.fixture
def sample_data() -> dict[str, Any]:
    """Provide sample test data."""
    return {"key": "value"}


class TestComponentName:
    """Test suite for ComponentName."""

    def test_creates_component_with_valid_data(
        self,
        sample_data: dict[str, Any]
    ) -> None:
        """Test successful component creation."""
        result = ComponentToTest(**sample_data)
        assert result.key == "value"

    def test_raises_validation_error_when_invalid(self) -> None:
        """Test validation error for invalid data."""
        with pytest.raises(ValueError, match="specific error message"):
            ComponentToTest(key="invalid")

    @pytest.mark.parametrize(
        "input_value,expected",
        [
            ("test1", "result1"),
            ("test2", "result2"),
            (None, "default"),
        ],
        ids=["normal_case", "edge_case", "none_case"]
    )
    def test_handles_multiple_inputs(
        self,
        input_value: str | None,
        expected: str
    ) -> None:
        """Test handling of various input values."""
        result = ComponentToTest.process(input_value)
        assert result == expected
```

## BEFORE WRITING ANY TEST

### Decision Tree - Follow This Exact Order

```txt
1. Can I extend an existing parameterized test?
   └─ YES → Add new parameter values to existing test
   └─ NO → Continue to 2

2. Can I convert an existing test to parameterized?
   └─ YES → Convert test and add both cases
   └─ NO → Continue to 3

3. Is there existing setup code I can extract?
   └─ YES → Extract to fixture first, then write test
   └─ NO → Continue to 4

4. Does conftest.py have a fixture I can use?
   └─ YES → Use existing fixture
   └─ NO → Create new fixture if setup is reusable

5. Write new test function following naming conventions
```

### Example: Extending Existing Tests

**BEFORE adding a new test, check if you can extend:**

```python
# EXISTING TEST - Check this first!
@pytest.mark.parametrize(
    "status,expected",
    [
        ("active", True),
        ("inactive", False),
    ]
)
def test_validates_user_status(status: str, expected: bool) -> None:
    """Test user status validation."""
    assert User.is_valid_status(status) == expected

# DO THIS - Extend the existing test
@pytest.mark.parametrize(
    "status,expected",
    [
        ("active", True),
        ("inactive", False),
        ("pending", True),  # NEW CASE ADDED HERE
        ("deleted", False),  # NEW CASE ADDED HERE
    ]
)
def test_validates_user_status(status: str, expected: bool) -> None:
    """Test user status validation."""
    assert User.is_valid_status(status) == expected

# DON'T DO THIS - Create a separate test
def test_validates_pending_status() -> None:  # WRONG - Should extend existing
    """Test pending status validation."""
    assert User.is_valid_status("pending") is True
```

## PYTEST BEST PRACTICES

### DO - Required Practices

1. **DO use pytest-mock over unittest.mock**

   ```python
   def test_with_mock(mocker: MockerFixture) -> None:
       """Test with proper mocking."""
       mock_func = mocker.patch("app.module.function")
       mock_func.return_value = "mocked"
   ```

2. **DO use fixtures for ALL reusable data**

   ```python
   @pytest.fixture
   def user_data() -> dict[str, Any]:
       """Provide user test data."""
       return {"name": "Test", "email": "test@example.com"}
   ```

3. **DO use pytest.mark.usefixtures for fixtures not accessed directly**

   ```python
   # WRONG - Adding unused fixture to function signature
   def test_with_database(db_session: Session) -> None:
       """Test that requires database."""
       result = some_function()  # db_session never used
       assert result == expected

   # RIGHT - Use decorator for setup-only fixtures
   @pytest.mark.usefixtures("db_session")
   def test_with_database() -> None:
       """Test that requires database."""
       result = some_function()  # db initialized via fixture
       assert result == expected
   ```

4. **DO test all scenarios**
   - Happy path (successful execution)
   - Error scenarios (all possible errors)
   - Edge cases (None, empty, boundary values)
   - Validation errors (Pydantic constraints)

5. **DO write independent tests**
   - Each test MUST run successfully in isolation
   - Tests MUST NOT depend on execution order

### DON'T - Forbidden Practices

1. **DON'T repeat test setup code**
   - Extract to fixtures immediately

2. **DON'T write tests without type hints**
   - All parameters and returns MUST be typed

3. **DON'T use manual setup when fixtures exist**
   - Always check for existing fixtures first

4. **DON'T write docstrings longer than one line**
   - Keep docstrings concise and single-line

## TEST EXECUTION COMMANDS

Execute these commands from `/workspace/backend` directory:

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=term

# Run specific test file
pytest tests/unit/domains/users/test_services.py

# Run tests matching pattern
pytest -k "test_create"

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

## EXCEPTION TESTING WITH pytest.raises

### MANDATORY PATTERN: Using match Parameter

You MUST use `pytest.raises` with the `match` parameter when testing exceptions and their messages:

```python
def test_raises_validation_error_when_age_negative() -> None:
    """Test that negative age raises validation error."""
    with pytest.raises(ValueError, match="Age must be between 0 and 150"):
        User(name="John", email="john@example.com", age=-1)
```

### Exception Testing Rules

1. **ALWAYS use match parameter** - Never test exceptions without verifying the message
2. **Use regex patterns** - The `match` parameter accepts regular expressions
3. **Escape special characters** - Use `r"raw strings"` to avoid escaping issues
4. **Test exact messages** - Use `^` and `$` anchors for exact matching

### Exception Testing Examples

```python
# CORRECT - Testing specific error message
def test_raises_value_error_when_invalid_input() -> None:
    """Test ValueError is raised for invalid input."""
    with pytest.raises(ValueError, match="Invalid input value"):
        process_input("invalid")

# CORRECT - Using regex patterns
def test_raises_error_with_regex_match() -> None:
    """Test exception with regex pattern matching."""
    with pytest.raises(RuntimeError, match=r"Error \d+: .* failed"):
        risky_operation()

# CORRECT - Exact message matching
def test_raises_exact_error_message() -> None:
    """Test exact error message matching."""
    with pytest.raises(TypeError, match="^Expected string, got int$"):
        invalid_function(123)

# CORRECT - Multiple possible messages
def test_raises_one_of_multiple_messages() -> None:
    """Test exception with one of multiple possible messages."""
    with pytest.raises(ConnectionError, match="Connection (timeout|refused|lost)"):
        connect_to_server()

# WRONG - No message verification
def test_raises_error_without_message_check() -> None:  # FORBIDDEN
    """Test that should verify message but doesn't."""
    with pytest.raises(ValueError):  # Missing match parameter
        validate_data("bad_data")
```

### Advanced Exception Testing

```python
# Testing exception details with excinfo
def test_captures_exception_details() -> None:
    """Test exception details capture."""
    with pytest.raises(DatabaseError, match="Connection failed") as excinfo:
        connect_to_database("invalid_host")

    assert excinfo.type is DatabaseError
    assert "Connection failed" in str(excinfo.value)
    assert excinfo.value.errno == 1001

# Testing nested exceptions
def test_raises_chained_exception() -> None:
    """Test chained exception handling."""
    with pytest.raises(ServiceError, match="Service unavailable") as excinfo:
        call_external_service()

    assert excinfo.value.__cause__ is not None
    assert isinstance(excinfo.value.__cause__, ConnectionError)
```

### Parameterized Exception Testing

```python
@pytest.mark.parametrize(
    "invalid_input,expected_message",
    [
        ("", "Input cannot be empty"),
        ("   ", "Input cannot be whitespace only"),
        ("x" * 1000, "Input too long"),
        ("invalid@", "Invalid format"),
    ],
    ids=["empty", "whitespace", "too_long", "invalid_format"]
)
def test_raises_validation_error_for_invalid_inputs(
    invalid_input: str,
    expected_message: str
) -> None:
    """Test validation errors for various invalid inputs."""
    with pytest.raises(ValidationError, match=expected_message):
        validate_user_input(invalid_input)
```

### FORBIDDEN Practices

```python
# WRONG - No message checking
with pytest.raises(ValueError):  # Missing match
    bad_function()

# WRONG - Using deprecated message parameter
with pytest.raises(ValueError, message="Custom fail message"):  # DEPRECATED
    bad_function()

# WRONG - Not using raw strings for regex
with pytest.raises(ValueError, match="\d+ errors found"):  # Should use r"\d+ errors found"
    bad_function()

# WRONG - Testing exception type only
try:  # Don't use try/except, use pytest.raises
    risky_function()
    assert False, "Should have raised exception"
except ValueError:
    pass
```

## COVERAGE REQUIREMENTS

You MUST achieve these coverage targets:

1. **100% function coverage** - Every function must have tests
2. **100% class coverage** - Every class must have tests
3. **100% method coverage** - Every method must have tests
4. **Edge case coverage** - Test with:
   - Empty inputs: `[]`, `{}`, `""`
   - None values: `None`
   - Boundary values: `0`, `-1`, `sys.maxsize`
   - Invalid types: wrong type inputs

## WHAT TO TEST vs WHAT NOT TO TEST

### ❌ DO NOT TEST - Simple Data Classes

```python
# DO NOT write tests like these for simple models:

class User(BaseModel):  # Pydantic model
    name: str
    email: str
    age: int

# WRONG - Testing simple assignment
def test_sets_user_name() -> None:
    """Test setting user name."""
    user = User(name="John", email="john@example.com", age=30)
    assert user.name == "John"  # POINTLESS TEST

# WRONG - Testing Pydantic's built-in functionality
def test_creates_user_model() -> None:
    """Test user model creation."""
    user = User(name="John", email="john@example.com", age=30)
    assert isinstance(user, User)  # POINTLESS TEST
```

### ✅ DO TEST - Validation Logic and Computed Properties

```python
# DO write tests for models with logic:

class User(BaseModel):
    name: str
    email: EmailStr
    age: int

    @field_validator("age")
    def validate_age(cls, v: int) -> int:
        if v < 0 or v > 150:
            raise ValueError("Age must be between 0 and 150")
        return v

    @property
    def is_adult(self) -> bool:
        return self.age >= 18

    def calculate_retirement_years(self) -> int:
        retirement_age = 65
        return max(0, retirement_age - self.age)

# RIGHT - Testing custom validation
def test_raises_validation_error_when_age_negative() -> None:
    """Test that negative age raises validation error."""
    with pytest.raises(ValueError, match="Age must be between 0 and 150"):
        User(name="John", email="john@example.com", age=-1)

# RIGHT - Testing computed property
def test_determines_adult_status_correctly() -> None:
    """Test adult status determination."""
    minor = User(name="Teen", email="teen@example.com", age=17)
    adult = User(name="Adult", email="adult@example.com", age=18)

    assert minor.is_adult is False
    assert adult.is_adult is True

# RIGHT - Testing business logic method
@pytest.mark.parametrize(
    "age,expected_years",
    [(30, 35), (65, 0), (70, 0)],
    ids=["working_age", "at_retirement", "past_retirement"]
)
def test_calculates_retirement_years(age: int, expected_years: int) -> None:
    """Test retirement years calculation."""
    user = User(name="Worker", email="worker@example.com", age=age)
    assert user.calculate_retirement_years() == expected_years
```

## EXAMPLE: COMPLETE TEST FILE

This example demonstrates a MIX of single and parameterized tests:

```python
"""Test suite for user services."""

from typing import Any
from datetime import datetime
from uuid import UUID

import pytest
from pytest_mock import MockerFixture

from app.domains.users.services import UserService
from app.domains.users.models import User
from app.domains.users.exceptions import UserNotFoundError, DuplicateEmailError


@pytest.fixture
def user_service() -> UserService:
    """Provide UserService instance."""
    return UserService()


@pytest.fixture
def valid_user_data() -> dict[str, Any]:
    """Provide valid user data."""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "age": 25
    }


@pytest.fixture
def mock_email_service(mocker: MockerFixture) -> Mock:
    """Provide mocked email service."""
    return mocker.patch("app.domains.users.email.send_welcome_email")


class TestUserService:
    """Test suite for UserService."""

    def test_creates_user_with_valid_data(
        self,
        user_service: UserService,
        valid_user_data: dict[str, Any],
        mocker: MockerFixture
    ) -> None:
        """Test successful user creation."""
        mock_save = mocker.patch("app.domains.users.repository.save")
        mock_save.return_value = User(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            **valid_user_data
        )

        result = user_service.create_user(**valid_user_data)

        assert result.email == valid_user_data["email"]
        assert result.name == valid_user_data["name"]
        mock_save.assert_called_once()

    def test_raises_duplicate_email_error_when_email_exists(
        self,
        user_service: UserService,
        valid_user_data: dict[str, Any],
        mocker: MockerFixture
    ) -> None:
        """Test that DuplicateEmailError is raised for existing email."""
        mocker.patch(
            "app.domains.users.repository.find_by_email",
            return_value=User(
                id=UUID("12345678-1234-5678-1234-567812345678"),
                **valid_user_data
            )
        )

        with pytest.raises(DuplicateEmailError, match="Email already exists"):
            user_service.create_user(**valid_user_data)

    @pytest.mark.usefixtures("mock_email_service")
    def test_sends_welcome_email_after_creation(
        self,
        user_service: UserService,
        valid_user_data: dict[str, Any],
        mocker: MockerFixture
    ) -> None:
        """Test welcome email is sent after user creation."""
        mocker.patch("app.domains.users.repository.save", return_value=User(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            **valid_user_data
        ))

        user_service.create_user(**valid_user_data)

        # mock_email_service fixture is used but not accessed directly

    @pytest.mark.parametrize(
        "age,should_be_adult",
        [
            (17, False),
            (18, True),
            (19, True),
            (65, True),
        ],
        ids=["minor", "exactly_18", "young_adult", "senior"]
    )
    def test_verifies_adult_status_correctly(
        self,
        user_service: UserService,
        age: int,
        should_be_adult: bool
    ) -> None:
        """Test adult status verification for various ages."""
        user = User(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            email="test@example.com",
            name="Test User",
            age=age
        )

        assert user_service.is_adult(user) == should_be_adult

    def test_deletes_user_successfully(
        self,
        user_service: UserService,
        mocker: MockerFixture
    ) -> None:
        """Test successful user deletion."""
        user_id = UUID("12345678-1234-5678-1234-567812345678")
        mock_delete = mocker.patch("app.domains.users.repository.delete")
        mock_find = mocker.patch(
            "app.domains.users.repository.find_by_id",
            return_value=User(
                id=user_id,
                email="test@example.com",
                name="Test User",
                age=25
            )
        )

        user_service.delete_user(user_id)

        mock_find.assert_called_once_with(user_id)
        mock_delete.assert_called_once()

    @pytest.mark.parametrize(
        "email",
        [
            "invalid-email",
            "@example.com",
            "user@",
            "",
            None,
        ],
        ids=["no_at", "no_local", "no_domain", "empty", "none"]
    )
    def test_raises_validation_error_for_invalid_email(
        self,
        user_service: UserService,
        email: str | None
    ) -> None:
        """Test validation error for various invalid email formats."""
        with pytest.raises(ValueError, match="Invalid email"):
            user_service.create_user(
                email=email,
                name="Test User",
                age=25
            )
```

**KEY POINTS**:

- Some tests are single test cases (when testing one specific scenario)
- Some tests are parameterized (when testing multiple similar cases)
- Use parameterization when the test logic is identical for multiple inputs
- Use single tests when the scenario is unique or complex

## FINAL CHECKLIST

Before submitting any test code, verify:

- [ ] NO comments (except non-obvious "why" explanations)
- [ ] NO inline imports (except for circular dependencies)
- [ ] ALL functions have complete type hints with return types
- [ ] Checked for existing parameterized tests to extend
- [ ] Checked for existing setup code to extract as fixtures
- [ ] Every test has a single-line docstring
- [ ] Test names follow exact naming conventions
- [ ] Used pytest-mock (mocker) instead of unittest.mock
- [ ] Tests are independent and can run in any order
- [ ] Covered happy path, errors, and edge cases

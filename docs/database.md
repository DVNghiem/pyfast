# Database Guide

## Overview

The database module provides a powerful ORM-like functionality for database operations. It supports multiple field types, relationships, and includes built-in validation.

## Database Configuration

To configure your database connection, use the `DatabaseConfig` class:

```python
from hypern.hypern import DatabaseConfig, DatabaseType

config = DatabaseConfig(
    driver=DatabaseType.Postgres,  # or MySQL, SQLite
    url="postgresql://user:password@localhost:5432/dbname",
    max_connections=10,
    min_connections=1,
    idle_timeout=30
)

app = Hypern(database_config=config)
```

## Defining Models

Models are defined by creating classes that inherit from the base `Model` class:

```python
from hypern.database import Model, CharField, IntegerField, DateTimeField

class User(Model):
    name = CharField(max_length=100)
    age = IntegerField(null=True)
    created_at = DateTimeField(auto_now_add=True)
```

## Available Field Types

### CharField
```python
name = CharField(
    max_length=255,
    min_length=0,
    null=True,
    default=None,
    unique=False,
    index=False,
    regex=None
)
```

### IntegerField
```python
age = IntegerField(
    min_value=None,
    max_value=None,
    null=True,
    default=None,
    unique=False,
    index=False
)
```

### DecimalField
```python
price = DecimalField(
    max_digits=10,
    decimal_places=2,
    min_value=None,
    max_value=None,
    null=True
)
```

### DateField
```python
birth_date = DateField(
    auto_now=False,
    auto_now_add=False,
    min_date=None,
    max_date=None
)
```

### DateTimeField
```python
created_at = DateTimeField(
    auto_now=False,
    auto_now_add=True,
    timezone_aware=True
)
```

### JSONField
```python
metadata = JSONField(
    schema=None,  # Optional JSON schema for validation
    null=True
)
```

### ArrayField
```python
tags = ArrayField(
    base_field=CharField(max_length=50),
    min_length=None,
    max_length=None
)
```

### ForeignKey
```python
department = ForeignKey(
    to_model="Department",
    on_delete="CASCADE",
    on_update="CASCADE"
)
```

## Querying Data

### Basic Queries

```python
# Get all users
users = User.objects().execute()

# Get filtered users
adults = User.objects().where(age__gte=18).execute()

# Get first user
first_user = User.objects().limit(1).execute()

# Order users by age
ordered_users = User.objects().order_by('age').execute()
```

### Complex Queries

```python
from hypern.database import Q, F

# Complex where conditions
users = User.objects().where(
    Q(age__gte=18) & Q(name__contains='John') | Q(is_admin=True)
).execute()

# Using F expressions for field comparisons
employees = Employee.objects().where(
    salary__gt=F('department__avg_salary')
).execute()
```

### Aggregations and Window Functions

```python
# Using window functions
User.objects().select(
    'name',
    F('salary').avg().over(
        partition_by='department',
        order_by='hire_date'
    ).as_('rolling_avg_salary')
).execute()
```

## Transactions

```python
def transfer_money(from_account, to_account, amount):
    try:
        transaction = Account.get_session()
        # Perform operations
        transaction.execute(
            "UPDATE accounts SET balance = balance - $1 WHERE id = $2",
            [amount, from_account]
        )
        transaction.execute(
            "UPDATE accounts SET balance = balance + $1 WHERE id = $2",
            [amount, to_account]
        )
        transaction.commit()
    except Exception:
        transaction.rollback()
        raise
```

## Working with Results

```python
# Create new record
user = User(name="John Doe", age=30)
user.save()

# Bulk create
users = [
    User(name="User 1", age=25),
    User(name="User 2", age=30)
]
User.objects().bulk_create(users)

# Update records
User.objects().where(age__lt=18).update(is_minor=True)

# Delete records
User.objects().where(is_active=False).delete()
```

## Best Practices

1. Always use transactions for multiple related operations
2. Use field validation for data integrity
3. Create indexes for frequently queried fields
4. Use appropriate field types for data
5. Set proper constraints (null, unique, etc.)
6. Handle database errors appropriately

## Error Handling

```python
from hypern.exceptions import DBFieldValidationError

try:
    user = User(name="John", age=-1)
    user.save()
except DBFieldValidationError as e:
    print(f"Validation error: {e}")
```

This documentation covers the main features of the database module. For more specific use cases or advanced features, consult the API reference.
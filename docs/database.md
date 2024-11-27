# Hypern Database Documentation

## Overview
Hypern provides a powerful database abstraction layer with an intuitive query builder inspired by Django ORM. This documentation covers how to define models, create queries, and work with the database.

## Model Definition

### Basic Model Structure
```python
from hypern.db import Model, CharField, IntegerField

class User(Model):
    __tablename__ = 'users'  # Specify the table name
    name = CharField(max_length=100)
    age = IntegerField()
    email = CharField(max_length=255, unique=True)
```

### Available Field Types
- `CharField`: String fields with max_length
- `TextField`: Unlimited length text
- `IntegerField`: Integer values
- `FloatField`: Floating point numbers
- `BooleanField`: True/False values
- `DateTimeField`: Date and time
- `DateField`: Date only
- `JSONField`: JSON data
- `ArrayField`: Array/List of values
- `DecimalField`: Decimal numbers
- `ForeignKey`: Relationships between models

## Querying

### Basic Queries
```python
# Get all users
users = User.objects().execute()

# Filter records
adult_users = User.objects().where(age__gte=18).execute()

# Order results
ordered_users = User.objects().order_by('name').execute()
```

### Complex Queries
```python
from hypern.db import Q, F

# Combining conditions with Q objects
User.objects().where(
    Q(age__gte=18) & Q(name__startswith='A')
).execute()

# Using F expressions for field comparisons
User.objects().where(
    F('age') * 2 > 30
).execute()
```

### Aggregation and Grouping
```python
# Count users by age
User.objects()
    .group_by('age')
    .annotate(count=F('id').count())
    .execute()
```

### Joins
```python
# Join with other tables
User.objects()
    .join('orders', 'orders.user_id = users.id')
    .execute()
```

## Transactions
Transaction support is built-in and can be used with context managers (not implemented yet).

## Advanced Features

### Window Functions
```python
from hypern.db import Window

User.objects()
    .annotate(
        rank=F('salary').rank().over(
            partition_by='department',
            order_by='-salary'
        )
    ).execute()
```

### Bulk Operations
```python
# Bulk create
users = [User(name='User1'), User(name='User2')]
User.objects().bulk_create(users)

# Bulk update
User.objects().where(age__lt=18).update(status='minor')
```

## Query Optimization

### Explaining Queries
```python
# Get query execution plan
User.objects().where(age__gte=18).explain(analyze=True)
```

For more detailed information about specific features, please refer to the source code documentation.
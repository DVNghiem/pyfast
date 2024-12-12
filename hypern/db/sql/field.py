from typing import Any


class Field:
    def __init__(
        self,
        field_type: str,
        primary_key: bool = False,
        null: bool = True,
        default: Any = None,
        unique: bool = False,
        index: bool = False,
        validators: list = None,
    ):
        self.field_type = field_type
        self.primary_key = primary_key
        self.null = null
        self.default = default
        self.unique = unique
        self.index = index
        self.validators = validators or []
        self.name = None
        self.model = None

    def sql_type(self) -> str:
        type_mapping = {
            "int": "INTEGER",
            "str": "VARCHAR(255)",
            "float": "FLOAT",
            "bool": "BOOLEAN",
            "datetime": "TIMESTAMP",
            "date": "DATE",
            "text": "TEXT",
            "json": "JSONB",
            "array": "ARRAY",
            "decimal": "DECIMAL",
        }
        return type_mapping.get(self.field_type, "VARCHAR(255)")

    def validate(self, value: Any) -> None:
        if value is None and not self.null:
            raise ValueError(f"Field {self.name} cannot be null")

        for validator in self.validators:
            validator(value)


class CharField(Field):
    def __init__(self, max_length: int = 255, **kwargs):
        super().__init__("str", **kwargs)
        self.max_length = max_length

    def sql_type(self) -> str:
        return f"VARCHAR({self.max_length})"


class TextField(Field):
    def __init__(self, **kwargs):
        super().__init__("text", **kwargs)


class IntegerField(Field):
    def __init__(self, **kwargs):
        super().__init__("int", **kwargs)


class FloatField(Field):
    def __init__(self, **kwargs):
        super().__init__("float", **kwargs)


class BooleanField(Field):
    def __init__(self, **kwargs):
        super().__init__("bool", **kwargs)


class DateTimeField(Field):
    def __init__(self, auto_now: bool = False, auto_now_add: bool = False, **kwargs):
        super().__init__("datetime", **kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add


class DateField(Field):
    def __init__(self, auto_now: bool = False, auto_now_add: bool = False, **kwargs):
        super().__init__("date", **kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add


class JSONField(Field):
    def __init__(self, **kwargs):
        super().__init__("json", **kwargs)


class ArrayField(Field):
    def __init__(self, base_field: Field, **kwargs):
        super().__init__("array", **kwargs)
        self.base_field = base_field

    def sql_type(self) -> str:
        return f"{self.base_field.sql_type()}[]"


class DecimalField(Field):
    def __init__(self, max_digits: int = 10, decimal_places: int = 2, **kwargs):
        super().__init__("decimal", **kwargs)
        self.max_digits = max_digits
        self.decimal_places = decimal_places

    def sql_type(self) -> str:
        return f"DECIMAL({self.max_digits},{self.decimal_places})"


class ForeignKey(Field):
    def __init__(self, to_model: str, on_delete: str = "CASCADE", on_update: str = "CASCADE", **kwargs):
        super().__init__("int", **kwargs)
        self.to_model = to_model
        self.on_delete = on_delete
        self.on_update = on_update

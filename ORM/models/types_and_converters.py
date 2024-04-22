from decimal import Decimal
from datetime import datetime


def string_converter(value) -> str:
    assert isinstance(value, str)
    return value


def bool_converter(value) -> bool:
    if value == 'True':
        return True
    if value == 'False':
        return False
    raise ValueError(f'Value: {value} cannot be converted to boolean')


def int_converter(value) -> int:
    return int(value)


def decimal_converter(value) -> Decimal:
    return Decimal(value)


def date_converter(value) -> datetime.date:
    return datetime.fromisoformat(value).date()


TYPE_CONVERTER_MAP = {
    str: string_converter,
    bool: bool_converter,
    int: int_converter,
    Decimal: decimal_converter,
    datetime.date: date_converter,
}

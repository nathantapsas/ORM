import operator
import sys
import typing
from types import NoneType
from typing import Any, Union, get_origin, get_args, List, Optional
from inspect import get_annotations
import ORM.database
from .types_and_converters import TYPE_CONVERTER_MAP


class PrimaryKey:
    def __new__(cls, *args, **kwargs) -> None:
        cls_dict = sys._getframe(1).f_locals
        cls_dict['_primary_key'] = tuple([*args])


class Relationship:
    _initialized = False

    def __init__(self,
                 reference_columns: tuple[str, ...] = None,
                 related_model: type['Model'] | str = None,
                 related_columns: tuple[str, ...] = None,
                 condition: 'Condition' = None
                 ) -> None:
        self.reference_columns = reference_columns
        self.related_columns = related_columns
        self.condition = condition
        self.related_model = related_model

    def __set_name__(self, owner, name: str) -> None:
        self.column_name = name
        self.is_nullable = False
        annotation = get_annotations(owner).get(name, None)

        if annotation is None:
            raise TypeError(f"No type annotation for {name} in {owner.__name__}")

        origin_type = get_origin(annotation)
        if origin_type in (list, List):
            self.many = True
            annotation = get_args(annotation)[0]
        elif origin_type in (Optional, Union):
            self.is_nullable = True
            args = get_args(annotation)

            if list_type := next((arg for arg in args if get_origin(arg) in (list, List)), None):
                self.many = True
                # Assuming there's only one list type in the Union/Optional
                annotation = get_args(list_type)[0]
            else:
                self.many = False
                annotation = next((arg for arg in args if not isinstance(arg, NoneType)), None)
        else:
            self.many = False

        annotation = annotation.__forward_arg__ if isinstance(annotation, typing.ForwardRef) else annotation

        if self.related_model is None:
            if isinstance(annotation, str) or (isinstance(annotation, type) and issubclass(annotation, Model)):
                self.related_model = annotation
            else:
                raise ValueError(f"Invalid type annotation for {name}: {annotation}")

        if self.reference_columns is None:
            self.reference_columns = (self.column_name,)

    def __get__(self, instance: 'Model', owner: type['Model']) -> Union['Relationship', 'Model', list['Model'], None]:
        if not instance:
            return self
        reference_values = tuple(instance._data[field] for field in self.reference_columns)
        related_instance_data = owner.database.get_index(
            self.related_model, self.related_columns).get(reference_values, [])

        if self.condition:
            related_instance_data = list(filter(self.condition.evaluate, related_instance_data))

        if self.many:
            return [self.related_model(row) for row in related_instance_data]

        if len(related_instance_data) > 1:
            raise ValueError(f'Expected 1 related instance, got {len(related_instance_data)}')

        if len(related_instance_data) == 0:
            if self.is_nullable:
                return None
            raise ValueError(f'Expected 1 related instance, got 0')
        return self.related_model(related_instance_data[0])

    def __eq__(self, other) -> 'Condition':
        return Condition(lambda x: x == other, self.column_name)

    def __nq__(self, other) -> 'Condition':
        return Condition(lambda x: x != other, self.column_name)


class Field:
    def __init__(self, column_name=None) -> None:
        self.column_name = column_name

    def __set_name__(self, owner, name: str) -> None:
        if self.column_name is None:
            self.column_name = name

        annotation = get_annotations(owner).get(name, None)

        if annotation is None:
            raise TypeError(f"No type annotation for {name} in {owner.__name__}")

        if get_origin(annotation) in (Optional, Union):
            self.d_type = next((arg for arg in get_args(annotation) if not isinstance(arg, NoneType)), None)
            self.is_nullable = True
        else:
            self.d_type = annotation
            self.is_nullable = False

        self.converter = TYPE_CONVERTER_MAP[self.d_type]

    def __get__(self, instance, owner) -> Any:
        # TODO: Try caching the values as class attributes and timing the difference.
        if not instance:
            return self

        # TODO: Handle nullable fields.
        #  This will involve changing the dataframe output so that null values are not represented as empty strings.
        if self.is_nullable:
            try:
                return self.converter(instance._data[self.column_name])
            except Exception:
                return None

        return self.converter(instance._data[self.column_name])

    def __eq__(self, other) -> 'Condition':
        return Condition(lambda x: x == other, self.column_name)

    def __nq__(self, other) -> 'Condition':
        return Condition(lambda x: x != other, self.column_name)


class Condition:
    def __init__(self, operation, field_name) -> None:
        self.operation = operation
        self.field_name = field_name

    def evaluate(self, record) -> bool:
        result = self.operation(record.get(self.field_name))
        return result

    def __and__(self, other: 'Condition') -> 'CombinedCondition':
        return CombinedCondition(self, other, operator.and_)

    def __or__(self, other: 'Condition') -> 'CombinedCondition':
        return CombinedCondition(self, other, operator.or_)


class CombinedCondition:
    def __init__(self, left: 'Condition', right: 'Condition', combiner: typing.Callable[[Any, Any], bool]) -> None:
        self.left = left
        self.right = right
        self.combiner = combiner

    def evaluate(self, record) -> bool:
        left_result = self.left.evaluate(record)
        right_result = self.right.evaluate(record)
        result = self.combiner(left_result, right_result)
        return result


class MetaModel(type):
    database = ORM.database.Database


class Model(metaclass=MetaModel):
    # Todo: Investigate a caching mechanism so that we don't have to create a new instance of a model every time.
    _table_name: str
    _primary_key: tuple[str, ...] | None = None
    _fields: dict[str, Field]
    _relationships: dict[str, Relationship]
    _initialized: bool = False

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        fields = {name: attr for name, attr in cls.__dict__.items() if isinstance(attr, Field)}
        if hasattr(cls, '_fields'):
            cls._fields |= fields
        else:
            cls._fields = fields

        relationships = {name: attr for name, attr in cls.__dict__.items() if isinstance(attr, Relationship)}
        if hasattr(cls, '_relationships'):
            cls._relationships |= relationships
        else:
            cls._relationships = relationships

    @classmethod
    def map_relationships(cls):
        for relationship in cls._relationships.values():
            if relationship._initialized:
                continue

            if isinstance(relationship.related_model, str):
                relationship.related_model = cls.database.resolve_related_model(relationship.related_model)

            relationship.related_columns = relationship.related_columns or relationship.related_model._primary_key
            cls.database.create_index(relationship.related_model, relationship.related_columns)
            relationship._initialized = True
        cls._initialized = True

    def __init__(self, data: dict[str, str]) -> None:
        self._data = data

    @classmethod
    def select(cls, where: Condition | None = None):
        df = cls.database.get_dataframe(cls)

        if where is not None:
            if not isinstance(where, Condition):
                raise TypeError(f'Expected Condition, got {type(where)}')
            for row in df:
                if where.evaluate(row):
                    yield cls(row)
        else:
            for row in df:
                yield cls(row)

    # TODO: Make the primary key index not return lists
    @classmethod
    def get(cls, primary_key: tuple[str, ...]) -> Optional['Model']:

        if model := cls.database.get_index(cls, cls._primary_key).get(primary_key, None):
            return cls(model[0])
        return None

    def __repr__(self):
        fields = ', '.join(f'{name}={getattr(self, name)}' for name in self._fields)
        return f'{self.__class__.__name__}({fields})'

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self._data == other._data

    def __hash__(self):
        return hash(tuple(self._data.values()))

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ORM.models import Model

DataFrame = list[dict[str, str]]


def dataframe_group_by(df: DataFrame, columns: tuple[str, ...]) -> dict[tuple[str, ...], 'DataFrame']:
    result = {}
    for row in df:
        key = tuple(row[column] for column in columns)
        result.setdefault(key, list()).append(row)

    return result


class Database:
    _models: dict[str, type['Model']] = {}
    _dataframes: dict[str, DataFrame] = {}
    _indexes: dict[str, dict[tuple[str, ...], dict[tuple[str, ...], DataFrame]]] = {}
    _initialized: bool = False

    @classmethod
    def set_dataframe(cls, model: type['Model'], df: DataFrame) -> None:
        """Sets the dataframe for a model."""
        for field in model._fields.values():
            if field.column_name not in df[0]:
                raise KeyError(f'Field {field.column_name} of model {model.__name__} not found in dataframe.')

        cls._models[model.__name__] = model
        cls._dataframes[model.__name__] = df

        cls.initialize()

    @classmethod
    def initialize(cls) -> None:
        for model in cls._models.values():
            if model._initialized or not hasattr(model, '_relationships'):
                continue
            try:
                model.map_relationships()
            except KeyError:
                break
        else:
            cls._initialized = True

    @classmethod
    def resolve_related_model(cls, model_name) -> type['Model']:
        """Resolves a model name to a model class."""
        return cls._models[model_name]

    @classmethod
    def create_index(cls, model: type['Model'], index: tuple[str, ...]) -> None:
        """Creates an index for a model."""
        indexes = cls._indexes.setdefault(model.__name__, {})
        if index not in indexes:
            df = cls._dataframes[model.__name__]
            indexes[index] = dataframe_group_by(df, index)

    @classmethod
    def get_index(cls, model_class, index) -> dict[tuple[str, ...], DataFrame]:
        return cls._indexes[model_class.__name__][index]

    @classmethod
    def get_dataframe(cls, model_class) -> DataFrame:
        if not cls._initialized:
            raise Exception('Database has not been initialized')
        return cls._dataframes[model_class.__name__]

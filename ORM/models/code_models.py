from ORM.models.base_model import Field, Model, PrimaryKey


class IACode(Model, str):
    PrimaryKey('code')

    code: str = Field()
    description: str = Field()

    def __new__(cls, row):
        return str.__new__(cls, row['code'])

    def __repr__(self):
        return f'{self.__class__.__name__}(code={self}, description={self.description})'

    def __hash__(self):
        return hash(str(self.code))

    def __eq__(self, other):
        if isinstance(other, IACode):
            return self.code == other.code

        return str(self.code) == other


class TransactionCode(Model, str):
    PrimaryKey('code')

    code: str = Field()
    description: str = Field()

    def __new__(cls, row):
        return str.__new__(cls, row['code'])

    def __repr__(self):
        return f'{self.__class__.__name__}(code={self}, description={self.description})'

    def __hash__(self):
        return hash(str(self.code))

    def __eq__(self, other):
        if isinstance(other, TransactionCode):
            return self.code == other.code

        return str(self.code) == other
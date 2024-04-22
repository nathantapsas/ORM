from decimal import Decimal
from typing import TYPE_CHECKING

from ORM.models.base_model import Relationship, Field, Model

if TYPE_CHECKING:
    from . import Account, TransactionCode


class Transaction(Model):
    account: 'Account' = Relationship(reference_columns=('account_number',))
    transaction_code: 'TransactionCode' = Relationship()

    cusip: str = Field()
    funds: str = Field()
    ia_code: str = Field()

    amount: Decimal = Field()
    int_value: Decimal = Field()
    cost: Decimal = Field()
    quantity: Decimal = Field()
    exchange_rate: Decimal = Field()

    description: str = Field()
    transaction_cancelled: bool = Field()

    def __str__(self):
        return f'{self.transaction_code} {self.account} {self.cusip} {self.amount} {self.description}'

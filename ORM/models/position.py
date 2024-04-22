from decimal import Decimal
from typing import TYPE_CHECKING

from ORM.models.base_model import Relationship, Field, Model, PrimaryKey

if TYPE_CHECKING:
    from . import IACode, Security, Account


class Position(Model):
    PrimaryKey('account_number', 'cusip')

    account: 'Account' = Relationship(reference_columns=('account_number',), related_columns=('number',))
    security: 'Security' = Relationship(reference_columns=('cusip',))
    ia_code: 'IACode' = Relationship()

    current_quantity: Decimal = Field()
    pending_quantity: Decimal = Field()
    segregated_quantity: Decimal = Field()
    safekeeping_quantity: Decimal = Field()

    def __str__(self):
        return (f'{self.__class__.__name__}: {self.security} '
                f'Current: {self.current_quantity} '
                f'Pending: {self.pending_quantity} '
                f'Segregated: {self.segregated_quantity} '
                f'Safekeeping: {self.safekeeping_quantity}')

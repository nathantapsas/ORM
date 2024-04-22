from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from ORM.models.base_model import Relationship, Field, Model, PrimaryKey

if TYPE_CHECKING:
    from . import Account, IACode


class FeeGroup(Model):
    PrimaryKey('group_id')

    group_id: int = Field()
    name: str = Field()
    group_portfolio_type: str = Field()
    ia_code: 'IACode' = Relationship()
    fund_type: str = Field()

    fee_basis: str = Field()
    trades_allowed: int = Field()
    free_trades_available: int = Field()
    minimum_fee: Decimal = Field()
    rate: Decimal = Field()

    money_manager_code: str = Field()
    fee_adjustment_type: str = Field()
    fee_adjustment: Decimal = Field()

    anniversary_date: datetime.date = Field()


class AccountFeeData(Model):
    account: 'Account' = Relationship(reference_columns=('account_number',))
    fee_account_number: 'Account' = Relationship()

    fee_group: 'FeeGroup' = Relationship(reference_columns=('group_id',))
    ia_percentage: Decimal = Field()
    date_joined: datetime.date = Field()

    # Make optional fields check for nulls
    date_left: Optional[datetime.date] = Field()

    mm_fund: str = Field()
    payment_type: str = Field()
    schedule_type: str = Field()
    sell_security: str = Field()
    is_active: bool = Field()

    # Remove this
    market_value: Decimal = Field()


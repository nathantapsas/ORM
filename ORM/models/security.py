from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from ORM.models.base_model import Relationship, Field, Model, PrimaryKey


class Security(Model):
    PrimaryKey('cusip')

    cusip: str = Field()

    market: str = Field()
    status: str = Field()
    security_class: str = Field('class')
    name: str = Field()
    isin: str = Field()
    funds: str = Field()
    trades_ok: bool = Field()
    call_put: str = Field()
    primary_symbol: str = Field()
    under_symbol: str = Field()
    code: str = Field()
    incorporation_country: str = Field()
    us_eci: bool = Field()
    convertible: bool = Field()
    price_status: str = Field()
    expiry_date: Optional[datetime.date] = Field()

    comment: str = Field()

    strike_price: Decimal = Field()
    ask: Decimal = Field()
    bid: Decimal = Field()
    last_trade: Decimal = Field()

    under_cusip: 'Security' = Relationship()

    def __str__(self):
        return f'{self.cusip} {self.name}'

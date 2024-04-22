from functools import cached_property
from typing import TYPE_CHECKING, Optional
from decimal import Decimal
from datetime import datetime

from ORM.models.base_model import Relationship, Field, PrimaryKey, Model
from .account_related_models import Subscriber, Beneficiary

if TYPE_CHECKING:
    from . import (
        Client,
        Address,
        SubscriberBeneficiary,
        Beneficiary,
        Subscriber,
        EFT,
        Transaction,
        AccountFeeData,
        IACode,
        Position,
    )


class Account(Model):
    PrimaryKey('number')

    number: str = Field()
    ia_code: 'IACode' = Relationship()
    status: str = Field()
    trades_okay: bool = Field()

    open_date: datetime.date = Field()
    close_date: Optional[datetime.date] = Field()

    account_type: str = Field('type')
    sub_type: str = Field()
    funds: str = Field()
    portfolio_type: str = Field()
    class_code: int = Field()

    residence_code: str = Field()
    minimum_commission_check: bool = Field()
    commission_type: str = Field()
    credit_int: str = Field()
    debit_int: str = Field()
    is_discretionary: bool = Field()


    ni54_email: str = Field()
    ni54_mail: str = Field()
    ni54_objecting: str = Field()
    option_approval: int = Field()

    market_value: Decimal = Field()
    equity: Decimal = Field()
    loan_value: Decimal = Field()
    settle_date_balance: Decimal = Field()
    trade_date_balance: Decimal = Field()

    client: 'Client' = Relationship(
        reference_columns=('client_code',))

    address: Optional[list['Address']] = Relationship(
        reference_columns=('number',),
        related_columns=('account_number',))

    positions: Optional[list['Position']] = Relationship(
        reference_columns=('number',),
        related_columns=('account_number',))

    _sub_benes: Optional[list['SubscriberBeneficiary']] = Relationship(
        reference_columns=('number',),
        related_columns=('account_number',))

    efts: list['EFT'] = Relationship(
        reference_columns=('number',),
        related_columns=('account_number',))

    transactions: list['Transaction'] = Relationship(
        reference_columns=('number',),
        related_columns=('account_number',))

    fee_data: Optional['AccountFeeData'] = Relationship(
        reference_columns=('number',),
        related_columns=('account_number',))

    @cached_property
    def is_active(self):
        return self.status == 'A'

    @property
    def subscribers(self) -> list['Subscriber']:
        """Returns a list of all subscribers on the account. Only valid for RESPs and RDSPs."""
        if self.sub_type[0] in {'E', 'V', 'D'}:
            return [record for record in self._sub_benes if isinstance(record, Subscriber)]

        raise ValueError('Subscribers are only recorded for RESPs and RDSPs')

    @property
    def beneficiaries(self) -> list['Beneficiary']:
        """Returns a list of all beneficiaries on the account. Only valid for RESPs and RDSPs."""
        if self.sub_type[0] in {'E', 'V', 'D'}:
            return [record for record in self._sub_benes if isinstance(record, Beneficiary)]

        raise ValueError('Beneficiaries are only recorded for RESPs and RDSPs')

    @cached_property
    def prefix(self) -> str:
        """The first three characters of an account number. Only used for client accounts."""
        if self.is_client:
            return self.number[:3]
        raise ValueError("Non-client accounts don't have reliable prefixes.")

    @cached_property
    def suffix(self) -> str:
        """The last digit of an account number. Only used for client accounts."""
        if self.is_client:
            return self.number[-1]
        raise ValueError("Non-client accounts don't have reliable suffixes.")

    @cached_property
    def is_client(self) -> bool:
        """Returns True if the account is a client account."""
        return self.number[0] == '0'

    @cached_property
    def is_commission(self) -> bool:
        return self.portfolio_type not in {'M', 'F', 'S'}

    @cached_property
    def is_managed(self) -> bool:
        return self.portfolio_type == 'M'

    @cached_property
    def is_fee_based(self) -> bool:
        return self.portfolio_type == 'F'

    @cached_property
    def is_sma(self) -> bool:
        return self.portfolio_type == 'S'

    @cached_property
    def is_cod(self) -> bool:
        """Returns True if the account is a client account."""
        return self.account_type[0] == '1'

    @cached_property
    def is_corporate(self) -> bool:
        """Returns True if the account belongs to a corporation."""
        return self.client.recipient_type == 3

    @cached_property
    def is_pro(self) -> bool:
        """Returns True if the account belongs to a professional."""
        return self.client.is_pro

    def __str__(self) -> str:
        return f'{self.number}'


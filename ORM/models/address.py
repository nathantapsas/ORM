from functools import cached_property
from typing import TYPE_CHECKING, Union, Optional

from ORM.models.base_model import Field, Relationship, Model, PrimaryKey

if TYPE_CHECKING:
    from . import Client, Account


class Address(Model):
    PrimaryKey('client_code', 'account_number', 'sequence_number')

    sequence_number: int = Field()
    statement: bool = Field()
    statement_copies: int = Field()
    confirm_copies: int = Field()
    internal_confirm_copies: int = Field()
    hold_statement: bool = Field()

    line_1: str = Field()
    line_2: str = Field()
    line_3: str = Field()
    line_4: str = Field()
    line_5: str = Field()
    line_6: str = Field()
    line_7: str = Field()
    line_8: str = Field()
    country: str = Field()

    cell_phone: str = Field()
    home_phone: str = Field()
    work_phone: str = Field()
    other_phone_1: str = Field()
    other_phone_2: str = Field()
    other_phone_3: str = Field()
    other_phone_4: str = Field()

    client: 'Client' = Relationship(reference_columns=('client_code',))
    account: Optional['Account'] = Relationship(reference_columns=('account_number',))

    def __new__(cls, row) -> Union['CivicAddress', 'RuralAddress', 'FreeFormAddress']:
        structured = row['is_structured'] == 'True'
        civic = row['is_civic'] == 'True'
        if not structured:
            return super(Address, cls).__new__(FreeFormAddress)
        if not civic:
            return super(Address, cls).__new__(RuralAddress)
        return super(Address, cls).__new__(CivicAddress)

    @cached_property
    def lines(self) -> list[str]:
        """Returns a list of all lines in the address."""
        return [self.line_1, self.line_2, self.line_3, self.line_4, self.line_5, self.line_6, self.line_7, self.line_8]

    @property
    def phone_numbers(self) -> list[str]:
        """Returns a list of all phone numbers in the address."""
        return [number for number in (self.cell_phone, self.home_phone, self.work_phone, self.other_phone_1,
                self.other_phone_2, self.other_phone_3, self.other_phone_4) if number]

    @property
    def is_canadian(self) -> bool:
        """Returns True if the address is in Canada, False otherwise."""
        return self.country == 'CAN'

    @property
    def is_us(self) -> bool:
        """Returns True if the address is in the USA, False otherwise."""
        return self.country == 'USA'

    def __str__(self) -> str:
        return '\n'.join(line for line in self.lines if line)

    @property
    def is_account_level(self) -> bool:
        return self.account is not None


class CivicAddress(Address):
    unit_number: str = Field()
    unit_type: str = Field()
    civic_number: str = Field()
    street: str = Field()
    street_type: str = Field()
    direction: str = Field()
    city: str = Field()
    province: str = Field()
    postal_code: str = Field()


class RuralAddress(Address):
    station_name: str = Field()
    station_type: str = Field()
    mail_mode: str = Field()
    mail_box: str = Field()
    mail_station: str = Field()
    mail_id: str = Field()
    province: str = Field()
    postal_code: str = Field()


class FreeFormAddress(Address):
    ...

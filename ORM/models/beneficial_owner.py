from typing import Optional
from typing import TYPE_CHECKING
from decimal import Decimal
from datetime import datetime

from ORM.models.base_model import Field, PrimaryKey, Model, Relationship, Condition

if TYPE_CHECKING:
    from . import Client, Address, CRSRecord


class BeneficialOwner(Model):
    PrimaryKey('client_code', 'sequence_number')

    sequence_number: int = Field()
    title: str = Field()

    first_name: str = Field()
    last_name: str = Field()
    # birth_date: str = Field()

    sin: str = Field()
    us_taxpayer_id_type: str = Field()
    ssn: str = Field()
    foreign_taxpayer_id: str = Field()

    uci: str = Field()
    uci_percentage: Decimal = Field()

    residence_code: str = Field()
    citizenship: str = Field()
    country_of_birth: str = Field()

    recipient_code: str = Field('1042_recipient_code')
    w9_on_file: bool = Field()
    w8_ben_date_received: Optional[datetime.date] = Field()
    limitation_of_benefits: bool = Field()
    cra_id_details: str = Field()
    cra_treaty: bool = Field()
    identification_type_received: str = Field()

    type_of_intermediary: str = Field()
    renounced_us_citizenship: bool = Field()
    crs_holder_type: str = Field()
    fatca_certification_status: str = Field()
    beneficial_owner_id: str = Field()
    holder_type: str = Field()
    holder_sub_type: str = Field()

    client: 'Client' = Relationship(reference_columns=('client_code',))

    address: Optional['Address'] = Relationship(
        reference_columns=('client_code', 'address_number'),
        related_columns=('client_code', 'sequence_number'),
        condition=Condition(lambda x: x == '', 'account_number'))

    crs_records: list['CRSRecord'] = Relationship(
        reference_columns=('client_code', 'sequence_number'),
        related_columns=('client_code', 'beneficial_owner_sequence_number'))

    def __str__(self) -> str:
        return f'Title: {self.title}\tName: {" ".join(name for name in (self.first_name, self.last_name) if name)}'

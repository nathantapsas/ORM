from decimal import Decimal
from typing import Union, TYPE_CHECKING

from ORM.models.base_model import Relationship, Field, PrimaryKey, Model

if TYPE_CHECKING:
    from . import BeneficialOwner


class SubscriberBeneficiary(Model):
    is_active: bool = Field()
    birth_date: str = Field()
    uci: str = Field()
    uci_percentage: Decimal = Field()
    first_name: str = Field()
    last_name: str = Field()
    relationship: int = Field()
    sin: str = Field()
    gender: str = Field()
    guardian: str = Field()
    primary_caregiver_first_name: str = Field()
    primary_caregiver_last_name: str = Field()
    primary_caregiver_sin: str = Field()
    primary_caregiver_id_type: str = Field()

    def __new__(cls, row) -> Union['Subscriber', 'Beneficiary']:
        record = row['record_type']
        if record == 'BENEF':
            return super(SubscriberBeneficiary, cls).__new__(Beneficiary)
        elif record == 'SUBSCR':
            return super(SubscriberBeneficiary, cls).__new__(Subscriber)

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.first_name} {self.last_name}'

    def __repr__(self) -> str:
        fields = ', '.join(f'{name}={getattr(self, name)}' for name in self._fields)
        return f'{self.__class__.__name__}({fields})'


class Subscriber(SubscriberBeneficiary):
    ...


class Beneficiary(SubscriberBeneficiary):
    ...


class CRSRecord(Model):
    PrimaryKey('client_code', 'beneficial_owner_sequence_number', 'record_number')

    certification_status: str = Field()
    citizenship: str = Field()
    tax_jurisdiction: str = Field()
    foreign_tax_id: str = Field()
    reason_code: str = Field()
    reason_notes: str = Field()
    certified_by: str = Field()

    beneficial_owner: 'BeneficialOwner' = Relationship(
        reference_columns=('client_code', 'beneficial_owner_sequence_number'))

    def __str__(self):
        return f'{self.__class__.__name__}: {self.citizenship} {self.tax_jurisdiction} {self.foreign_tax_id}'


class EFT(Model):
    PrimaryKey('account_number', 'sequence_number')

    bank_institution_number: str = Field()
    bank_branch_number: str = Field()
    bank_account_number: str = Field()

    third_party: bool = Field()

    bank_country: str = Field()
    description: str = Field()
    funds: str = Field()

    payee_line_1: str = Field()
    payee_line_2: str = Field()
    payee_line_3: str = Field()
    payee_line_4: str = Field()
    payee_line_5: str = Field()
    payee_line_6: str = Field()
    # delete this
    crs_records: list[CRSRecord] = Relationship(related_model='CRSRecord', reference_columns=('account_number',))

    @property
    def payee_lines(self):
        return [line for line in [self.payee_line_1,
                                  self.payee_line_2,
                                  self.payee_line_3,
                                  self.payee_line_4,
                                  self.payee_line_5,
                                  self.payee_line_6] if line]

    def __str__(self):
        return f'{self.bank_institution_number} {self.bank_branch_number} {self.bank_account_number}'

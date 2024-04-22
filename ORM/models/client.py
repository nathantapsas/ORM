from datetime import datetime
from typing import Optional
from typing import TYPE_CHECKING

from ORM.models.base_model import Relationship, Field, Model, PrimaryKey

if TYPE_CHECKING:
    from . import Account, Address, BeneficialOwner, IACode, KYCInformation


ENTITY_RECIPIENT_TYPES = {3, 4, 5, 6}


class Client(Model):
    PrimaryKey("code")

    code: int = Field()
    status: str = Field()
    ia_code: "IACode" = Relationship()
    recipient_type: int = Field()
    first_name: str = Field()
    last_name: str = Field()
    birth_date: Optional[datetime.date] = Field()
    residence_code: str = Field()
    employee: str = Field()
    monitor_code: str = Field()
    citizenship: str = Field()
    is_us_person: bool = Field()
    sin: str = Field()
    ssn: str = Field()
    corporate_id_type: str = Field()
    corporate_id: str = Field()
    verification_id: str = Field()
    spouse_name: str = Field()
    spouse_sin: str = Field()
    spouse_birth_date: Optional[datetime.date] = Field()
    nrt_code: bool = Field()

    beneficial_owners: list["BeneficialOwner"] = Relationship(
        reference_columns=("code",), related_columns=("client_code",)
    )

    accounts: list["Account"] = Relationship(
        reference_columns=("code",), related_columns=("client_code",)
    )

    addresses: list["Address"] = Relationship(
        reference_columns=("code",), related_columns=("client_code",)
    )

    # TODO: Why do some clients not have kyc information?
    kyc_information: Optional["KYCInformation"] = Relationship(
        reference_columns=("code",)
    )

    @property
    def is_active(self) -> bool:
        return self.status == "A"

    @property
    def unique_id_object(self):
        """Returns the unique ID object for the client."""

        return frozenset(bene.sin for bene in self.beneficial_owners if bene.sin)

    @property
    def primary_address(self) -> Optional["Address"]:
        # TODO: Fix logic for Account level addresses
        if not self.addresses:
            return None

        addresses = sorted(self.addresses, key=lambda addr: addr.sequence_number)

        for address in addresses:
            if any(
                (
                    address.internal_confirm_copies > 0,
                    address.confirm_copies > 0,
                    address.statement_copies > 0,
                    address.statement,
                )
            ):
                return address

        return addresses[0]

    @property
    def is_entity(self) -> bool:
        """Returns True if the client is an entity, False otherwise."""
        return self.recipient_type in ENTITY_RECIPIENT_TYPES

    @property
    def is_pro(self) -> bool:
        """Returns True if the client is an employee or non-employee professional, False otherwise."""
        return self.employee in {"Y", "P"}

    @property
    def is_employee(self) -> bool:
        """Returns True if the client is an employee, False otherwise."""
        return self.employee == "Y"

    @property
    def is_non_employee_pro(self) -> bool:
        """Returns True if the client is a non-employee professional, False otherwise."""
        return self.employee == "P"

    @property
    def has_client_account(self) -> bool:
        return any(account.is_client for account in self.accounts)

    @property
    def has_non_cod_account(self) -> bool:
        return any(not account.is_cod for account in self.accounts)

    def __str__(self) -> str:
        string = (
            f'Client Code: {str(self.code).rjust(8)}\t'
            f'Name: {" ".join(name for name in (self.last_name, self.first_name) if name).ljust(36)}'
        )

        if self.status != "A":
            string += f"\tStatus: {self.status}"

        return string

from decimal import Decimal
from typing import Optional
from datetime import datetime
from ORM.models.base_model import Field, Model, PrimaryKey


class KYCInformation(Model):
    PrimaryKey("client_code")

    sex: str = Field()
    marital_status: str = Field()
    number_of_dependants: str = Field()

    employee_name: str = Field()
    employee_address: str = Field()
    employee_type: str = Field()
    occupation: str = Field()
    employee_years: str = Field()

    spouse_employment_type: str = Field()
    spouse_employment_address: str = Field()
    spouse_employer: str = Field()
    spouse_occupation: str = Field()

    ia_met: bool = Field()
    relation_name: str = Field()
    relation_position: str = Field()
    date_met: Optional[datetime.date] = Field()
    approved_by: str = Field()
    referred_by: str = Field()

    bank_account: str = Field()
    bank_check: bool = Field()
    credit_check: bool = Field()

    estimated_net_worth: Decimal = Field()
    fixed_assets: Decimal = Field()
    liquid_assets: Decimal = Field()
    income: Decimal = Field()

    investor_knowledge: str = Field()

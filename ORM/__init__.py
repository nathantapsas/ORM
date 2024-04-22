import csv
import json
import time
from datetime import datetime
from decimal import Decimal
from functools import wraps
from pathlib import Path

from ORM.database import Database, DataFrame
from ORM.models import (
    EFT,
    Account,
    AccountFeeData,
    Address,
    BeneficialOwner,
    Client,
    CRSRecord,
    FeeGroup,
    IACode,
    KYCInformation,
    Position,
    Security,
    SubscriberBeneficiary,
    Transaction,
    TransactionCode,
)


def timed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end - start} seconds")
        return result

    return wrapper


SQL_TO_PYTHON_TYPE_MAP = {
    "Int32": int,
    "Int8": int,
    "string": str,
    "date": datetime.date,
    "Decimal": Decimal,
    "boolean": bool,
}

source_data_dir = Path("../csv_cleaning/output")
metadata_dir = Path("../csv_cleaning/table_metadata")


def load_database():
    data_and_models = [
        ("clients.csv", Client, "clients.json"),
        ("accounts.csv", Account, "accounts.json"),
        ("addresses.csv", Address, "addresses.json"),
        ("beneficial_owners.csv", BeneficialOwner, "bene_owners.json"),
        ("resp_rdsp.csv", SubscriberBeneficiary, "resp_rdsp.json"),
        ("crs.csv", CRSRecord, "crs.json"),
        ("eft.csv", EFT, "eft.json"),
        ("transactions.csv", Transaction, "transactions.json"),
        ("fee_groups.csv", FeeGroup, "fee_groups.json"),
        ("fee_accounts.csv", AccountFeeData, "fee_accounts.json"),
        ("ia_codes.csv", IACode, "ia_codes.json"),
        ("transaction_codes.csv", TransactionCode, "transaction_codes.json"),
        ("positions.csv", Position, "positions.json"),
        ("securities.csv", Security, "securities.json"),
        ("kyc.csv", KYCInformation, "kyc.json"),
    ]

    for data_filename, model_class, metadata_filename in data_and_models:
        with open(metadata_dir / metadata_filename, "r") as f:
            metadata = json.load(f)

        metadata_fields = {
            field["db_column_name"]: field["data_type"]
            for field in metadata["columns"]
            if field.get("db_column_name")
        }

        for field in model_class._fields.values():
            if field.column_name not in metadata_fields:
                raise Exception(
                    f"Column {field.column_name} not found in metadata for {model_class.__name__}"
                )
            elif field.d_type != SQL_TO_PYTHON_TYPE_MAP.get(
                metadata_fields[field.column_name]
            ):
                raise Exception(
                    f"Column {field.column_name} of model {model_class.__name__} has type {field.d_type} "
                    f"but metadata specifies {metadata_fields[field.column_name]}"
                )

        with open(source_data_dir / data_filename, "r", encoding='latin') as f:
            data = list(csv.DictReader(f, delimiter="|"))
        Database.set_dataframe(model_class, DataFrame(data))


load_database()
with open(source_data_dir / "metadata.json", "r") as f:
    SNAPSHOT_DATE = datetime.date(datetime.strptime(json.load(f)["date"], "%Y-%m-%d"))

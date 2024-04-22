from functools import wraps

import pandas as pd
import json
import csv
from decimal import Decimal
from stock_record import parse_stock_record
from file_prep import prep_files
import pathlib
import logging
from datetime import datetime

logger = logging.getLogger("csv_cleaning")

data_metadata = [
    ("client_table", "table_metadata/clients.json"),
    ("account_table", "table_metadata/accounts.json"),
    ("address_table", "table_metadata/addresses.json"),
    ("irs_table", "table_metadata/bene_owners.json"),
    ("resp_table", "table_metadata/resp_rdsp.json"),
    ("rdsp_table", "table_metadata/resp_rdsp.json"),
    ("crs", "table_metadata/crs.json"),
    ("cheque_payee_table", "table_metadata/eft.json"),
    ("transaction_table", "table_metadata/transactions.json"),
    ("fee_group_table", "table_metadata/fee_groups.json"),
    ("fee_account_table", "table_metadata/fee_accounts.json"),
    ("ia_code_table", "table_metadata/ia_codes.json"),
    ("trans_code_table", "table_metadata/transaction_codes.json"),
    ("stock_record", "table_metadata/positions.json"),
    ("security_table_1", "table_metadata/securities.json"),
    ("security_table_2", "table_metadata/securities.json"),
    ("kyc_table", "table_metadata/kyc.json"),
]


def convert_boolean(true_string):
    @wraps(convert_boolean)
    def converter(value: str):
        return true_string == value.upper()

    return converter


def convert_int():
    @wraps(convert_int)
    def converter(value: str):
        if not value:
            return 0
        return int(value.replace(",", ""))

    return converter


def convert_decimal(column):
    positive_suffix = column.get("positive_suffix", "")
    negative_suffix = column.get("negative_suffix", "")
    negative_prefix = column.get("negative_prefix", "")

    @wraps(convert_decimal)
    def converter(value: str):
        if not value:
            return Decimal(0)
        # Remove commas for consistent processing
        value = value.replace(",", "")

        if value.startswith("????"):
            return Decimal(999999999999)

        # TODO: Handle cases where the value is not a valid Decimal
        if positive_suffix:
            if value.endswith(positive_suffix):
                # Remove positive_suffix and return positive Decimal
                return Decimal(value.replace(positive_suffix, ""))
            else:
                # Convert to negative Decimal
                result = Decimal(value)
                return result * -1 if result != 0 else result
        elif negative_suffix:
            if value.endswith(negative_suffix):
                # Remove negative_suffix and return negative Decimal
                result = Decimal(value.replace(negative_suffix, ""))
                return result * -1 if result != 0 else result
            else:
                # Return positive Decimal
                return Decimal(value)
        elif negative_prefix:
            if value.startswith(negative_prefix):
                # Remove negative_prefix and convert to negative Decimal
                result = Decimal(value.replace(negative_prefix, ""))
                return result * -1 if result != 0 else result
            else:
                # Return positive Decimal
                return Decimal(value)
        else:
            # Default case: Convert to Decimal as is
            return Decimal(value)

    return converter


def convert_date():
    @wraps(convert_date)
    def converter(value: str):
        if not value:
            return None
        if len(value) == 10:
            return datetime.strptime(value, "%m/%d/%Y").date()
        return datetime.strptime(value, "%m/%d/%y").date()

    return converter


def get_converter_map(metadata):
    converters = {}
    for column in metadata["columns"]:
        column_names = column.get("csv_column_name")
        if not column_names:
            continue

        if not isinstance(column_names, list):
            column_names = [column_names]

        for column_name in column_names:
            if column["data_type"] == "boolean":
                converters[column_name] = convert_boolean(column["boolean_true_string"])
            elif column["data_type"] == "Decimal":
                converters[column_name] = convert_decimal(column)
            elif column["data_type"] in {"Int8", "Int16", "Int32", "Int64"}:
                converters[column_name] = convert_int()
            elif column["data_type"] == "date":
                converters[column_name] = convert_date()
    return converters


def get_name_map(metadata):
    name_map = {}
    for column in metadata["columns"]:
        if column.get("csv_column_name"):
            if isinstance(column["csv_column_name"], list):
                for csv_column_name in column["csv_column_name"]:
                    name_map[csv_column_name] = column["db_column_name"]
            else:
                name_map[column["csv_column_name"]] = column["db_column_name"]
    return name_map


def get_dtype_map(metadata):
    dtype_map = {}
    for column in metadata["columns"]:
        if column.get("csv_column_name") and column["data_type"] not in (
            "boolean",
            "Decimal",
            "date",
            "Int8",
            "Int16",
            "Int32",
            "Int64",
        ):
            if isinstance(column["csv_column_name"], list):
                for csv_column_name in column["csv_column_name"]:
                    dtype_map[csv_column_name] = column["data_type"]
            else:
                dtype_map[column["csv_column_name"]] = column["data_type"]
    return dtype_map


def get_na_values_map(metadata):
    return {
        column["csv_column_name"]: ""
        for column in metadata["columns"]
        if column.get("csv_column_name") and column.get("is_nullable")
    }


def clean_csvs():
    tables: dict[str, tuple[dict, list[pd.DataFrame]]] = {}

    for data_file, metadata_file in data_metadata:
        with open(metadata_file, "r", encoding="latin") as f:
            metadata = json.load(f)

        converters = get_converter_map(metadata)
        name_map = get_name_map(metadata)
        dtype_map = get_dtype_map(metadata)
        na_values_map = get_na_values_map(metadata)
        data_file_path = next(pathlib.Path("source_data").glob(f"*{data_file}*.txt"))

        logger.info(f"Processing {data_file_path}")

        df = pd.read_csv(
            data_file_path,
            encoding="latin",
            sep="|",
            quotechar='"',
            doublequote=False,
            keep_default_na=False,
            converters=converters,
            dtype=dtype_map,
            na_values=na_values_map,
        )
        df.rename(columns=name_map, inplace=True)
        tables.setdefault(metadata["table_name"], (metadata, list()))[1].append(df)

    merged_tables: dict[str, tuple[dict, pd.DataFrame]] = {}
    # Concatenate tables
    for table_name, (metadata, df_list) in tables.items():
        if len(df_list) > 1:
            logger.info(f"Concatenating {len(df_list)} DataFrames for {table_name}")
            merged_table = pd.concat(df_list, ignore_index=True, sort=False)
            merged_table = merged_table.drop_duplicates(
                subset=[
                    col["db_column_name"]
                    for col in metadata["columns"]
                    if col.get("db_column_name")
                ]
            )
            merged_tables[table_name] = (metadata, merged_table)
        else:
            merged_tables[table_name] = (metadata, df_list[0])

    # Remove rows with invalid foreign keys
    for table_name, (metadata, df) in merged_tables.items():
        if "foreign_keys" in metadata:
            temp_df = df.copy()
            for fk_constraint in metadata["foreign_keys"]:
                foreign_key = fk_constraint["column"]
                reference_table = fk_constraint["references"]["table"]
                reference_column = fk_constraint["references"]["column"]

                # Filter and update temp_df
                valid_rows = pd.isna(temp_df[foreign_key]) | temp_df[foreign_key].isin(
                    merged_tables[reference_table][1][reference_column]
                )
                temp_df = temp_df[valid_rows]

            logger.info(
                f"Filtered {table_name} to {len(temp_df)} rows. Removed {len(df) - len(temp_df)} rows."
            )
            # Update the original DataFrame after processing all foreign keys
            merged_tables[table_name] = (metadata, temp_df)

    # Clean up any specific tables
    for table_name, (metadata, df) in merged_tables.items():
        if table_name == "transactions":
            df["transaction_code"] = df["transaction_code"].apply(
                lambda x: x.split(" ")[0] if pd.notna(x) and " " in x else x
            )

        if table_name == "securities":
            df.dropna(subset=["cusip"], inplace=True)
            assert df["cusip"].is_unique, "Cusip is not unique"
            # assert cusip column is unique
    # Export to CSV
    for metadata, table in merged_tables.values():
        logger.info(
            f'Exporting Table\n{metadata["table_name"]}\n'
            f"Columns and Types: \n {str(table.dtypes)}"
            f"Columns Excluded:  "
            f"{str([col for col in table.columns if col not in get_name_map(metadata).values()])}"
        )
        table.to_csv(
            f'{output_folder}/{metadata["table_name"]}.csv',
            sep="|",
            columns=list(get_name_map(metadata).values()),
            encoding="latin",
            index=False,
            quotechar='"',
            quoting=csv.QUOTE_NONNUMERIC,
        )

    # Copy metadata file
    # metadata_file = pathlib.Path("source_data/metadata.json")
    # metadata_file_destination = pathlib.Path(f"{output_folder}/metadata.json")
    # with open(metadata_file_destination, "w") as f:
    #     f.write(metadata_file.read_text())


if __name__ == "__main__":
    output_folder = "output"
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename="output/csv_cleaning.log",
        filemode="w",
    )
    prep_files()
    parse_stock_record()
    clean_csvs()

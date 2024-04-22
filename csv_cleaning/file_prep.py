import pathlib
from datetime import datetime
from datetime import timedelta


def prep_files():
    directory = pathlib.Path().home().joinpath("FTP")

    for file in directory.iterdir():
        if file.is_dir():
            continue

        modified_datetime = datetime.fromtimestamp(file.stat().st_mtime)

        # anything created before 5 am will be considered for the day before
        if modified_datetime.hour <= 5:
            modified_datetime -= timedelta(days=1)

        modified_date_string = str(modified_datetime.date())

        folder_path = directory / modified_date_string
        if not folder_path.exists():
            folder_path.mkdir()
            # Create metadata file
            with open(folder_path / "metadata.json", "w") as f:
                f.write(
                    f'{{"date": "{modified_date_string}""]}}'
                )

        try:
            file.rename(folder_path / file.name)
        except FileExistsError as e:
            print(e)


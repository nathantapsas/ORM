from itertools import zip_longest, accumulate, groupby
import re
import csv
import pathlib


def is_seperator(line: str) -> bool:
    """Matches any string that contains at least twenty hyphens,
    optionally surrounded by spaces and no other characters."""
    pattern = re.compile(r"^(?=.*-)[ -]*(-[ -]*){20,}$")
    result = pattern.match(line)
    return result is not None


def get_field_widths(line: str) -> tuple[int, ...]:
    """Takes string and records count of groups of matching consecutive characters.
    if the characters are whitespace characters, count is negative."""
    result = tuple(sum(1 for _ in g) * (-1 if re.search(r"\s", k) is not None else 1) for k, g in groupby(line))
    return result


class FixedWidthParser:
    def __init__(self, column_and_pad_widths: tuple[int, ...]) -> None:
        col_and_pad_indexes = tuple(width for width in accumulate(abs(width) for width in column_and_pad_widths))
        is_pad = tuple(width < 0 for width in column_and_pad_widths)  # bool flags for padding fields
        self.fields = \
            tuple(zip_longest(is_pad, (0,) + col_and_pad_indexes, col_and_pad_indexes))[:-1]  # ignore final one

    def parse_line(self, line: str) -> tuple[list[str], list[str]]:
        """Parses a line of text into fields and pads based on the defined column and padding widths."""
        fields, pads = [line[start:end] for pad, start, end in self.fields if not pad], \
            [line[start:end] for pad, start, end in self.fields if pad]

        return fields, pads


def parse_stock_record():
    file_path = next(pathlib.Path('source_data').glob('ws*'))
    lines_with_cusip = []
    current_cusip = None
    field_widths = (10, -2, 3, -1, 16, -2, 5, -2, 4, -2, 12, -2, 1, -2, 12, -2, 12, -2, 12, -2, 8)
    parser = FixedWidthParser(field_widths)

    with open(file_path, 'r', encoding='latin') as f:
        pages = f.read().split('\f')
        for page in pages:
            lines = page.split('\n')
            for line in lines:
                if not line or line.startswith('--------'):
                    continue

                if 'BID: ' in line and 'ASK: ' in line:
                    current_cusip = line.split('  ')[0]

                elif line[3] == '-' and line[8] == '-':
                    if is_seperator(line):
                        continue
                    fields, pads = parser.parse_line(line)
                    fields = [field.strip() for field in fields]
                    lines_with_cusip.append(fields + [current_cusip])

                elif ('*** ExeClear Brokerage System ***' in line
                      or line.startswith('Account         Client  ')
                      or (line.startswith('CUSIP: ALL') and 'Run Code:' in line)
                      or line.startswith('Leede Jones Gable Inc.')
                      or (line.startswith('Weekly Stock Record') and 'Processed:' in line)
                      or line.startswith('*** End of Report ***')):
                    continue
                else:
                    raise ValueError(line)

    writer = csv.writer(open('source_data/stock_record.txt', 'w', newline=''),
                        delimiter='|', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(
        ['Account', 'Funds', 'Client', 'Type', 'IA', 'Current', 'And Column What is This',
         'Pending', 'Segregated', 'Safekeeping', 'Date', 'Cusip'])
    writer.writerows(lines_with_cusip)


if __name__ == '__main__':
    parse_stock_record()

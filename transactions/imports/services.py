import csv
import io
import logging
from transactions.choices import ImportStatus
from transactions.models import DataImport

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_ROW_LIMIT = 2000
ALLOWED_EXTENSIONS = ['.csv']
REQUIRED_HEADER_GROUPS = [
    ('date', ['date', 'txn_date', 'transaction_date']),
    ('amount', ['amount', 'value', 'sum']),
    ('transaction_type', ['transaction_type', 'type', 'type_name', 'txn_type']),
    ('category', ['category', 'category_name', 'cat']),
    ('description', ['description', 'title', 'desc', 'details', 'name', 'memo']),
]


class CSVValidationService:
    """
    Service layer providing CSV file validation: file extension, file size,
    UTF-8 encoding, empty file check, row limit validation, and column header analysis.
    """

    @classmethod
    def validate_file(cls, file_obj):
        """
        Validates basic file constraints and reads content into decoded text rows.
        Returns tuple: (is_valid, errors, rows, header_map)
        """
        if not file_obj:
            return False, [{'row': 0, 'field': 'file', 'message': 'No CSV file was uploaded.'}], [], {}

        filename = getattr(file_obj, 'name', 'import.csv')
        if not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
            return False, [{'row': 0, 'field': 'file', 'message': 'Only CSV files (.csv) are accepted.'}], [], {}

        if file_obj.size > MAX_FILE_SIZE_BYTES:
            return False, [{
                'row': 0,
                'field': 'file',
                'message': f"File size exceeds maximum limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
            }], [], {}

        try:
            raw_data = file_obj.read()
            file_obj.seek(0)
            content = raw_data.decode('utf-8-sig')
        except UnicodeDecodeError:
            return False, [{
                'row': 0,
                'field': 'file',
                'message': 'File encoding is invalid. Please upload a UTF-8 encoded CSV file.'
            }], [], {}

        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        if not rows or not any(any(cell.strip() for cell in row) for row in rows):
            return False, [{'row': 0, 'field': 'file', 'message': 'Uploaded CSV file is empty.'}], [], {}

        data_rows = [r for r in rows[1:] if any(cell.strip() for cell in r)]
        if len(data_rows) > MAX_ROW_LIMIT:
            return False, [{
                'row': 0,
                'field': 'file',
                'message': f"CSV file contains {len(data_rows)} rows, exceeding the limit of {MAX_ROW_LIMIT} rows."
            }], [], {}

        # Validate column headers
        header_row = [col.strip().lower().replace(' ', '_') for col in rows[0]]
        header_map = {}
        missing_groups = []

        for group_name, aliases in REQUIRED_HEADER_GROUPS:
            found_idx = None
            for idx, col in enumerate(header_row):
                if col in aliases:
                    found_idx = idx
                    break
            if found_idx is not None:
                header_map[group_name] = found_idx
            else:
                missing_groups.append(group_name)

        if missing_groups:
            return False, [{
                'row': 1,
                'field': 'header',
                'message': f"Missing required CSV column headers: {', '.join(missing_groups)}. "
                           f"Found columns: {', '.join(rows[0])}."
            }], rows, {}

        return True, [], rows, header_map

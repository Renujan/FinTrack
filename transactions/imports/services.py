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


class CSVRowValidationService:
    """
    Service layer providing row-level field parsing and validation
    for transaction date, amount, transaction type, title, and description.
    """

    @classmethod
    def validate_row_fields(cls, line_num, date_raw, amount_raw, type_raw, category_raw, desc_raw, title_raw=""):
        """
        Validates individual raw row values and returns parsed values & error list.
        """
        from decimal import Decimal, InvalidOperation
        import datetime
        from transactions.choices import TransactionType

        row_errors = []

        # Construct final description text
        if title_raw and desc_raw and title_raw.lower() != desc_raw.lower():
            final_description = f"{title_raw} - {desc_raw}"
        elif title_raw:
            final_description = title_raw
        else:
            final_description = desc_raw

        # Required field presence check
        if not date_raw:
            row_errors.append({'row': line_num, 'field': 'date', 'message': 'Date field is required.'})
        if not amount_raw:
            row_errors.append({'row': line_num, 'field': 'amount', 'message': 'Amount field is required.'})
        if not type_raw:
            row_errors.append({'row': line_num, 'field': 'transaction_type', 'message': 'Transaction type field is required.'})
        if not category_raw:
            row_errors.append({'row': line_num, 'field': 'category', 'message': 'Category field is required.'})

        # Date parsing & format validation
        parsed_date = None
        if date_raw:
            try:
                parsed_date = datetime.datetime.strptime(date_raw, '%Y-%m-%d').date()
            except ValueError:
                row_errors.append({'row': line_num, 'field': 'date', 'message': f"Invalid date format '{date_raw}'. Expected YYYY-MM-DD."})

        # Amount parsing & validation
        parsed_amount = None
        if amount_raw:
            try:
                parsed_amount = Decimal(amount_raw)
                if parsed_amount <= Decimal('0.00'):
                    row_errors.append({'row': line_num, 'field': 'amount', 'message': 'Amount must be greater than zero.'})
                    parsed_amount = None
            except (InvalidOperation, TypeError, ValueError):
                row_errors.append({'row': line_num, 'field': 'amount', 'message': f"Invalid numeric format for amount '{amount_raw}'."})

        # Transaction type validation
        parsed_type = None
        if type_raw:
            upper_type = type_raw.upper()
            if upper_type in TransactionType.values:
                parsed_type = upper_type
            else:
                row_errors.append({
                    'row': line_num,
                    'field': 'transaction_type',
                    'message': f"Invalid transaction type '{type_raw}'. Choices: {', '.join(TransactionType.values)}."
                })

        return {
            'parsed_date': parsed_date,
            'parsed_amount': parsed_amount,
            'parsed_type': parsed_type,
            'final_description': final_description,
            'errors': row_errors
        }


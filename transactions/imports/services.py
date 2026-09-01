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


class CategoryMatchingService:
    """
    Service layer providing safe user-isolated category matching (by name or ID),
    unmatched category discovery, and controlled missing category creation.
    """

    @classmethod
    def match_category(cls, user, category_raw, create_if_missing=False, cache=None):
        """
        Attempts to match category_raw against user categories.
        Returns tuple: (category_obj, is_newly_created, error_message)
        """
        from transactions.models import Category

        if not category_raw or not str(category_raw).strip():
            return None, False, 'Category field is required.'

        cat_str = str(category_raw).strip()

        if cache is None:
            user_cats_by_name = {c.name.lower(): c for c in Category.objects.filter(user=user)}
            user_cats_by_id = {str(c.id): c for c in Category.objects.filter(user=user)}
        else:
            user_cats_by_name = cache.get('by_name', {})
            user_cats_by_id = cache.get('by_id', {})

        # Direct ID match
        if cat_str.isdigit() and cat_str in user_cats_by_id:
            return user_cats_by_id[cat_str], False, None

        # Case-insensitive name match
        if cat_str.lower() in user_cats_by_name:
            return user_cats_by_name[cat_str.lower()], False, None

        # Category not found
        if create_if_missing:
            new_cat = Category.objects.create(user=user, name=cat_str[:100])
            if cache is not None:
                cache['by_name'][new_cat.name.lower()] = new_cat
                cache['by_id'][str(new_cat.id)] = new_cat
            return new_cat, True, None

        return None, False, f"Category '{cat_str}' does not exist for this user."


class DuplicateDetectionService:
    """
    Service layer providing intra-file and database transaction duplicate detection
    using field comparisons (date, amount, transaction_type, category, title/description).
    """

    @classmethod
    def generate_row_fingerprint(cls, user_id, parsed_date, parsed_amount, parsed_type, category_identifier, description):
        """
        Generates SHA-256 hash fingerprint for transaction uniqueness comparison.
        """
        import hashlib
        raw_str = f"{user_id}:{parsed_date}:{parsed_amount:.2f}:{parsed_type}:{category_identifier}:{description.strip().lower()}"
        return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

    @classmethod
    def check_duplicate_in_db(cls, user, parsed_date, parsed_amount, parsed_type, category_obj, description):
        """
        Queries database for existing duplicate transaction belonging to user.
        """
        from transactions.models import Transaction
        if not category_obj:
            return False
        return Transaction.objects.filter(
            user=user,
            date=parsed_date,
            amount=parsed_amount,
            transaction_type=parsed_type,
            category=category_obj,
            description=description
        ).exists()


class DataImportService:
    """
    Dedicated service for financial CSV data import management:
    preview generation, row validation, category matching, duplicate protection,
    import execution, and error summary reporting.
    """

    @classmethod
    def create_import_record(cls, user, file_obj, filename):
        """
        Initializes a DataImport model record for the user.
        """
        return DataImport.objects.create(
            user=user,
            file=file_obj,
            file_name=filename[:255],
            status=ImportStatus.PENDING
        )

    @classmethod
    def generate_preview(cls, user, file_obj, create_missing_categories=False):
        """
        Parses uploaded CSV, validates file & rows, checks category matching & duplicates,
        and creates/updates DataImport instance with status PREVIEW_READY.
        Returns structured preview dictionary.
        """
        from transactions.choices import TransactionType
        from transactions.models import Category, Transaction
        from transactions.audit_services import AuditLogService

        filename = getattr(file_obj, 'name', 'import.csv')

        # 1. Create initial DataImport object
        import_obj = cls.create_import_record(user, file_obj, filename)

        # 2. File-level validation
        is_valid_file, file_errors, rows, header_map = CSVValidationService.validate_file(file_obj)
        if not is_valid_file:
            import_obj.status = ImportStatus.FAILED
            import_obj.error_summary = file_errors
            import_obj.total_rows = 0
            import_obj.save(update_fields=['status', 'error_summary', 'total_rows'])
            AuditLogService.log_action(
                user=user,
                action='DATA_IMPORT_FAILED',
                resource_type='DataImport',
                resource_id=str(import_obj.id),
                metadata={'file_name': filename, 'errors': file_errors}
            )
            return {
                'id': import_obj.id,
                'file_name': filename,
                'status': import_obj.status,
                'total_rows': 0,
                'valid_rows': 0,
                'invalid_rows': 0,
                'duplicate_rows': 0,
                'unmatched_categories': [],
                'errors': file_errors,
                'preview_rows': []
            }

        data_rows = rows[1:]
        total_rows = len([r for r in data_rows if any(cell.strip() for cell in r)])

        cats = list(Category.objects.filter(user=user))
        cat_cache = {
            'by_name': {c.name.lower(): c for c in cats},
            'by_id': {str(c.id): c for c in cats}
        }

        errors = []
        preview_rows = []
        intra_hashes = set()
        unmatched_categories_set = set()
        valid_count = 0
        invalid_count = 0
        duplicate_count = 0

        user_txns = set(
            Transaction.objects.filter(user=user).values_list(
                'date', 'amount', 'transaction_type', 'category_id', 'description'
            )
        )

        for line_num, row in enumerate(data_rows, start=2):
            if not row or not any(cell.strip() for cell in row):
                continue

            row_errors = []

            date_raw = row[header_map['date']].strip() if header_map['date'] < len(row) else ''
            amount_raw = row[header_map['amount']].strip() if header_map['amount'] < len(row) else ''
            type_raw = row[header_map['transaction_type']].strip() if header_map['transaction_type'] < len(row) else ''
            category_raw = row[header_map['category']].strip() if header_map['category'] < len(row) else ''
            desc_raw = row[header_map['description']].strip() if header_map['description'] < len(row) else ''

            title_raw = ''
            if 'title' in [col.strip().lower() for col in rows[0]]:
                t_idx = [col.strip().lower() for col in rows[0]].index('title')
                if t_idx < len(row):
                    title_raw = row[t_idx].strip()

            row_eval = CSVRowValidationService.validate_row_fields(
                line_num, date_raw, amount_raw, type_raw, category_raw, desc_raw, title_raw
            )
            row_errors.extend(row_eval['errors'])

            parsed_date = row_eval['parsed_date']
            parsed_amount = row_eval['parsed_amount']
            parsed_type = row_eval['parsed_type']
            final_description = row_eval['final_description']

            # Category matching
            category_obj = None
            if category_raw:
                cat_obj, _, cat_err = CategoryMatchingService.match_category(
                    user=user,
                    category_raw=category_raw,
                    create_if_missing=False,
                    cache=cat_cache
                )
                if cat_err:
                    unmatched_categories_set.add(category_raw)
                    if not create_missing_categories:
                        row_errors.append({'row': line_num, 'field': 'category', 'message': cat_err})
                else:
                    category_obj = cat_obj

            # Duplicate detection
            is_duplicate = False
            if parsed_date and parsed_amount and parsed_type and (category_obj or create_missing_categories):
                cat_id_for_dup = category_obj.id if category_obj else category_raw.lower()
                fingerprint = DuplicateDetectionService.generate_row_fingerprint(
                    user.id, parsed_date, parsed_amount, parsed_type, cat_id_for_dup, final_description
                )

                if fingerprint in intra_hashes:
                    is_duplicate = True
                    row_errors.append({'row': line_num, 'field': 'duplicate', 'message': 'Duplicate row found within CSV file.'})
                else:
                    intra_hashes.add(fingerprint)

                if category_obj and (parsed_date, parsed_amount, parsed_type, category_obj.id, final_description) in user_txns:
                    is_duplicate = True
                    row_errors.append({'row': line_num, 'field': 'duplicate', 'message': 'Duplicate transaction already exists in database.'})

            if is_duplicate:
                duplicate_count += 1

            is_row_valid = len(row_errors) == 0

            if is_row_valid:
                valid_count += 1
            else:
                invalid_count += 1
                errors.extend(row_errors)

            if len(preview_rows) < 100:
                preview_rows.append({
                    'row': line_num,
                    'title': title_raw or final_description,
                    'description': final_description,
                    'amount': str(parsed_amount) if parsed_amount else amount_raw,
                    'transaction_type': parsed_type or type_raw,
                    'category': category_obj.name if category_obj else category_raw,
                    'date': str(parsed_date) if parsed_date else date_raw,
                    'is_valid': is_row_valid,
                    'is_duplicate': is_duplicate,
                    'errors': [e['message'] for e in row_errors]
                })

        capped_errors = errors[:100]

        import_obj.status = ImportStatus.PREVIEW_READY
        import_obj.total_rows = total_rows
        import_obj.failed_rows = invalid_count
        import_obj.duplicate_rows = duplicate_count
        import_obj.error_summary = capped_errors
        import_obj.preview_data = {
            'valid_rows_count': valid_count,
            'invalid_rows_count': invalid_count,
            'duplicate_rows_count': duplicate_count,
            'unmatched_categories': sorted(list(unmatched_categories_set)),
            'preview_rows': preview_rows
        }
        import_obj.save(update_fields=['status', 'total_rows', 'failed_rows', 'duplicate_rows', 'error_summary', 'preview_data'])

        AuditLogService.log_action(
            user=user,
            action='DATA_IMPORT_PREVIEWED',
            resource_type='DataImport',
            resource_id=str(import_obj.id),
            metadata={
                'file_name': filename,
                'total_rows': total_rows,
                'valid_rows': valid_count,
                'invalid_rows': invalid_count,
                'duplicate_rows': duplicate_count
            }
        )

        return {
            'id': import_obj.id,
            'file_name': filename,
            'status': import_obj.status,
            'total_rows': total_rows,
            'valid_rows': valid_count,
            'invalid_rows': invalid_count,
            'duplicate_rows': duplicate_count,
            'unmatched_categories': sorted(list(unmatched_categories_set)),
            'errors': capped_errors,
            'preview_rows': preview_rows
        }





import pdfplumber
import re
from datetime import datetime
from decimal import Decimal

def parse_pdf_statement(filepath):
    """
    Parse a PDF bank statement and extract transactions.

    Returns a list of dictionaries with transaction details:
    [{'date': 'YYYY-MM-DD', 'description': 'text', 'amount': float, 'type': 'debit/credit'}]
    """
    transactions = []

    print(f"DEBUG: Opening PDF: {filepath}")

    with pdfplumber.open(filepath) as pdf:
        print(f"DEBUG: PDF has {len(pdf.pages)} pages")

        for page_num, page in enumerate(pdf.pages):
            print(f"DEBUG: Processing page {page_num + 1}")

            # First, try to extract tables (more reliable for structured data)
            tables = page.extract_tables()

            if tables:
                print(f"DEBUG: Found {len(tables)} tables on page {page_num + 1}")
                for table_num, table in enumerate(tables):
                    print(f"DEBUG: Table {table_num + 1} has {len(table)} rows")
                    table_transactions = parse_table(table)
                    transactions.extend(table_transactions)
                    print(f"DEBUG: Extracted {len(table_transactions)} transactions from table {table_num + 1}")

            # If no tables or tables didn't yield transactions, try text parsing
            if not tables or len(transactions) == 0:
                print(f"DEBUG: No tables found or no transactions from tables, trying text parsing")
                text = page.extract_text()

                if text:
                    lines = text.split('\n')
                    print(f"DEBUG: Found {len(lines)} lines of text")

                    for line in lines:
                        transaction = parse_transaction_line(line)
                        if transaction:
                            transactions.append(transaction)

    print(f"DEBUG: Total transactions found in PDF: {len(transactions)}")
    return transactions

def parse_table(table):
    """
    Parse a table extracted from PDF.
    Returns list of transactions.
    """
    if not table or len(table) < 2:  # Need at least header + 1 row
        return []

    transactions = []

    # Try to identify columns
    header = table[0]
    if not header:
        # No header, try to infer from first data row
        header = ['col' + str(i) for i in range(len(table[0]) if table[0] else 0)]

    # Normalize header
    header = [str(h).lower().strip() if h else f'col{i}' for i, h in enumerate(header)]
    print(f"DEBUG: Table header: {header}")

    # Find relevant columns
    date_idx = None
    desc_idx = None
    amount_idx = None
    withdrawal_idx = None
    deposit_idx = None

    for i, col in enumerate(header):
        if any(keyword in col for keyword in ['date', 'posted', 'trans']):
            date_idx = i
        elif any(keyword in col for keyword in ['description', 'memo', 'detail', 'merchant', 'payee']):
            desc_idx = i
        elif any(keyword in col for keyword in ['withdrawal', 'debit', 'payment']):
            withdrawal_idx = i
        elif any(keyword in col for keyword in ['deposit', 'credit']):
            deposit_idx = i
        elif any(keyword in col for keyword in ['amount']):
            amount_idx = i

    print(f"DEBUG: Column indices - date: {date_idx}, desc: {desc_idx}, amount: {amount_idx}, withdrawal: {withdrawal_idx}, deposit: {deposit_idx}")

    # If we can't find columns by header, try to infer from data
    if date_idx is None or desc_idx is None or amount_idx is None:
        print("DEBUG: Attempting to infer columns from data patterns")
        # Look at first few data rows to identify patterns
        for row in table[1:min(5, len(table))]:
            if not row:
                continue
            for i, cell in enumerate(row):
                if not cell:
                    continue
                cell_str = str(cell).strip()
                # Check if looks like a date
                if date_idx is None and re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', cell_str):
                    date_idx = i
                    print(f"DEBUG: Inferred date column at index {i}")
                # Check if looks like an amount
                if amount_idx is None and re.match(r'[-]?\$?[\d,]+\.\d{2}', cell_str):
                    amount_idx = i
                    print(f"DEBUG: Inferred amount column at index {i}")

    # Parse rows
    for row_num, row in enumerate(table[1:], start=1):  # Skip header
        if not row or len(row) == 0:
            continue

        try:
            # Extract values
            date_val = row[date_idx] if date_idx is not None and date_idx < len(row) else None
            desc_val = row[desc_idx] if desc_idx is not None and desc_idx < len(row) else None

            if not date_val:
                continue

            # Parse date first
            date_str = str(date_val).strip()
            try:
                normalized_date = normalize_date(date_str)
            except:
                continue

            # Get description
            description = str(desc_val).strip() if desc_val else ''

            # If desc_idx not found, try to concatenate middle columns
            if not description or len(description) < 3:
                if date_idx is not None:
                    desc_parts = []
                    for i in range(len(row)):
                        if i != date_idx and i != amount_idx and i != withdrawal_idx and i != deposit_idx and row[i]:
                            desc_parts.append(str(row[i]))
                    description = ' '.join(desc_parts)

            # Skip if description is still too short
            if len(description) < 3:
                continue

            # Handle withdrawal/deposit columns (Truist Bank format)
            if withdrawal_idx is not None or deposit_idx is not None:
                # Check withdrawal column
                if withdrawal_idx is not None and withdrawal_idx < len(row):
                    withdrawal_val = row[withdrawal_idx]
                    if withdrawal_val and str(withdrawal_val).strip():
                        amount = parse_amount(str(withdrawal_val))
                        if amount and amount != 0:
                            transactions.append({
                                'date': normalized_date,
                                'description': description,
                                'amount': abs(amount),
                                'type': 'debit'
                            })

                # Check deposit column
                if deposit_idx is not None and deposit_idx < len(row):
                    deposit_val = row[deposit_idx]
                    if deposit_val and str(deposit_val).strip():
                        amount = parse_amount(str(deposit_val))
                        if amount and amount != 0:
                            transactions.append({
                                'date': normalized_date,
                                'description': description,
                                'amount': abs(amount),
                                'type': 'credit'
                            })

            # Otherwise use single amount column
            elif amount_idx is not None:
                amount_val = row[amount_idx] if amount_idx < len(row) else None
                if not amount_val:
                    continue

                amount_str = str(amount_val).strip()
                amount = parse_amount(amount_str)
                if amount is None or amount == 0:
                    continue

                # Determine transaction type
                transaction_type = 'debit' if amount < 0 else 'credit'

                transactions.append({
                    'date': normalized_date,
                    'description': description,
                    'amount': abs(amount),
                    'type': transaction_type
                })

        except Exception as e:
            print(f"DEBUG: Error parsing table row {row_num}: {str(e)}")
            continue

    return transactions

def parse_transaction_line(line):
    """
    Parse a single line of text to extract transaction information.
    Supports multiple common bank statement formats.
    """
    # Common patterns for bank statements:
    # Pattern 1: MM/DD/YYYY Description Amount
    # Pattern 2: YYYY-MM-DD Description Amount
    # Pattern 3: DD/MM/YYYY Description Amount

    # Remove extra whitespace
    line = ' '.join(line.split())

    # Pattern to match: date, description, and amount
    # Looking for amounts like: $1,234.56 or 1234.56 or -1234.56
    amount_pattern = r'[-]?\$?[\d,]+\.\d{2}'

    # Date patterns
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY or DD/MM/YYYY
        r'\d{4}-\d{2}-\d{2}',         # YYYY-MM-DD
        r'\d{2}-\d{2}-\d{4}',         # DD-MM-YYYY
    ]

    for date_pattern in date_patterns:
        # Try to find date and amount in the line
        date_match = re.search(date_pattern, line)
        amount_match = re.search(amount_pattern, line)

        if date_match and amount_match:
            date_str = date_match.group()
            amount_str = amount_match.group()

            # Extract description (text between date and amount)
            date_end = date_match.end()
            amount_start = amount_match.start()
            description = line[date_end:amount_start].strip()

            # Skip if description is empty or too short
            if len(description) < 3:
                continue

            # Parse amount
            amount = parse_amount(amount_str)

            # Skip if amount is 0 or invalid
            if amount is None or amount == 0:
                continue

            # Normalize date
            try:
                normalized_date = normalize_date(date_str)
            except:
                continue

            # Determine transaction type (debit if negative or if it's an expense)
            transaction_type = 'debit' if amount < 0 else 'credit'

            return {
                'date': normalized_date,
                'description': description,
                'amount': abs(amount),  # Store as positive, use type to indicate direction
                'type': transaction_type
            }

    return None

def parse_amount(amount_str):
    """Parse amount string to float"""
    try:
        # Remove $ and commas
        amount_str = amount_str.replace('$', '').replace(',', '')
        return float(amount_str)
    except:
        return None

def normalize_date(date_str):
    """Convert various date formats to YYYY-MM-DD"""
    date_formats = [
        '%m/%d/%Y', '%m/%d/%y',
        '%d/%m/%Y', '%d/%m/%y',
        '%Y-%m-%d', '%d-%m-%Y'
    ]

    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except:
            continue

    # If no format matches, return as-is
    return date_str

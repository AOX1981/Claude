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
    Supports multiple common bank statement formats including Truist.
    """
    # Remove extra whitespace
    line = ' '.join(line.split())

    # Skip lines that are too short or look like headers
    if len(line) < 10:
        return None

    # Skip common header/footer lines
    skip_patterns = [
        'page', 'account', 'balance', 'statement', 'total', 'subtotal',
        'beginning', 'ending', 'deposit', 'withdrawal', 'date', 'description',
        'checks', 'debits', 'credits', 'interest'
    ]
    line_lower = line.lower()
    if any(skip in line_lower for skip in skip_patterns):
        return None

    # Pattern to match amounts - including negative and with various formats
    # Truist often uses formats like: 1,234.56 or -1,234.56
    amount_patterns = [
        r'[-]?\$?\d{1,3}(?:,\d{3})*\.\d{2}',  # 1,234.56 or -1,234.56
        r'[-]?\d+\.\d{2}',                     # 123.56 or -123.56
    ]

    # Date patterns - Truist typically uses MM/DD format
    date_patterns = [
        r'\d{1,2}/\d{1,2}(?:/\d{2,4})?',  # MM/DD or MM/DD/YY or MM/DD/YYYY
        r'\d{2}-\d{2}',                     # MM-DD
    ]

    # Try to find date and amounts in the line
    date_match = None
    for date_pattern in date_patterns:
        date_match = re.search(date_pattern, line)
        if date_match:
            break

    if not date_match:
        return None

    # Find all amounts in the line (there might be multiple)
    amounts = []
    for amount_pattern in amount_patterns:
        amounts.extend(re.finditer(amount_pattern, line))

    if not amounts:
        return None

    # Use the last amount in the line (typically the transaction amount)
    # In Truist statements, the format is often: Date Description CheckNumber Amount
    amount_match = amounts[-1]

    date_str = date_match.group()
    amount_str = amount_match.group()

    # Extract description (text between date and amount)
    date_end = date_match.end()
    amount_start = amount_match.start()

    # Get the full description area
    description_area = line[date_end:amount_start].strip()

    # Remove any digits that are part of the amount (commas in thousands)
    # The amount regex might not capture the full number if there are spaces
    # Remove trailing numbers that are likely part of the amount
    description = re.sub(r'[\d,]+\s*$', '', description_area).strip()

    # Also clean up check numbers that come after description (usually smaller numbers)
    # But keep the description text
    description = re.sub(r'\s+\d{1,6}\s*$', '', description).strip()

    # Skip if description is empty or too short
    if len(description) < 3:
        return None

    # Parse amount
    amount = parse_amount(amount_str)

    # Skip if amount is 0 or invalid
    if amount is None or amount == 0:
        return None

    # Normalize date - add current year if not present
    try:
        if '/' in date_str and date_str.count('/') == 1:
            # MM/DD format - add year
            from datetime import datetime
            current_year = datetime.now().year
            date_str = f"{date_str}/{current_year}"
        normalized_date = normalize_date(date_str)
    except:
        return None

    # Determine transaction type
    # Look for deposit keywords in description
    deposit_keywords = ['deposit', 'direct dep', 'credit', 'payroll', 'transfer from', 'payment received']
    is_deposit = any(keyword in description.lower() for keyword in deposit_keywords)

    # If amount is negative, it's definitely a debit
    # If positive and looks like a deposit, it's credit
    # Otherwise, default to debit (most transactions are expenses)
    if amount < 0:
        transaction_type = 'debit'
    elif is_deposit:
        transaction_type = 'credit'
    else:
        # For Truist, check if there are two amounts on the line
        # Format is often: Date Description Debit Credit
        # If this is the second amount, it's likely a credit
        if len(amounts) >= 2 and amount_match == amounts[-1]:
            # This might be the credit column
            # Check if previous amount exists and is larger (indicating this might be credit)
            prev_amount_str = amounts[-2].group()
            prev_amount = parse_amount(prev_amount_str)
            if prev_amount and prev_amount == 0:
                # Previous column was empty/zero, this is likely a debit
                transaction_type = 'debit'
            else:
                # Could be either, default to debit for safety
                transaction_type = 'debit'
        else:
            transaction_type = 'debit'

    return {
        'date': normalized_date,
        'description': description,
        'amount': abs(amount),
        'type': transaction_type
    }

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

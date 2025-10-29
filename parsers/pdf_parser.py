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

    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            if text:
                # Parse transactions from text
                # This is a generic parser that looks for common patterns
                lines = text.split('\n')

                for line in lines:
                    transaction = parse_transaction_line(line)
                    if transaction:
                        transactions.append(transaction)

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

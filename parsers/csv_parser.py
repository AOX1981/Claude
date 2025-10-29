import pandas as pd
from datetime import datetime
import re

def parse_csv_statement(filepath):
    """
    Parse a CSV bank statement and extract transactions.

    Returns a list of dictionaries with transaction details:
    [{'date': 'YYYY-MM-DD', 'description': 'text', 'amount': float, 'type': 'debit/credit'}]
    """
    try:
        # Try reading CSV with different encodings
        try:
            df = pd.read_csv(filepath)
        except UnicodeDecodeError:
            df = pd.read_csv(filepath, encoding='latin-1')

        # Log columns for debugging
        print(f"DEBUG: CSV columns: {list(df.columns)}")
        print(f"DEBUG: CSV shape: {df.shape}")

        # Normalize column names (lowercase and strip whitespace)
        df.columns = df.columns.str.lower().str.strip()

        # Identify relevant columns
        date_col = identify_column(df, ['date', 'transaction date', 'posting date', 'trans date', 'posted'])
        desc_col = identify_column(df, ['description', 'memo', 'details', 'transaction', 'payee', 'merchant'])
        amount_col = identify_column(df, ['amount', 'transaction amount'])

        print(f"DEBUG: Found columns - date: {date_col}, desc: {desc_col}, amount: {amount_col}")

        if not date_col or not desc_col:
            raise ValueError(f'Could not identify required columns. Found columns: {list(df.columns)}')

        # Try to find amount column - could be single amount or debit/credit
        if not amount_col:
            # Try alternative approach: check if there's a debit and credit column
            debit_col = identify_column(df, ['debit', 'withdrawal', 'debits', 'withdrawals'])
            credit_col = identify_column(df, ['credit', 'deposit', 'credits', 'deposits'])

            print(f"DEBUG: Trying debit/credit format - debit: {debit_col}, credit: {credit_col}")

            if debit_col and credit_col:
                return parse_debit_credit_format(df, date_col, desc_col, debit_col, credit_col)
            else:
                raise ValueError(f'Could not identify amount column. Found columns: {list(df.columns)}')

        transactions = []

        for idx, row in df.iterrows():
            try:
                date = normalize_date(str(row[date_col]))
                description = str(row[desc_col]).strip()
                amount = parse_amount(row[amount_col])

                # Skip invalid rows but log them
                if pd.isna(amount) or amount == 0:
                    print(f"DEBUG: Skipping row {idx} - invalid amount: {row[amount_col]}")
                    continue

                if len(description) < 3 or description == 'nan':
                    print(f"DEBUG: Skipping row {idx} - invalid description: {description}")
                    continue

                # Determine transaction type
                transaction_type = 'debit' if amount < 0 else 'credit'

                transactions.append({
                    'date': date,
                    'description': description,
                    'amount': abs(amount),
                    'type': transaction_type
                })
            except Exception as e:
                print(f"DEBUG: Error parsing row {idx}: {str(e)}")
                continue

        print(f"DEBUG: Found {len(transactions)} total transactions")
        return transactions

    except Exception as e:
        print(f"DEBUG: Fatal error in parse_csv_statement: {str(e)}")
        raise Exception(f'Error parsing CSV: {str(e)}')

def parse_debit_credit_format(df, date_col, desc_col, debit_col, credit_col):
    """Parse CSV where debits and credits are in separate columns"""
    transactions = []

    for _, row in df.iterrows():
        try:
            date = normalize_date(str(row[date_col]))
            description = str(row[desc_col]).strip()

            # Check debit column
            debit = parse_amount(row[debit_col])
            credit = parse_amount(row[credit_col])

            if debit and not pd.isna(debit) and debit != 0:
                transactions.append({
                    'date': date,
                    'description': description,
                    'amount': abs(debit),
                    'type': 'debit'
                })

            if credit and not pd.isna(credit) and credit != 0:
                transactions.append({
                    'date': date,
                    'description': description,
                    'amount': abs(credit),
                    'type': 'credit'
                })

        except Exception as e:
            continue

    return transactions

def identify_column(df, possible_names):
    """Identify column by checking possible names"""
    for col in df.columns:
        for name in possible_names:
            if name in col.lower():
                return col
    return None

def parse_amount(amount):
    """Parse amount to float"""
    if pd.isna(amount):
        return None

    # Convert to string and clean
    amount_str = str(amount).replace('$', '').replace(',', '').strip()

    # Handle parentheses as negative (common in accounting)
    if '(' in amount_str:
        amount_str = '-' + amount_str.replace('(', '').replace(')', '')

    try:
        return float(amount_str)
    except:
        return None

def normalize_date(date_str):
    """Convert various date formats to YYYY-MM-DD"""
    date_formats = [
        '%m/%d/%Y', '%m/%d/%y',
        '%d/%m/%Y', '%d/%m/%y',
        '%Y-%m-%d', '%d-%m-%Y',
        '%m-%d-%Y', '%m-%d-%y',
        '%Y/%m/%d', '%d.%m.%Y'
    ]

    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except:
            continue

    # If no format matches, return as-is
    return date_str

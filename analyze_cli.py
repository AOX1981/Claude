#!/usr/bin/env python3
"""
Command-line interface for Financial Spending Analyzer
"""

import sys
import os
from parsers.pdf_parser import parse_pdf_statement
from parsers.csv_parser import parse_csv_statement
from analyzer.categorizer import categorize_transactions, calculate_totals

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_cli.py <path-to-csv-or-pdf>")
        print("\nExample: python analyze_cli.py sample_statement.csv")
        sys.exit(1)

    filepath = sys.argv[1]

    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found")
        sys.exit(1)

    print("\n" + "="*60)
    print("Financial Spending Analyzer")
    print("="*60)
    print(f"\nAnalyzing: {filepath}\n")

    # Parse the file
    file_ext = filepath.rsplit('.', 1)[1].lower()

    try:
        if file_ext == 'pdf':
            print("Parsing PDF...")
            transactions = parse_pdf_statement(filepath)
        elif file_ext == 'csv':
            print("Parsing CSV...")
            transactions = parse_csv_statement(filepath)
        else:
            print(f"Error: Unsupported file type '.{file_ext}'")
            print("Supported formats: .pdf, .csv")
            sys.exit(1)

        print(f"Found {len(transactions)} transactions\n")

        # Categorize transactions
        print("Categorizing transactions...")
        categorized = categorize_transactions(transactions)

        # Calculate totals
        totals = calculate_totals(categorized)

        # Display results
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total Expenses:        ${totals['total_expenses']:>10,.2f}")
        print(f"Frivolous Spending:    ${totals['frivolous_total']:>10,.2f}  ({totals['frivolous_percentage']:.1f}%)")
        print(f"Necessary Expenses:    ${totals['necessary_total']:>10,.2f}")
        print(f"Total Transactions:    {totals['transaction_count']:>10}")

        # Frivolous breakdown
        print("\n" + "="*60)
        print("FRIVOLOUS SPENDING BY CATEGORY")
        print("="*60)
        if totals['frivolous_by_category']:
            sorted_frivolous = sorted(totals['frivolous_by_category'].items(),
                                     key=lambda x: x[1], reverse=True)
            for category, amount in sorted_frivolous:
                print(f"{category.replace('_', ' ').title():<30} ${amount:>10,.2f}")
        else:
            print("No frivolous expenses found!")

        # Necessary breakdown
        print("\n" + "="*60)
        print("NECESSARY EXPENSES BY CATEGORY")
        print("="*60)
        if totals['necessary_by_category']:
            sorted_necessary = sorted(totals['necessary_by_category'].items(),
                                     key=lambda x: x[1], reverse=True)
            for category, amount in sorted_necessary:
                print(f"{category.replace('_', ' ').title():<30} ${amount:>10,.2f}")
        else:
            print("No necessary expenses found!")

        # Detailed frivolous transactions
        print("\n" + "="*60)
        print(f"FRIVOLOUS EXPENSES DETAIL ({len(categorized['frivolous'])} transactions)")
        print("="*60)
        if categorized['frivolous']:
            # Sort by amount (highest first)
            sorted_frivolous = sorted(categorized['frivolous'],
                                     key=lambda x: x['amount'], reverse=True)
            print(f"{'Date':<12} {'Description':<40} {'Category':<20} {'Amount':>10}")
            print("-"*60)
            for trans in sorted_frivolous:
                desc = trans['description'][:38] + ".." if len(trans['description']) > 40 else trans['description']
                cat = trans['category'].replace('_', ' ')[:18] + ".." if len(trans['category']) > 20 else trans['category'].replace('_', ' ')
                print(f"{trans['date']:<12} {desc:<40} {cat:<20} ${trans['amount']:>9.2f}")
        else:
            print("Great job! No frivolous expenses detected.")

        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print(f"\n💡 You could save ${totals['frivolous_total']:,.2f} by eliminating frivolous spending!\n")

    except Exception as e:
        print(f"\nError processing file: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

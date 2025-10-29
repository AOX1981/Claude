# Financial Spending Analyzer

A web-based application that analyzes your monthly bank statements to identify frivolous spending and help you make informed financial decisions.

## Features

- Upload bank statements in PDF or CSV format
- Automatic transaction parsing and categorization
- Identifies frivolous vs. necessary expenses
- Visual breakdown of spending by category
- Detailed transaction list with categorization
- Summary statistics showing total expenses and frivolous spending percentage

## How It Works

The application uses keyword-based categorization to classify transactions:

### Necessary Expenses
- **Groceries**: Supermarkets, food markets
- **Utilities**: Electric, water, gas, internet, phone
- **Housing**: Rent, mortgage, HOA fees
- **Healthcare**: Pharmacy, medical, dental, insurance
- **Transportation**: Gas, public transit, car payments, insurance
- **Education**: Tuition, textbooks, student loans

### Frivolous Expenses
- **Dining Out**: Restaurants, coffee shops, food delivery
- **Entertainment**: Streaming services, movies, concerts, gaming
- **Shopping**: Online shopping, clothing, electronics
- **Luxury**: Spa, salon, fine dining
- **Subscriptions**: Gym memberships, recurring services
- **Impulse Purchases**: Convenience stores, snacks

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd Claude
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. **Upload Your Bank Statement**
   - Click the upload area or drag and drop your file
   - Supported formats: PDF and CSV
   - Maximum file size: 16MB

2. **Click "Analyze Spending"**
   - The app will parse your statement
   - Transactions will be categorized automatically

3. **Review Results**
   - View total expenses and frivolous spending percentage
   - Examine category breakdowns
   - Review individual transactions

4. **Make Informed Decisions**
   - Identify areas where you can cut back
   - Set goals for the next month
   - Track your progress over time

## Supported File Formats

### CSV Format

The app can parse CSV files with various column layouts. It automatically detects columns for:
- Date (Transaction Date, Posting Date, Date)
- Description (Description, Memo, Details, Transaction)
- Amount (Amount, Transaction Amount, Debit, Credit)

Example CSV format:
```csv
Date,Description,Amount
01/15/2024,Starbucks Coffee,-5.75
01/16/2024,Grocery Store,-85.32
01/17/2024,Netflix Subscription,-15.99
```

### PDF Format

The app can parse PDF bank statements that contain transaction tables. It looks for:
- Date in various formats (MM/DD/YYYY, YYYY-MM-DD, DD/MM/YYYY)
- Transaction descriptions
- Dollar amounts

## Customization

### Adding Custom Categories

To customize the categorization logic, edit `analyzer/categorizer.py`:

1. Add keywords to existing categories:
```python
NECESSARY_CATEGORIES = {
    'groceries': [
        'grocery', 'supermarket', 'your-store-name'
    ]
}
```

2. Create new categories:
```python
FRIVOLOUS_CATEGORIES = {
    'new_category': [
        'keyword1', 'keyword2'
    ]
}
```

## Project Structure

```
Claude/
├── app.py                      # Flask application
├── requirements.txt            # Python dependencies
├── .gitignore                 # Git ignore file
├── README.md                  # This file
├── parsers/                   # File parsing modules
│   ├── __init__.py
│   ├── pdf_parser.py          # PDF statement parser
│   └── csv_parser.py          # CSV statement parser
├── analyzer/                  # Transaction analysis
│   ├── __init__.py
│   └── categorizer.py         # Categorization logic
├── templates/                 # HTML templates
│   └── index.html             # Main UI
└── uploads/                   # Temporary file storage (auto-created)
```

## API Endpoints

### GET `/`
Returns the main application interface.

### POST `/upload`
Uploads and analyzes a bank statement.

**Request:**
- Content-Type: multipart/form-data
- Body: file (PDF or CSV)

**Response:**
```json
{
  "success": true,
  "frivolous_expenses": [...],
  "necessary_expenses": [...],
  "totals": {
    "total_expenses": 1234.56,
    "frivolous_total": 456.78,
    "necessary_total": 777.78,
    "frivolous_percentage": 36.98,
    "frivolous_by_category": {...},
    "necessary_by_category": {...}
  }
}
```

### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## Security Notes

- Uploaded files are deleted immediately after processing
- No data is stored permanently
- All processing happens locally on your machine
- No data is sent to external services

## Troubleshooting

### File Upload Fails
- Check file size (must be under 16MB)
- Ensure file is in PDF or CSV format
- Try converting PDF to CSV if parsing fails

### Transactions Not Categorized Correctly
- Edit `analyzer/categorizer.py` to add your specific merchants
- Unclassified transactions are marked as frivolous by default
- You can adjust the categorization logic to fit your needs

### PDF Parsing Issues
- Some PDF formats may not be supported
- Try exporting your statement as CSV from your bank's website
- Ensure the PDF contains text (not just scanned images)

## Future Enhancements

- Machine learning-based categorization
- Multi-month analysis and trends
- Budget tracking and alerts
- Export analysis results
- User accounts and data persistence
- Mobile app version

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Privacy

This application processes all data locally. No bank statements or transaction data is transmitted to external servers or stored permanently.

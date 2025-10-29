from flask import Flask, request, render_template, jsonify
import os
import sys
from werkzeug.utils import secure_filename

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.pdf_parser import parse_pdf_statement
from parsers.csv_parser import parse_csv_statement
from analyzer.categorizer import categorize_transactions, calculate_totals

app = Flask(__name__, template_folder='../templates')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'csv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload PDF or CSV'}), 400

    try:
        # Read file content directly without saving to disk
        file_content = file.read()
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()

        # Create temporary file in /tmp (Vercel serverless allows /tmp)
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as temp_file:
            temp_file.write(file_content)
            temp_filepath = temp_file.name

        # Parse the file based on extension
        if file_ext == 'pdf':
            transactions = parse_pdf_statement(temp_filepath)
        elif file_ext == 'csv':
            transactions = parse_csv_statement(temp_filepath)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400

        # Clean up temp file
        os.unlink(temp_filepath)

        # Categorize transactions
        categorized = categorize_transactions(transactions)

        # Calculate totals
        totals = calculate_totals(categorized)

        return jsonify({
            'success': True,
            'frivolous_expenses': categorized['frivolous'],
            'necessary_expenses': categorized['necessary'],
            'totals': totals
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

# For Vercel
app = app

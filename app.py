from flask import Flask, request, render_template, jsonify
import os
from werkzeug.utils import secure_filename
from parsers.pdf_parser import parse_pdf_statement
from parsers.csv_parser import parse_csv_statement
from analyzer.categorizer import categorize_transactions, calculate_totals

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'csv'}

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Parse the file based on extension
        file_ext = filename.rsplit('.', 1)[1].lower()

        if file_ext == 'pdf':
            transactions = parse_pdf_statement(filepath)
        elif file_ext == 'csv':
            transactions = parse_csv_statement(filepath)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400

        # Categorize transactions
        categorized = categorize_transactions(transactions)

        # Calculate totals
        totals = calculate_totals(categorized)

        # Clean up uploaded file
        os.remove(filepath)

        return jsonify({
            'success': True,
            'frivolous_expenses': categorized['frivolous'],
            'necessary_expenses': categorized['necessary'],
            'totals': totals
        })

    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

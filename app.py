from flask import Flask, render_template, request, jsonify, send_file
import os
from werkzeug.utils import secure_filename
import PyPDF2
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def merge_pdfs(file_paths, output_path):
    """Merge multiple PDF files into one"""
    pdf_merger = PyPDF2.PdfMerger()
    
    for file_path in file_paths:
        pdf_merger.append(file_path)
    
    with open(output_path, 'wb') as output_file:
        pdf_merger.write(output_file)
    
    pdf_merger.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/merge-pdf')
def merge_pdf_page():
    return render_template('merge_pdf.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads"""
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files selected'}), 400
    
    files = request.files.getlist('files[]')
    saved_files = []
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            saved_files.append({
                'name': filename,
                'path': file_path,
                'size': os.path.getsize(file_path)
            })
    
    return jsonify({'files': saved_files})

@app.route('/merge', methods=['POST'])
def merge_files():
    """Merge uploaded PDF files"""
    data = request.get_json()
    file_paths = data.get('file_paths', [])
    
    if len(file_paths) < 2:
        return jsonify({'error': 'At least 2 files required'}), 400
    
    try:
        output_filename = 'merged_document.pdf'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        merge_pdfs(file_paths, output_path)
        
        return jsonify({
            'success': True,
            'download_url': f'/download/{output_filename}',
            'message': 'PDFs merged successfully!'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error merging PDFs: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download the merged PDF file"""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    """Clean up uploaded files"""
    try:
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        return jsonify({'success': True, 'message': 'Files cleaned up'})
    except Exception as e:
        return jsonify({'error': f'Cleanup failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
import os
import json

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def extract_outline(pdf_path):
    doc = fitz.open(pdf_path)
    outline = []
    font_sizes = {}
    
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = ""
                    for span in line["spans"]:
                        size = span["size"]
                        text = span["text"].strip()
                        if not text: continue
                        line_text += text + " "
                        font_sizes[size] = font_sizes.get(size, 0) + 1
                    if line_text:
                        outline.append((line_text.strip(), size, page_num + 1))

    sorted_sizes = sorted(font_sizes.items(), key=lambda x: -x[0])
    size_map = {}
    if len(sorted_sizes) >= 3:
        size_map = {
            sorted_sizes[0][0]: "H1",
            sorted_sizes[1][0]: "H2",
            sorted_sizes[2][0]: "H3"
        }

    result = {
        "title": outline[0][0] if outline else "Untitled Document",
        "outline": []
    }
    for text, size, page in outline:
        if size in size_map:
            result["outline"].append({
                "level": size_map[size],
                "text": text,
                "page": page
            })

    return result
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')
@app.route('/extract-outline', methods=['POST'])
def upload_file():
    if 'pdf' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['pdf']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    result = extract_outline(filepath)
    return jsonify(result)

@app.route('/uploads/<filename>')
def serve_pdf(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)

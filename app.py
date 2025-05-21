from flask import Flask, request, jsonify, render_template_string
from PIL import Image
import os
import io
import base64

app = Flask(__name__)

# Template HTML inline (pour éviter les problèmes de templates)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>HMB Tech - Image to SVG</title>
    <style>
        body {
            background-color: #0D1C40;
            color: gold;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        .upload-zone {
            border: 2px dashed gold;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
            border-radius: 8px;
            cursor: pointer;
        }
        .preview {
            max-width: 100%;
            margin: 20px 0;
            display: none;
        }
        .preview img, .preview svg {
            max-width: 100%;
            height: auto;
        }
        button {
            background: gold;
            color: #0D1C40;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            width: 100%;
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>HMB Tech - Convertisseur Image vers SVG</h1>
        
        <div class="upload-zone" onclick="document.getElementById('fileInput').click()">
            <input type="file" id="fileInput" style="display:none" accept=".png,.jpg,.jpeg">
            <p>Cliquez ou glissez une image ici</p>
        </div>

        <div id="preview" class="preview">
            <h3>Image originale:</h3>
            <img id="imagePreview">
        </div>

        <div id="svgPreview" class="preview">
            <h3>SVG généré:</h3>
            <div id="svgContainer"></div>
            <button onclick="downloadSVG()">Télécharger SVG</button>
            <button onclick="toggleCode()">Voir le code SVG</button>
        </div>

        <pre id="svgCode" style="display:none; background: rgba(255,255,255,0.1); padding: 10px; color: gold;"></pre>
    </div>

    <script>
        let currentSVG = '';

        document.getElementById('fileInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('imagePreview').src = e.target.result;
                document.getElementById('preview').style.display = 'block';
                uploadImage(file);
            }
            reader.readAsDataURL(file);
        });

        async function uploadImage(file) {
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                
                if (data.error) {
                    alert(data.error);
                    return;
                }

                currentSVG = data.svg;
                document.getElementById('svgContainer').innerHTML = currentSVG;
                document.getElementById('svgPreview').style.display = 'block';
                
            } catch (error) {
                alert('Erreur lors du traitement de l\'image');
            }
        }

        function downloadSVG() {
            if (!currentSVG) return;
            
            const blob = new Blob([currentSVG], {type: 'image/svg+xml'});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'hmb-tech.svg';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }

        function toggleCode() {
            const codeElement = document.getElementById('svgCode');
            if (codeElement.style.display === 'none') {
                codeElement.textContent = currentSVG;
                codeElement.style.display = 'block';
            } else {
                codeElement.style.display = 'none';
            }
        }
    </script>
</body>
</html>
'''

# Configuration simplifiée
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def simple_image_to_svg(image_path):
    """Version simplifiée de la conversion en SVG"""
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            max_size = 800
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.LANCZOS)

            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            width, height = img.size
            
            svg = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
            <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
                <image width="{width}" height="{height}" 
                       href="data:image/png;base64,{img_base64}"/>
            </svg>'''
            
            return svg
            
    except Exception as e:
        raise Exception(f"Erreur lors de la conversion: {str(e)}")

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Aucun fichier envoyé"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Aucun fichier sélectionné"}), 400
            
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return jsonify({"error": "Type de fichier non autorisé"}), 400

        temp_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(temp_path)

        svg_content = simple_image_to_svg(temp_path)

        if os.path.exists(temp_path):
            os.remove(temp_path)

        return jsonify({
            "success": True,
            "svg": svg_content
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
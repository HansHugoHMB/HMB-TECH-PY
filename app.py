from flask import Flask, request, jsonify, render_template_string
from PIL import Image
import os
import io
import base64

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HMB Tech - Image to SVG</title>
    <style>
        :root {
            --primary-color: #0D1C40;
            --accent-color: #FFD700;
            --text-color: #FFFFFF;
            --error-color: #FF4444;
            --success-color: #44FF44;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background: var(--primary-color);
            color: var(--text-color);
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        h1 {
            color: var(--accent-color);
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }

        .upload-zone {
            border: 3px dashed var(--accent-color);
            padding: 40px;
            text-align: center;
            margin: 20px 0;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            background: rgba(255, 215, 0, 0.1);
        }

        .upload-zone:hover {
            background: rgba(255, 215, 0, 0.2);
            transform: scale(1.02);
        }

        .upload-zone p {
            font-size: 1.2em;
            color: var(--accent-color);
        }

        .preview-section {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            display: none;
        }

        .preview-section h3 {
            color: var(--accent-color);
            margin-bottom: 15px;
        }

        .preview-content {
            max-width: 100%;
            overflow: hidden;
            margin: 15px 0;
        }

        .preview-content img, 
        .preview-content svg {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 0 auto;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .button-group {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 20px;
        }

        button {
            background: var(--accent-color);
            color: var(--primary-color);
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            font-size: 1em;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            opacity: 0.9;
        }

        #svgCode {
            background: rgba(0, 0, 0, 0.3);
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            color: var(--accent-color);
            font-family: monospace;
            margin-top: 20px;
            display: none;
            white-space: pre-wrap;
            max-height: 300px;
        }

        .error-message {
            background: var(--error-color);
            color: white;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            display: none;
        }

        .success-message {
            background: var(--success-color);
            color: white;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            display: none;
        }

        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            h1 {
                font-size: 1.8em;
            }

            .upload-zone {
                padding: 20px;
            }

            .button-group {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>HMB Tech - Convertisseur Image vers SVG</h1>
        
        <div class="upload-zone" onclick="document.getElementById('fileInput').click()">
            <input type="file" id="fileInput" style="display:none" accept=".png,.jpg,.jpeg">
            <p>📁 Cliquez ou glissez une image ici</p>
            <p style="font-size: 0.9em; color: #AAA;">Formats acceptés: PNG, JPG, JPEG</p>
        </div>

        <div id="error" class="error-message"></div>
        <div id="success" class="success-message"></div>

        <div id="preview" class="preview-section">
            <h3>Image originale</h3>
            <div class="preview-content">
                <img id="imagePreview" alt="Prévisualisation">
            </div>
        </div>

        <div id="svgPreview" class="preview-section">
            <h3>SVG généré</h3>
            <div class="preview-content" id="svgContainer"></div>
            <div class="button-group">
                <button onclick="downloadSVG()">💾 Télécharger SVG</button>
                <button onclick="toggleCode()">🔍 Voir le code SVG</button>
            </div>
        </div>

        <pre id="svgCode"></pre>
    </div>

    <script>
        let currentSVG = '';

        // Fonction pour montrer les messages d'erreur
        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        }

        // Fonction pour montrer les messages de succès
        function showSuccess(message) {
            const successDiv = document.getElementById('success');
            successDiv.textContent = message;
            successDiv.style.display = 'block';
            setTimeout(() => {
                successDiv.style.display = 'none';
            }, 5000);
        }

        // Support du drag and drop
        const dropZone = document.querySelector('.upload-zone');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults (e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });

        function highlight(e) {
            dropZone.style.transform = 'scale(1.02)';
            dropZone.style.background = 'rgba(255, 215, 0, 0.2)';
        }

        function unhighlight(e) {
            dropZone.style.transform = 'scale(1)';
            dropZone.style.background = 'rgba(255, 215, 0, 0.1)';
        }

        dropZone.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const file = dt.files[0];
            handleFile(file);
        }

        // Gestion du fichier
        document.getElementById('fileInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) handleFile(file);
        });

        function handleFile(file) {
            if (!file) return;

            const validTypes = ['image/jpeg', 'image/png'];
            if (!validTypes.includes(file.type)) {
                showError('Type de fichier non supporté. Utilisez PNG ou JPG/JPEG.');
                return;
            }

            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('imagePreview').src = e.target.result;
                document.getElementById('preview').style.display = 'block';
                uploadImage(file);
            }
            reader.readAsDataURL(file);
        }

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
                    showError(data.error);
                    return;
                }

                currentSVG = data.svg;
                document.getElementById('svgContainer').innerHTML = currentSVG;
                document.getElementById('svgPreview').style.display = 'block';
                showSuccess('Image convertie avec succès !');
                
            } catch (error) {
                showError('Erreur lors du traitement de l\'image');
                console.error('Error:', error);
            }
        }

        function downloadSVG() {
            if (!currentSVG) {
                showError('Aucun SVG à télécharger');
                return;
            }
            
            const blob = new Blob([currentSVG], {type: 'image/svg+xml'});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'hmb-tech.svg';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            showSuccess('SVG téléchargé !');
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

# Configuration
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def convert_to_svg(image_path):
    """Version améliorée de la conversion en SVG"""
    try:
        with Image.open(image_path) as img:
            # Conversion en RGB si nécessaire
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                # Conserver la transparence
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                # Créer un fond blanc
                background = Image.new('RGBA', img.size, (255, 255, 255, 255))
                background.paste(img, (0, 0), img)
                img = background.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Optimisation de la taille
            max_size = 800
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.LANCZOS)

            # Sauvegarde en PNG et conversion en base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            width, height = img.size
            
            # Création du SVG optimisé
            svg = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" version="1.1">
    <image width="{width}" height="{height}" preserveAspectRatio="none" href="data:image/png;base64,{img_base64}"/>
</svg>'''
            
            return svg.strip()
            
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

        try:
            svg_content = convert_to_svg(temp_path)
        finally:
            # Nettoyage du fichier temporaire
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
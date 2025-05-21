from flask import Flask, request, jsonify, render_template_string
from PIL import Image
import os
import io
import base64

app = Flask(__name__)

# Template HTML simplifié mais fonctionnel
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HMB Tech - Image to SVG</title>
    <style>
        body {
            background-color: #0D1C40;
            color: #FFD700;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
        }

        h1 {
            text-align: center;
            margin-bottom: 20px;
        }

        #dropZone {
            border: 2px dashed #FFD700;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
            cursor: pointer;
            background: rgba(255, 215, 0, 0.1);
        }

        #previewContainer, #svgContainer {
            background: rgba(0, 0, 0, 0.2);
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
            display: none;
        }

        #previewImage, #outputSvg {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 10px auto;
        }

        button {
            background: #FFD700;
            color: #0D1C40;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            cursor: pointer;
            font-weight: bold;
            border-radius: 5px;
            width: 100%;
        }

        button:hover {
            opacity: 0.9;
        }

        #messageBox {
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            display: none;
        }

        .error {
            background-color: #ff4444;
            color: white;
        }

        .success {
            background-color: #44ff44;
            color: black;
        }

        #loadingSpinner {
            display: none;
            text-align: center;
            margin: 20px 0;
        }

        #svgCode {
            background: rgba(0, 0, 0, 0.3);
            padding: 10px;
            border-radius: 5px;
            color: #FFD700;
            display: none;
            white-space: pre-wrap;
            overflow-x: auto;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>HMB Tech - Convertisseur Image vers SVG</h1>
        
        <div id="dropZone" onclick="document.getElementById('fileInput').click()">
            <input type="file" id="fileInput" accept=".png,.jpg,.jpeg" style="display: none;">
            <p>Cliquez ou glissez une image ici</p>
            <p style="font-size: 0.8em">Formats acceptés: PNG, JPG, JPEG</p>
        </div>

        <div id="messageBox"></div>
        
        <div id="loadingSpinner">
            Conversion en cours...
        </div>

        <div id="previewContainer">
            <h3>Image originale:</h3>
            <img id="previewImage" alt="Preview">
        </div>

        <div id="svgContainer">
            <h3>SVG généré:</h3>
            <div id="outputSvg"></div>
            <button onclick="downloadSVG()">Télécharger SVG</button>
            <button onclick="toggleSvgCode()">Voir le code SVG</button>
            <pre id="svgCode"></pre>
        </div>
    </div>

    <script>
        let currentSVG = '';
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const messageBox = document.getElementById('messageBox');
        const loadingSpinner = document.getElementById('loadingSpinner');
        const previewContainer = document.getElementById('previewContainer');
        const svgContainer = document.getElementById('svgContainer');
        const svgCode = document.getElementById('svgCode');

        function showMessage(message, isError = false) {
            messageBox.textContent = message;
            messageBox.style.display = 'block';
            messageBox.className = isError ? 'error' : 'success';
            setTimeout(() => {
                messageBox.style.display = 'none';
            }, 5000);
        }

        function handleFile(file) {
            if (!file) return;

            const validTypes = ['image/jpeg', 'image/png'];
            if (!validTypes.includes(file.type)) {
                showMessage('Type de fichier non supporté. Utilisez PNG ou JPG/JPEG.', true);
                return;
            }

            // Afficher la prévisualisation
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('previewImage').src = e.target.result;
                previewContainer.style.display = 'block';
            };
            reader.readAsDataURL(file);

            // Envoyer le fichier
            uploadFile(file);
        }

        async function uploadFile(file) {
            const formData = new FormData();
            formData.append('file', file);

            loadingSpinner.style.display = 'block';
            svgContainer.style.display = 'none';

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.error) {
                    showMessage(data.error, true);
                    return;
                }

                currentSVG = data.svg;
                document.getElementById('outputSvg').innerHTML = currentSVG;
                svgContainer.style.display = 'block';
                showMessage('Conversion réussie!');

            } catch (error) {
                showMessage('Erreur lors du traitement de l\'image', true);
                console.error('Error:', error);
            } finally {
                loadingSpinner.style.display = 'none';
            }
        }

        function downloadSVG() {
            if (!currentSVG) {
                showMessage('Aucun SVG à télécharger', true);
                return;
            }

            const blob = new Blob([currentSVG], {type: 'image/svg+xml'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'image-convertie.svg';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showMessage('SVG téléchargé avec succès!');
        }

        function toggleSvgCode() {
            if (svgCode.style.display === 'none') {
                svgCode.textContent = currentSVG;
                svgCode.style.display = 'block';
            } else {
                svgCode.style.display = 'none';
            }
        }

        // Event Listeners
        fileInput.addEventListener('change', (e) => handleFile(e.target.files[0]));

        // Drag and Drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.style.backgroundColor = 'rgba(255, 215, 0, 0.2)';
        });

        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dropZone.style.backgroundColor = 'rgba(255, 215, 0, 0.1)';
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.style.backgroundColor = 'rgba(255, 215, 0, 0.1)';
            handleFile(e.dataTransfer.files[0]);
        });
    </script>
</body>
</html>
'''

# Configuration
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def convert_to_svg(image_path):
    """Convertir une image en SVG"""
    try:
        with Image.open(image_path) as img:
            # Convertir en RGB si nécessaire
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGBA', img.size, (255, 255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img, mask=img.split()[1])
                img = background.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Redimensionner si nécessaire
            max_size = 800
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.LANCZOS)

            # Convertir en base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            width, height = img.size
            
            # Créer le SVG
            svg = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
    <image width="{width}" height="{height}" href="data:image/png;base64,{img_base64}"/>
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
        try:
            file.save(temp_path)
            svg_content = convert_to_svg(temp_path)
            return jsonify({
                "success": True,
                "svg": svg_content
            })
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
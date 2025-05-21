from flask import Flask, request, jsonify, render_template_string
from PIL import Image
import numpy as np
import cv2
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HMB Tech - Convertisseur Image → SVG</title>
    <style>
        body { 
            background: #0D1C40; 
            color: gold;
            font-family: Arial;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: auto;
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 8px;
        }
        .upload-box {
            border: 3px dashed gold;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
            cursor: pointer;
        }
        .preview {
            background: rgba(0,0,0,0.2);
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
            display: none;
        }
        .preview img, .preview svg {
            max-width: 100%;
            height: auto;
            margin: 10px 0;
            background: white;
        }
        button {
            background: gold;
            color: #0D1C40;
            border: none;
            padding: 10px;
            width: 100%;
            margin: 5px 0;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        }
        #message {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            display: none;
        }
        .error { background: #ff4444; color: white; }
        .success { background: #44ff44; color: black; }
        #loader {
            display: none;
            text-align: center;
            padding: 20px;
            color: gold;
        }
        .controls {
            background: rgba(0,0,0,0.2);
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        .controls label {
            display: block;
            margin: 10px 0;
        }
        input[type="range"] {
            width: 100%;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>HMB Tech - Convertisseur Image → SVG</h1>
        
        <div class="upload-box" onclick="document.getElementById('file').click()">
            <input type="file" id="file" hidden accept=".jpg,.jpeg,.png">
            <p>Cliquez ici pour sélectionner une image</p>
            <p style="font-size: 0.8em">(JPG, JPEG, PNG)</p>
        </div>

        <div class="controls">
            <label>
                Seuil de détection
                <input type="range" id="threshold" min="0" max="255" value="128">
            </label>
            <label>
                Niveau de détail
                <input type="range" id="detail" min="1" max="100" value="50">
            </label>
        </div>

        <div id="message"></div>
        <div id="loader">Conversion en cours...</div>

        <div id="imagePreview" class="preview">
            <h3>Image originale :</h3>
            <img id="preview">
        </div>

        <div id="svgResult" class="preview">
            <h3>SVG vectorisé :</h3>
            <div id="svgPreview"></div>
            <button onclick="downloadSVG()">Télécharger SVG</button>
            <button onclick="toggleCode()">Voir le code</button>
            <pre id="svgCode" style="display:none; white-space:pre-wrap;"></pre>
        </div>
    </div>

    <script>
        let currentSVG = '';
        let currentFile = null;
        const message = document.getElementById('message');
        const loader = document.getElementById('loader');
        
        function showMessage(text, isError) {
            message.textContent = text;
            message.className = isError ? 'error' : 'success';
            message.style.display = 'block';
            setTimeout(() => message.style.display = 'none', 5000);
        }

        function convertImage() {
            if (!currentFile) return;

            const form = new FormData();
            form.append('file', currentFile);
            form.append('threshold', document.getElementById('threshold').value);
            form.append('detail', document.getElementById('detail').value);

            loader.style.display = 'block';
            document.getElementById('svgResult').style.display = 'none';

            fetch('/convert', {
                method: 'POST',
                body: form
            })
            .then(res => res.json())
            .then(data => {
                loader.style.display = 'none';
                if (data.error) {
                    throw new Error(data.error);
                }
                currentSVG = data.svg;
                document.getElementById('svgPreview').innerHTML = currentSVG;
                document.getElementById('svgResult').style.display = 'block';
                showMessage('Conversion réussie !', false);
            })
            .catch(err => {
                loader.style.display = 'none';
                showMessage(err.message || 'Erreur de conversion', true);
            });
        }

        document.getElementById('file').onchange = function(e) {
            const file = e.target.files[0];
            if (!file) return;

            currentFile = file;

            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('preview').src = e.target.result;
                document.getElementById('imagePreview').style.display = 'block';
                convertImage();
            }
            reader.readAsDataURL(file);
        };

        // Mise à jour automatique lors du changement des paramètres
        document.getElementById('threshold').addEventListener('change', convertImage);
        document.getElementById('detail').addEventListener('change', convertImage);

        function downloadSVG() {
            if (!currentSVG) return;
            const blob = new Blob([currentSVG], {type: 'image/svg+xml'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'image-vectorisee.svg';
            a.click();
            URL.revokeObjectURL(url);
        }

        function toggleCode() {
            const code = document.getElementById('svgCode');
            if (code.style.display === 'none') {
                code.textContent = currentSVG;
                code.style.display = 'block';
            } else {
                code.style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def image_to_svg(file_path, threshold=128, detail=50):
    """Convertit une image en SVG en utilisant OpenCV"""
    try:
        # Lire l'image avec OpenCV
        img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        
        # Redimensionner si nécessaire
        max_size = 800
        if max(img.shape) > max_size:
            ratio = max_size / max(img.shape[0])
            img = cv2.resize(img, None, fx=ratio, fy=ratio)

        # Appliquer un seuil pour binariser l'image
        _, binary = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)

        # Trouver les contours
        contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        # Filtrer les contours selon le niveau de détail
        min_area = (img.shape[0] * img.shape[1]) * (1 - detail/100) / 1000
        filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]

        # Générer le SVG
        height, width = img.shape
        svg = f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'

        # Ajouter les contours au SVG
        for contour in filtered_contours:
            path = "M"
            for point in contour.reshape(-1, 2):
                x, y = point
                path += f" {x},{y}"
            path += "Z"
            svg += f'<path d="{path}" fill="black"/>'

        svg += "</svg>"
        return svg

    except Exception as e:
        raise Exception(f"Erreur de conversion : {str(e)}")

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier reçu'}), 400
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'Nom de fichier vide'}), 400
        
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        return jsonify({'error': 'Format non supporté'}), 400

    try:
        temp_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(temp_path)
        
        threshold = int(request.form.get('threshold', 128))
        detail = int(request.form.get('detail', 50))
        
        svg = image_to_svg(temp_path, threshold, detail)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return jsonify({
            'success': True,
            'svg': svg
        })
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
from flask import Flask, request, jsonify, render_template_string
from PIL import Image
import numpy as np
import potrace
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
        const message = document.getElementById('message');
        const loader = document.getElementById('loader');
        
        function showMessage(text, isError) {
            message.textContent = text;
            message.className = isError ? 'error' : 'success';
            message.style.display = 'block';
            setTimeout(() => message.style.display = 'none', 5000);
        }

        document.getElementById('file').onchange = function(e) {
            const file = e.target.files[0];
            if (!file) return;

            // Afficher la prévisualisation
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('preview').src = e.target.result;
                document.getElementById('imagePreview').style.display = 'block';
            }
            reader.readAsDataURL(file);

            // Envoyer pour conversion
            const form = new FormData();
            form.append('file', file);

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
        };

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

def image_to_svg(file_path):
    """Convertit une image en véritable SVG vectoriel"""
    try:
        # Ouvrir et préparer l'image
        with Image.open(file_path) as img:
            # Convertir en niveaux de gris
            if img.mode != 'L':
                img = img.convert('L')
            
            # Redimensionner si nécessaire
            max_size = 800
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.LANCZOS)

            # Convertir en tableau numpy
            data = np.array(img)

            # Créer un bitmap pour potrace
            # Seuil à 128 pour la binarisation
            bitmap = potrace.Bitmap(data < 128)
            
            # Tracer les contours
            path = bitmap.trace()

            # Générer le SVG
            width, height = img.size
            svg = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
            svg += '<g transform="scale(1,-1) translate(0,-{})">'.format(height)

            # Ajouter les chemins
            for curve in path:
                svg += '<path d="'
                for segment in curve:
                    x0, y0 = segment.start_point
                    svg += f'M {x0:.1f} {y0:.1f} '
                    
                    if segment.is_corner:
                        x1, y1 = segment.c
                        x2, y2 = segment.end_point
                        svg += f'L {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f} '
                    else:
                        x1, y1 = segment.c1
                        x2, y2 = segment.c2
                        x3, y3 = segment.end_point
                        svg += f'C {x1:.1f} {y1:.1f} {x2:.1f} {y2:.1f} {x3:.1f} {y3:.1f} '
                
                svg += 'Z" fill="black" />'
            
            svg += '</g></svg>'
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
        
        svg = image_to_svg(temp_path)
        
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
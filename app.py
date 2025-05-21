from flask import Flask, request, jsonify, render_template_string, abort
from PIL import Image
import os
import io
import base64

app = Flask(__name__)

# Template HTML simple mais fonctionnel
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

        <div id="imagePreview" class="preview">
            <h3>Image originale :</h3>
            <img id="preview">
        </div>

        <div id="svgResult" class="preview">
            <h3>SVG généré :</h3>
            <div id="svgPreview"></div>
            <button onclick="downloadSVG()">Télécharger SVG</button>
            <button onclick="toggleCode()">Voir le code</button>
            <pre id="svgCode" style="display:none; white-space:pre-wrap;"></pre>
        </div>
    </div>

    <script>
        let currentSVG = '';
        const message = document.getElementById('message');
        
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

            fetch('/convert', {
                method: 'POST',
                body: form
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                currentSVG = data.svg;
                document.getElementById('svgPreview').innerHTML = currentSVG;
                document.getElementById('svgResult').style.display = 'block';
                showMessage('Conversion réussie !', false);
            })
            .catch(err => {
                showMessage(err.message || 'Erreur de conversion', true);
            });
        };

        function downloadSVG() {
            if (!currentSVG) return;
            const blob = new Blob([currentSVG], {type: 'image/svg+xml'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'image-convertie.svg';
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

# Dossier pour les fichiers temporaires
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def image_to_svg(file_path):
    """Convertit une image en SVG avec data URL"""
    try:
        with Image.open(file_path) as img:
            # Convertir en RGB
            if img.mode in ('RGBA', 'LA'):
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[-1])
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Redimensionner si nécessaire
            max_size = 800
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                img = img.resize([int(s * ratio) for s in img.size], Image.LANCZOS)

            # Convertir en base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            img_b64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Générer le SVG
            width, height = img.size
            return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" 
                      xmlns="http://www.w3.org/2000/svg">
                      <image width="{width}" height="{height}" 
                      href="data:image/png;base64,{img_b64}"/>
                   </svg>'''
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
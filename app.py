from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from PIL import Image
import numpy as np
import svgwrite
import os
import io
import base64
import cairosvg
import potrace
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = Path('uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Créer le dossier uploads s'il n'existe pas
UPLOAD_FOLDER.mkdir(exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def image_to_svg(image_path, transparent=False):
    """Convertit une image en SVG optimisé"""
    try:
        # Ouvrir l'image avec Pillow
        with Image.open(image_path) as img:
            # Convertir en mode RGB si nécessaire
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Redimensionner si l'image est trop grande
            max_size = 1200
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.LANCZOS)

            # Convertir en noir et blanc pour le traçage
            bw = img.convert('L')
            
            # Convertir en tableau numpy et créer un bitmap
            bitmap = potrace.Bitmap(np.array(bw))
            
            # Tracer les contours
            path = bitmap.trace()
            
            # Créer un nouveau document SVG
            dwg = svgwrite.Drawing(size=img.size)
            
            # Si non transparent, ajouter un fond blanc
            if not transparent:
                dwg.add(dwg.rect(size=('100%', '100%'), fill='white'))
            
            # Ajouter les chemins au SVG
            for curve in path:
                points = curve.tesselate()
                d = f'M {points[0].x},{points[0].y}'
                for p in points[1:]:
                    d += f' L {p.x},{p.y}'
                d += ' Z'
                dwg.add(dwg.path(d=d, fill='black'))
            
            # Optimiser la sortie
            svg_string = dwg.tostring()
            
            return svg_string
            
    except Exception as e:
        raise Exception(f"Erreur lors de la conversion en SVG: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Aucun fichier envoyé"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Aucun fichier sélectionné"}), 400
            
        if not allowed_file(file.filename):
            return jsonify({"error": "Type de fichier non autorisé"}), 400

        # Sauvegarder le fichier temporairement
        temp_path = UPLOAD_FOLDER / file.filename
        file.save(temp_path)

        # Obtenir le paramètre transparent
        transparent = request.form.get('transparent', 'false').lower() == 'true'

        # Convertir l'image en SVG
        svg_content = image_to_svg(temp_path, transparent)

        # Supprimer le fichier temporaire
        temp_path.unlink()

        return jsonify({
            "success": True,
            "svg": svg_content
        })

    except Exception as e:
        # En cas d'erreur, nettoyer les fichiers temporaires
        if 'temp_path' in locals() and temp_path.exists():
            temp_path.unlink()
        return jsonify({
            "error": str(e)
        }), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({
        "error": "Le fichier est trop volumineux"
    }), 413

@app.errorhandler(500)
def server_error(e):
    return jsonify({
        "error": "Erreur serveur interne"
    }), 500

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, request, jsonify
from flask_cors import CORS
import io
import sys
import os
import base64
import traceback

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return '''
    <h1 style="color:gold; background:#0D1C49; padding:20px; text-align:center;">
        Bienvenue sur le serveur Python HMB-Tech
    </h1>
    <p style="color:white; text-align:center;">
        Envoyez vos scripts Python via une requête POST à <code>/run</code> (application/json).
    </p>
    '''

@app.route('/run', methods=['POST'])
def run_code():
    try:
        code = request.json.get("code", "")
        files = request.json.get("files", {})

        # Sauvegarde temporaire des fichiers uploadés
        for filename, content in files.items():
            with open(filename, 'wb') as f:
                f.write(base64.b64decode(content))

        stdout = io.StringIO()
        stderr = io.StringIO()
        sys.stdout = stdout
        sys.stderr = stderr

        # Contexte d'exécution isolé
        local_env = {}
        exec(code, {}, local_env)

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        return jsonify({
            "output": stdout.getvalue(),
            "error": stderr.getvalue(),
        })

    except Exception as e:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        return jsonify({
            "output": "",
            "error": traceback.format_exc()
        })

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Aucun fichier envoyé"}), 400
    file = request.files['file']
    filename = file.filename
    file.save(os.path.join(".", filename))
    return jsonify({"message": f"Fichier {filename} téléversé avec succès"})

if __name__ == '__main__':
    app.run(debug=True)
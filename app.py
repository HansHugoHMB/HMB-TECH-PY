from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import io
import base64
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)
CORS(app)  # Pour permettre les appels depuis une page HTML

@app.route('/', methods=['GET'])
def index():
    return '''
        <h1 style="color:gold;background-color:#0D1C49;padding:20px">
        Bienvenue sur l'API HMB Python Runner
        </h1>
        <p style="color:white;padding:10px;">Fais une requête POST à <code>/run</code> pour exécuter du code Python.</p>
    '''

@app.route('/run', methods=['POST'])
def run_code():
    try:
        code = request.json.get("code", "")

        if "plt.plot" in code:
            x = np.linspace(0, 10, 100)
            y = np.sin(x)
            plt.plot(x, y)
            plt.title("Graphique de sin(x)")

            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)

            img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
            plt.close()
            return jsonify({"output": "Voici votre image", "image": img_base64})

        stdout = io.StringIO()
        sys.stdout = stdout
        exec(code, {})
        sys.stdout = sys.__stdout__
        return jsonify({"output": stdout.getvalue()})

    except Exception as e:
        return jsonify({"output": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
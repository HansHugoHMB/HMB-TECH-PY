from flask import Flask, request, jsonify
import sys
import io
import base64
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)

@app.route('/run', methods=['POST'])
def run_code():
    try:
        code = request.json.get("code", "")
        
        # Si le code contient des instructions pour générer une image, on l'exécute
        if "plt.plot" in code:  # Vérifie si plt.plot est présent dans le code
            # Générer un graphique avec matplotlib
            x = np.linspace(0, 10, 100)
            y = np.sin(x)
            plt.plot(x, y)
            plt.title("Graphique de sin(x)")
            
            # Sauvegarder l'image dans un objet en mémoire (en format PNG)
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)  # Remise à zéro du curseur du fichier en mémoire
            
            # Convertir l'image en base64
            img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
            plt.close()  # Fermer l'image après génération

            # Renvoi du résultat avec l'image encodée en base64
            return jsonify({"output": "Voici votre image", "image": img_base64})
        
        # Si le code ne génère pas d'image, on l'exécute normalement
        stdout = io.StringIO()
        sys.stdout = stdout
        exec(code, {})
        sys.stdout = sys.__stdout__
        return jsonify({"output": stdout.getvalue()})
    
    except Exception as e:
        return jsonify({"output": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
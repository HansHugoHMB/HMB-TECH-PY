from flask import Flask, request, jsonify
import sys
import io
import base64
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <html>
        <head>
            <title>API Python de Hans Mbaya</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #0D1C49;
                    color: #FFD700;
                    padding: 40px;
                }
                h2 {
                    color: #FFD700;
                }
                pre {
                    background-color: #1a2a5c;
                    color: #FFD700;
                    padding: 15px;
                    border-radius: 5px;
                }
                code {
                    background-color: #1f326f;
                    padding: 2px 4px;
                    border-radius: 4px;
                    font-family: monospace;
                    color: #FFD700;
                }
                p {
                    font-size: 16px;
                }
            </style>
        </head>
        <body>
            <h2>Bienvenue sur l'API Python de Hans Mbaya</h2>
            <p>Utilisez une requête POST vers <code>/run</code> avec un JSON comme :</p>
            <pre>{
  "code": "print('Hello world')"
}</pre>
            <p>Si votre code contient <code>plt.plot</code>, un graphique sera généré automatiquement.</p>
        </body>
    </html>
    """

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
import os
from proxy import Proxy

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Render fournit le port via la variable PORT
    proxy = Proxy()
    proxy.run(host="0.0.0.0", port=port)
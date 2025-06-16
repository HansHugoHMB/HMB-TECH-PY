import subprocess
from colorama import init, Fore, Back, Style

# Initialisation de colorama pour le style dans le terminal
init(autoreset=True)

# Couleurs personnalisées (doré et fond bleu nuit simulé)
gold = Fore.YELLOW
background = Back.BLUE  # Simule le fond #0D1C40, approximation console

# Affichage stylisé
print(background + gold + Style.BRIGHT + "\n📡 Bienvenue sur le serveur de HMB-TECH\n")

# Lancement du proxy
subprocess.run(["proxy", "--hostname", "0.0.0.0", "--port", "8080"])
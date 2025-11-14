# save as csv_to_json.py
import csv, json, sys   # On importe les modules nécessaires :
                        # - csv pour lire les fichiers CSV
                        # - json pour écrire le fichier JSON
                        # - sys pour lire les arguments passés dans la ligne de commande

# usage: python csv_to_json.py input.csv output.json
# ↑ Commentaire expliquant comment exécuter le script en ligne de commande.
# Exemple : python csv_to_json.py data/couriers.csv output.json

# On récupère le premier argument (nom du fichier CSV d'entrée)
# Si aucun argument n'est fourni, on utilise le fichier par défaut "data/couriers.csv"
inp = sys.argv[1] if len(sys.argv) > 1 else "data/couriers.csv"

# On récupère le deuxième argument (nom du fichier JSON de sortie)
# Si aucun argument n'est fourni, on crée "output.json" par défaut
out = sys.argv[2] if len(sys.argv) > 2 else "output.json"

# On crée une liste vide pour stocker les lignes converties
rows = []

# On ouvre le fichier CSV en lecture avec encodage UTF-8
with open(inp, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)  # Permet de lire chaque ligne du CSV sous forme de dictionnaire
                                # Exemple : {"pickup": "Restaurant A", "dropoff": "Client Z", "reward": "6.5"}
    for r in reader:            # On parcourt chaque ligne du CSV
        # Si la clé "reward" existe et n’est pas vide
        if "reward" in r and r["reward"] != "":
            # On convertit la valeur de "reward" en nombre flottant (float)
            r["reward"] = float(r["reward"])
        # On ajoute le dictionnaire (la ligne convertie) à la liste
        rows.append(r)

# On ouvre le fichier JSON de sortie en écriture
with open(out, "w", encoding="utf-8") as f:
    # On écrit la liste `rows` au format JSON
    # - ensure_ascii=False pour garder les caractères accentués
    # - indent=2 pour rendre le JSON lisible (indentation de 2 espaces)
    json.dump(rows, f, ensure_ascii=False, indent=2)

# On affiche un message de confirmation dans le terminal
print(f"OK → {out}")

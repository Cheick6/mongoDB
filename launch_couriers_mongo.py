import argparse, csv, subprocess, sys, os

# -------------------------------------------------
# Script "Launcher" : lance plusieurs livreurs à la fois
# -------------------------------------------------
# Ce programme lit un fichier CSV avec la liste des livreurs,
# puis lance un script "courier_mongo.py" pour chacun d’eux.
# Chaque livreur s’exécute dans un processus séparé.

def main():
    # --- Lecture du chemin du fichier CSV ---
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default="data/couriers.csv",
        help="Fichier CSV avec colonnes : id,name,accept_rate"
    )
    args = parser.parse_args()

    # --- Vérifie si le fichier CSV existe ---
    if not os.path.exists(args.csv):
        print(f"[Launcher] Fichier introuvable : {args.csv}")
        sys.exit(1)

    procs = []  # Liste qui contiendra les processus des livreurs

    # --- Ouvre le fichier CSV ---
    with open(args.csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)  # Lit le CSV sous forme de dictionnaire

        # --- Parcourt chaque ligne (chaque livreur) ---
        for row in reader:
            cid = (row.get("id") or "").strip()              # identifiant du livreur
            name = (row.get("name") or "Livreur").strip()    # nom du livreur
            rate = (row.get("accept_rate") or "0.9").strip() # taux d’acceptation (0 à 1)

            # Si pas d’identifiant → on ignore la ligne
            if not cid:
                continue

            # --- Prépare la commande pour lancer le script du livreur ---
            # Exemple :
            # python courier_mongo.py --id L1 --name "Ali" --accept-rate 0.8
            cmd = [sys.executable, "courier_mongo.py", "--id", cid, "--name", name, "--accept-rate", rate]

            print("[Launcher] Lancement :", " ".join(cmd))

            # Lance le processus (le script du livreur)
            procs.append(subprocess.Popen(cmd))

    # --- Résumé ---
    print(f"[Launcher] ✅ {len(procs)} livreur(s) lancé(s). Appuie sur Ctrl+C pour arrêter.")

    try:
        # Attend que tous les processus se terminent
        for p in procs:
            p.wait()
    except KeyboardInterrupt:
        # Si on fait Ctrl+C, on arrête tous les livreurs
        print("\n[Launcher]  Arrêt demandé, fermeture des livreurs...")
        for p in procs:
            p.terminate()

# Point d’entrée du programme
if __name__ == "__main__":
    main()

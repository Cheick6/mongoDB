import argparse
import time
from typing import Optional
from pymongo.errors import DuplicateKeyError
from pymongo import DESCENDING

from common import mongo, ensure_indexes, new_annonce, new_selection, new_notification_assignment

# -------------------------------------------------
# Script "Manager"
# -------------------------------------------------
# Ce script joue le rôle du gestionnaire (ou "dispatch").
# Il publie des annonces (courses à livrer), attend les candidatures,
# choisit le meilleur livreur, et lui envoie une notification.

# -------------------------------------------------
# 1️ Choisir le meilleur candidat
# -------------------------------------------------
def choose_best_candidate(cands):
    """Retourne le candidat avec le plus petit ETA (temps d’arrivée)."""
    return sorted(cands, key=lambda c: c.get("eta", 999999))[0] if cands else None

# -------------------------------------------------
# 2️ Attendre les candidatures
# -------------------------------------------------
def wait_candidatures(db, annonce_id: str, wait_seconds: float = 8.0):
    """
    Attend les candidatures reçues pour une annonce pendant un certain temps.
    - Utilise un Change Stream pour détecter les insertions en temps réel.
    - Retourne la liste des candidatures reçues.
    """
    deadline = time.time() + wait_seconds  # fin du délai d’attente
    cands = []  # liste des candidatures reçues

    # Filtrer uniquement les insertions de candidatures pour cette annonce
    pipeline = [
        {"$match": {"operationType": "insert", "fullDocument.annonceId": annonce_id}}
    ]

    # Écoute les nouvelles candidatures dans MongoDB
    with db.candidatures.watch(pipeline=pipeline, full_document="default", max_await_time_ms=1000) as stream:
        while time.time() < deadline:
            change = stream.try_next()  # essaie de lire un changement
            if change:
                doc = change.get("fullDocument", {})
                cands.append(doc)
                print(f"[Manager] 📨 Candidature reçue : {doc}")
            else:
                time.sleep(0.2)  # petite pause pour éviter la surcharge CPU
    return cands

# -------------------------------------------------
# 3️ Assigner le livreur choisi
# -------------------------------------------------
def assign(db, annonce_id: str, courier_id: str):
    """
    Attribue l’annonce à un livreur :
    - insère une sélection,
    - met à jour le statut de l’annonce,
    - envoie une notification au livreur.
    """
    sel = new_selection(annonce_id, courier_id)
    try:
        db.selections.insert_one(sel)
    except DuplicateKeyError:
        print("[Manager] ⚠️ Une sélection existe déjà pour cette annonce.")
        return False

    # Mise à jour du statut de l’annonce : "assigned"
    db.annonces.update_one(
        {"_id": annonce_id},
        {"$set": {"status": "assigned", "chosenCourierId": courier_id}}
    )

    # Crée et envoie une notification à ce livreur
    notif = new_notification_assignment(courier_id, annonce_id)
    db.notifications.insert_one(notif)

    print(f"[Manager] ✅ Assignation enregistrée et notification envoyée : {sel}")
    return True

# -------------------------------------------------
# 4️ Publier une annonce et gérer son cycle complet
# -------------------------------------------------
def process_one(db, pickup: str, dropoff: str, reward: float, wait_seconds: float):
    """
    Publie une annonce, attend les candidatures, et attribue la course.
    """
    ann = new_annonce(pickup, dropoff, reward)
    db.annonces.insert_one(ann)
    print(f"[Manager] 📢 Annonce publiée : {ann}")

    # Attend les candidatures des livreurs pendant X secondes
    cands = wait_candidatures(db, ann["_id"], wait_seconds)
    if not cands:
        print("[Manager] Aucun candidat dans le délai.")
        return

    # Choisit le meilleur candidat (plus petit ETA)
    best = choose_best_candidate(cands)
    print(f"[Manager]  Meilleur candidat : {best}")

    # Assigne la course au livreur choisi
    assign(db, ann["_id"], best["courierId"])

# -------------------------------------------------
# 5️ Fonction principale
# -------------------------------------------------
def main():
    # Lecture des paramètres du script
    parser = argparse.ArgumentParser()
    parser.add_argument("--pickup", default="Restaurant A")
    parser.add_argument("--dropoff", default="Client Z")
    parser.add_argument("--reward", type=float, default=6.5)
    parser.add_argument("--wait", type=float, default=8.0)
    parser.add_argument("--csv", type=str, help="Fichier CSV avec pickup,dropoff,reward")
    parser.add_argument("--interval", type=float, default=1.5)
    args = parser.parse_args()

    # Connexion à la base MongoDB
    client = mongo()
    db = client.get_database("ubereats")
    ensure_indexes(db)

    # --- Si un fichier CSV est fourni ---
    # Chaque ligne correspond à une annonce à publier
    if args.csv:
        import csv
        with open(args.csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pickup = (row.get("pickup") or args.pickup).strip()
                dropoff = (row.get("dropoff") or args.dropoff).strip()
                reward = float((row.get("reward") or args.reward))
                process_one(db, pickup, dropoff, reward, args.wait)
                time.sleep(args.interval)  # petite pause entre chaque annonce
    else:
        # Si pas de CSV, on publie une seule annonce
        process_one(db, args.pickup, args.dropoff, args.reward, args.wait)

# -------------------------------------------------
# Point d’entrée du programme
# -------------------------------------------------
if __name__ == "__main__":
    main()

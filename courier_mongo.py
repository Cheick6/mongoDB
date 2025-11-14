import argparse
import random
import time

from common import mongo, ensure_indexes, new_candidature

# ----------------------------------------
# Programme du livreur (simulateur)
# ----------------------------------------
# Ce script simule le comportement d’un livreur :
# il écoute les nouvelles annonces et les notifications MongoDB en temps réel.
# Quand une nouvelle course apparaît, il décide (au hasard) s’il veut y répondre.

def main():
    # --- Lecture des arguments de la ligne de commande ---
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True, help="Identifiant unique du livreur")
    parser.add_argument("--name", default="Livreur", help="Nom affiché du livreur")
    parser.add_argument("--accept-rate", type=float, default=0.9, help="Probabilité d'accepter une annonce (entre 0 et 1)")
    args = parser.parse_args()

    # --- Connexion à la base de données MongoDB ---
    client = mongo()
    db = client.get_database("ubereats")

    # Crée les index nécessaires si ce n’est pas déjà fait
    ensure_indexes(db)

    # --- Définition des pipelines pour écouter les changements Mongo ---
    # 1. Pour les annonces : on veut écouter uniquement les "insert" d’annonces "open"
    pipeline_annonces = [
        {"$match": {"operationType": "insert", "fullDocument.status": "open"}}
    ]

    # 2. Pour les notifications : on écoute les notifs envoyées à CE livreur
    pipeline_notifs = [
        {"$match": {"operationType": "insert", "fullDocument.courierId": args.id}}
    ]

    # --- Ouverture des Change Streams (écoute en temps réel) ---
    # On ouvre deux flux :
    # - ann_stream : écoute des nouvelles annonces
    # - notif_stream : écoute des notifications destinées à ce livreur
    with db.annonces.watch(pipeline=pipeline_annonces, full_document="default", max_await_time_ms=1000) as ann_stream, \
         db.notifications.watch(pipeline=pipeline_notifs, full_document="default", max_await_time_ms=1000) as notif_stream:

        print(f"[Courier {args.id}] ✅ En écoute des annonces & notifications...")

        # --- Boucle infinie : écoute continue ---
        while True:
            # --- 1) Vérifie s’il y a une nouvelle notification ---
            notif = notif_stream.try_next()
            if notif:
                doc = notif.get("fullDocument", {})
                # Si la notif est une assignation, on affiche un message
                if doc.get("type") == "assignment":
                    print(f"[Courier {args.id}] 🎉 Assignation reçue pour annonce {doc.get('annonceId')}")

            # --- 2) Vérifie s’il y a une nouvelle annonce ---
            change = ann_stream.try_next()
            if change:
                ann = change.get("fullDocument", {})
                ann_id = ann.get("_id")
                print(f"[Courier {args.id}] 🆕 Nouvelle annonce reçue : {ann}")

                # Le livreur décide s’il accepte ou pas (en fonction du taux d’acceptation)
                if random.random() <= args.accept_rate:
                    # Génère un ETA (temps estimé d’arrivée) entre 5 et 20 minutes
                    eta = random.randint(5, 20)
                    # Crée la candidature correspondante
                    cand = new_candidature(ann_id, args.id, args.name, eta)
                    # L’envoie dans la collection "candidatures"
                    db.candidatures.insert_one(cand)
                    print(f"[Courier {args.id}] Candidature envoyée : {cand}")
                else:
                    print(f"[Courier {args.id}]  Je passe cette annonce.")

            # Petite pause pour ne pas surcharger la boucle
            time.sleep(0.1)

# Point d’entrée du programme
if __name__ == "__main__":
    main()

import os
import uuid
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING, DESCENDING

# ----------------------------------------
# Connexion à MongoDB
# ----------------------------------------
# On utilise un utilisateur "ubereats" avec mot de passe.
# Le "replicaSet=rs0" est obligatoire pour activer les Change Streams.
# "authSource=ubereats" indique où vérifier le mot de passe.
DEFAULT_URI = (
    "mongodb://ubereats_app:ubereats123@localhost:27017/ubereats"
    "?replicaSet=rs0&authSource=ubereats"
)



def now():
    """Retourne la date et l’heure actuelle en UTC."""
    return datetime.now(timezone.utc)

def mongo():
    """Crée la connexion à MongoDB."""
    # Si une variable d’environnement MONGO_URI existe, on l’utilise.
    # Sinon, on prend DEFAULT_URI.
    uri = os.getenv("MONGO_URI", DEFAULT_URI)
    # On augmente un peu le temps d’attente si le serveur met du temps à répondre.
    return MongoClient(uri, serverSelectionTimeoutMS=10000)

# ----------------------------------------
# Création des index
# ----------------------------------------
def ensure_indexes(db):
    """Crée les index nécessaires dans les collections."""
    # Un seul livreur peut être sélectionné par annonce.
    db.selections.create_index([("annonceId", ASCENDING)], unique=True, name="uniq_annonce_selection")

    # Permet de trier les candidatures d’une annonce par ETA (temps estimé).
    db.candidatures.create_index([("annonceId", ASCENDING), ("eta", ASCENDING)], name="by_annonce_eta")

    # Permet de chercher rapidement les annonces ouvertes les plus récentes.
    db.annonces.create_index([("status", ASCENDING), ("createdAt", DESCENDING)], name="by_status_created")

# ----------------------------------------
# Fonctions pour créer les documents
# ----------------------------------------
def new_annonce(pickup: str, dropoff: str, reward: float):
    """Crée une nouvelle annonce (course à livrer)."""
    return {
        "_id": str(uuid.uuid4()),     # identifiant unique
        "pickup": pickup,             # lieu de récupération
        "dropoff": dropoff,           # lieu de livraison
        "reward": float(reward),      # prix de la course
        "status": "open",             # statut : ouverte
        "createdAt": now(),           # date de création
    }

def new_candidature(annonce_id: str, courier_id: str, courier_name: str, eta: int):
    """Crée une candidature d’un livreur pour une annonce."""
    return {
        "_id": str(uuid.uuid4()),     # identifiant unique
        "annonceId": annonce_id,      # référence de l’annonce
        "courierId": courier_id,      # identifiant du livreur
        "courierName": courier_name,  # nom du livreur
        "eta": int(eta),              # temps estimé d’arrivée (en secondes)
        "createdAt": now(),           # date de création
    }

def new_selection(annonce_id: str, courier_id: str):
    """Crée une sélection quand un livreur est choisi pour une annonce."""
    return {
        "_id": str(uuid.uuid4()),     # identifiant unique
        "annonceId": annonce_id,      # référence de l’annonce
        "courierId": courier_id,      # livreur choisi
        "status": "assigned",         # statut : assigné
        "createdAt": now(),           # date de création
    }

def new_notification_assignment(courier_id: str, annonce_id: str):
    """Crée une notification pour informer un livreur qu’il a une nouvelle course."""
    return {
        "_id": str(uuid.uuid4()),     # identifiant unique
        "courierId": courier_id,      # livreur concerné
        "type": "assignment",         # type de notification
        "annonceId": annonce_id,      # annonce concernée
        "createdAt": now(),           # date de création
    }

# UberEats-like Platform — MongoDB Change Streams POC (Python)

Ce POC reprend la logique Manager ⇄ Livreurs mais **full MongoDB** :
- Le **manager** insère des **annonces** dans MongoDB.
- Les **livreurs** écoutent (`Change Streams`) les **nouvelles annonces** et publient des **candidatures**.
- Le **manager** écoute (`Change Streams`) les **candidatures** liées à son annonce, **sélectionne** le meilleur (stratégie: *meilleur ETA*), et écrit une **selection** + une **notification** au livreur.

> Nécessite un MongoDB en **replica set** (ok chez toi : `rs0`).

## 🔧 Prérequis
- Python 3.10+
- MongoDB 7 en replica set (`rs0`) accessible sur `mongodb://ubereats:ubereats123@localhost:27017/ubereats?replicaSet=rs0&authSource=ubereats`
- `pip install -r requirements.txt`

## Installation
```bash
pip install -r requirements.txt
```
### ▶Pour redémarrer :
```bash
docker start mongo-poc
```
### ▶Pour l'arrêter:
```bash
docker stop mongo-poc
```
### ▶Pour voir si il tourne:
```bash
docker docker ps
```

## connecte-toi avec ton compte ubereats Copie-colle cette commande :
```bash
docker exec -it mongo-poc mongosh -u ubereats -p ubereats123 --authenticationDatabase ubereats

```
## Ensuite rentre dans ta Bd ubereats 

- use ubereats
- show collections
- db.annonces.find().pretty()
- db.candidatures.find().pretty()
- db.selections.find().pretty()
- db.notifications.find().pretty()

## Afficher ce qu'il se passe sur le serveur 
```bash
docker logs -f mongodb
```

## ⚙️ Variables d'environnement (optionnel)
- `MONGO_URI` (sinon valeur par défaut): `mongodb://app:app123@localhost:27017/ubereats?replicaSet=rs0`

## ▶️ Lancer la démo

### A) Lancer des livreurs (depuis un CSV)
```bash
python launch_couriers_mongo.py --csv data/couriers.csv
```
Chaque livreur écoute les annonces et publie sa candidature avec un `eta` aléatoire (pondéré par `--accept-rate`).  
Il écoute aussi ses **notifications** (assignations).

### B) Publier des annonces (depuis un CSV)
```bash
python manager_mongo.py --csv data/announcements.csv --wait 10 --interval 2
```
Pour chaque annonce : le manager attend jusqu'à `--wait` secondes les candidatures, choisit la **meilleure ETA**, crée la **selection**, notifie le livreur.

### C) Mode simple (une seule annonce en CLI)
```bash
python manager_mongo.py --pickup "Restaurant A" --dropoff "Client Z" --reward 6.5 --wait 8
```

## Collections
- `annonces`      : `{ _id, pickup, dropoff, reward, status:"open|assigned", chosenCourierId?, createdAt }`
- `candidatures`  : `{ _id, annonceId, courierId, courierName, eta, createdAt }`
- `selections`    : `{ _id, annonceId, courierId, status:"assigned", createdAt }` (index unique sur `annonceId`)
- `notifications` : `{ _id, courierId, type:"assignment", annonceId, createdAt }`

##  Indexes créés au démarrage
- `selections`: unique `{ annonceId: 1 }`
- `candidatures`: `{ annonceId: 1, eta: 1 }`
- `annonces`: `{ status: 1, createdAt: -1 }`

## Notes
- Change Streams exigent `replicaSet` → vous êtes déjà en `rs0` 
- En prod, remplace l'aléatoire ETA par un vrai calcul (distance, trafic, note du livreur, etc.).
# mongoDB

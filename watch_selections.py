from common import mongo  # Importe la fonction mongo() depuis le module common (gère la connexion à MongoDB)

client = mongo()  # Initialise le client MongoDB à l’aide de la fonction mongo()

db = client.get_database("ubereats")  # Sélectionne la base de données "ubereats"

print("[Watcher] En écoute des selections...")  # Indique dans la console que l'écoute commence

pipeline = [{"$match": {"operationType": "insert"}}]  # Définit le filtre : ne réagir qu’aux insertions de documents

with db.selections.watch(pipeline=pipeline, full_document="default") as stream:  # Ouvre un flux d’écoute (Change Stream) sur la collection "selections"
    for change in stream:  # Boucle infinie : traite chaque événement dès qu’un document est inséré
        print("[Watcher] Nouvelle selection:", change.get("fullDocument"))  # Affiche le document inséré dans la console

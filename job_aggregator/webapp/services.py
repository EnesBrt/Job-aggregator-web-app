import requests
import time
import threading
import json
from urllib.parse import quote_plus
import pprint

# Token d'accès actuel pour l'API de Pôle Emploi
current_token = None


# Générer un token d'accès pour l'API de Pôle Emploi
def generate_token():
    global current_token
    url = "https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"

    headers = {"content-type": "application/x-www-form-urlencoded"}

    data = {
        "grant_type": "client_credentials",
        "client_id": "PAR_workaggregator_a30664a55d29ccbe52caf22755443f85fd7e803404c0c733f4113f0f89bf4336",
        "client_secret": "bdf0504a83deb575d744fdb9ccb3ae1d45ffbc54b701723e6ce5c14e08b574b4",
        "scope": "api_offresdemploiv2 o2dsoffre",
    }

    # Demander un token d'accès toutes les 24 minutes
    while True:
        try:
            response = requests.post(url, headers=headers, data=data)
            print(f"Status code: {response.status_code}")
            print(f"Response body: {response.text}")
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                print("Failed to decode JSON response")
                continue

            if "access_token" in response_json:
                current_token = response_json["access_token"]
                expires_in = response_json["expires_in"]
                # Dormir pendant la durée d'expiration moins un délai de sécurité de 60 secondes
                time.sleep(expires_in - 60)
            else:
                print("access_token not found in the response")
            time.sleep(1439)
        except requests.exceptions.RequestException as e:
            print(e)


def job_search(query):
    # URL de recherche pour l'API de Pôle Emploi
    def search_url(query):
        base_url = (
            "https://api.pole-emploi.io/partenaire/offresdemploi/v2/offres/search?"
        )
        key_words = quote_plus(query)
        url = f"{base_url}motsCles={key_words}"
        return url

    # Obtenir les offres d'emploi pour un travail spécifique
    def get_jobs_offers(query):
        global current_token
        url = search_url(query)
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {current_token}",
        }

        # Attendre jusqu'à ce que le token soit disponible
        while current_token is None:
            time.sleep(0.1)
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 401 or response.status_code == 500:
                print("token non valide, renouvellement du token...")
                generate_token()
                response = requests.get(url, headers=headers)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(e)
            return None

        # Vérifier si la requête a réussi
        if response.status_code in [200, 206]:
            try:
                return response.json()
            except json.JSONDecodeError:
                print("Échec du décodage de la réponse JSON")
                return None
        else:
            print(f"La requête a échoué avec le code de statut {response.status_code}")
            return None

    # Afficher les offres d'emploi
    def print_jobs_offers(query):
        response = get_jobs_offers(query)
        job_offers = response.get("resultats")
        liste_offres = []
        if job_offers is not None:
            for i, offer in enumerate(job_offers):
                if i >= 5:
                    break

                liste_offres_dict = {
                    "Intitulé": offer.get("intitule"),
                    "Entreprise": offer.get("entreprise"),
                    "Lieu de travail": offer.get("lieuTravail"),
                    "Type de contrat": offer.get("typeContrat"),
                    "Salaire": offer.get("salaire"),
                    "Origine offre": offer.get("origineOffre"),
                    "Description": offer.get("description"),
                }

                liste_offres.append(liste_offres_dict)

                # Affichage formaté des offres d'emploi
                """
                for offre in liste_offres:
                    print("\n")
                    print(f"Intitulé: {offre['Intitulé']}")
                    print("\n")
                    print(f"Entreprise: {offre['Entreprise']}")
                    print("\n")
                    print(f"Lieu de travail: {offre['Lieu de travail']}")
                    print("\n")
                    print(f"Type de contrat: {offre['Type de contrat']}")
                    print("\n")
                    print(
                        f"Salaire: {offre['Salaire'] if offre['Salaire'] else 'Non spécifié'}"
                    )
                    print("\n")
                    print(f"Origine de l'offre: {offre['Origine offre']}")
                    print("\n")
                    print(f"Description: {offre['Description']}")
                    print("\n")
                    print("-" * 100)
                    print("\n")
                """
        else:
            return "Aucune offre d'emploi trouvée ou une erreur s'est produite."
        return liste_offres

    return print_jobs_offers(query)


# Thread est un module qui permet de faire des tâches en parallèle.
# C'est-à-dire que le programme peut faire plusieurs tâches en même temps.
# Par exemple, la fonction generate_token() est exécutée en parallèle avec le reste du programme.
# Cela signifie aussie qu'une fonction peut être exécutée indépendamment et en arrière plan du reste du programme.
# daemon=True signifie que le thread s'arrête lorsque le programme principal s'arrête.

token_thread = threading.Thread(target=generate_token)
token_thread.daemon = True
token_thread.start()

if __name__ == "__main__":
    # Demander à l'utilisateur le travail qu'il recherche
    while True:
        query = input(
            "Entrez le nom du poste que vous recherchez (ou 'q' pour quitter) : "
        )
        if query.lower() == "q":
            exit()

        # print_jobs_offers(query=query)
        job_search_result = job_search(query=query)
        print(job_search_result)

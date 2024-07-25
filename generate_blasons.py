import csv
from playwright.sync_api import sync_playwright
import wptools

departements = {}
communes = {}

with open("data/v_departement_2024.csv") as file:
    reader = csv.DictReader(file)

    for nom_departement in reader:
        departements[nom_departement["DEP"]] = nom_departement

with open("data/v_commune_2024.csv") as file:
    reader = csv.DictReader(file)

    for commune in reader:
        # Pas d'ancienne commune
        if commune["TYPECOM"] == "COM":
            communes[commune["COM"]] = commune

# Configuration manuelle de certains blasons
blasons = {
    "Florac Trois Rivières": "Blason_ville_fr_Florac_48.svg",
    "Segré-en-Anjou Bleu": "Blason_ville_fr_Segré_(Maine-et-Loire).svg",
    "Coutances": "Blason_Coutances.svg",
    "Louhans": "Blason_Louhans.svg",
    "Évry-Courcouronnes": "Blason_Evry.svg",
    "Marseille": "Blason_Marseille.svg",
    "Brest": "Blason_de_Brest.svg",
    "Toulouse": "Blason_de_Toulouse.svg",
    "Mont-de-Marsan": "Blason_mont-de-marsan.svg",
    "Reims": "Blason_ville_Reims.svg",
    "Nancy": "Blason_Nancy_54.svg",
    "Le Mans": "Blason_de_la_ville_de_Le_Mans_(Sarthe).svg",
    "Toulon": "Blason_ville_fr_Toulon_(Var).svg",
    "Bordeaux": "Coat_of_arms_of_Bordeaux,_France.svg",
    "Orléans": "Blason_Orléans.svg",
    "Lille": "Blason_ville_fr_Lille_(Nord).svg",
    "Clermont-Ferrand": "Blason_ville_fr_ClermontFerrand_(PuyDome).svg",
    "Pau": "Arms_of_Pau.svg",
    "Lyon": "Blason_Ville_fr_Lyon.svg",
    "Rouen": "Blason_Rouen_76.svg",
    "Nice": "Arms_of_Nice.svg",
    "Nantes": "Blason_Nantes.svg",
    "Metz": "Blason_Metz_57.svg",
    "Strasbourg": "Blason_Strasbourg.svg",
    "Paris": "Blason_paris_75.svg",
    "Roanne": "Blason_ville_fr_Roanne_(Loire).svg",
    "Montargis": "Blason_ville_fr_Montargis4_(Loiret).svg",
    "Bayonne": "Blason_Bayonne.svg",
}

with sync_playwright() as p:
    browser = p.chromium.launch()
    browser_page = browser.new_page()

    with open("data/v_arrondissement_2024.csv") as file:
        print("CODE;LIBELLE;URL")

        reader = csv.DictReader(file)

        for arrondissement in reader:
            code_departement = arrondissement["DEP"]
            code_insee = arrondissement["CHEFLIEU"]
            ville = communes[code_insee]["LIBELLE"]

            # France métropolitaine uniquement
            if code_departement in ["971", "972", "973", "974", "976"]:
                continue

            print(f"{code_insee};{ville};", end="")

            file = None

            if blasons.get(ville):
                # Configuration sans Wikipedia du blason
                file = blasons[ville]
            else:
                # Tentative avec juste le nom de la ville comme nom de page Wikipedia
                wikipedia_page_name = ville

                wikipedia_page = wptools.page(
                    wikipedia_page_name, lang="fr", silent=True
                )

                data = wikipedia_page.get_parse().data

                if data.get("infobox") and data["infobox"].get("blason"):
                    file = data["infobox"]["blason"]
                else:
                    departement = departements[communes[code_insee]["DEP"]]["LIBELLE"]

                    # Tentative avec également le nom du département comme nom de page Wikipedia
                    wikipedia_page_name = f"{ville} ({departement})"

                    wikipedia_page = wptools.page(
                        wikipedia_page_name, lang="fr", silent=True
                    )

                    data = wikipedia_page.get_parse().data

                    if data.get("infobox") and data["infobox"].get("blason"):
                        file = data["infobox"]["blason"]

            blason = ""

            if file:
                # Récupération du nom du vrai fichier
                url = f"https://commons.wikimedia.org/wiki/File:{file}"

                browser_page.goto(url)
                locator = browser_page.locator("#file > a")

                blason = locator.get_attribute("href")

            print(blason)

        # Ajouts manuels
        print(
            "31113;Castanet-Tolosan;https://upload.wikimedia.org/wikipedia/commons/9/98/Blason_ville_fr_Castanet-Tolosan_%28Haute-Garonne%29.svg"
        )

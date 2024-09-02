import csv
import io
import jinja2
import math
import os
import pathlib
from PIL import Image
from playwright.sync_api import sync_playwright

# from pyproj import Transformer
import requests

# A mettre à True pour PrinterStudio
printer_studio = False


def deg_to_dms(deg, type):
    decimals, number = math.modf(deg)
    d = int(number)
    m = int(decimals * 60)
    s = (deg - d - m / 60) * 3600.00

    if deg < 0:
        if type == "lon":
            dir = "Ouest"
        else:
            dir = "Sud"
    else:
        if type == "lon":
            dir = "Est"
        else:
            dir = "Nord"

    return [abs(d), abs(m), abs(s), dir]


# transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857")


def proj_x_y(lat, lon):
    # Projection équirectangulaire
    # Méridien central (longitude) : 002° 06' E = 2.1
    # Parallèle à la bonne échelle (latitude) : 46° 15' N = 46.25
    LAT0 = 46.25
    LON0 = 2.1

    x = math.cos(LAT0) * (lon - LON0)
    y = lat - LAT0

    # return transformer.transform(lat, lon)
    return [x, y]


def img_x_y(lat, lon):
    # Point en haut à gauche de la carte
    lat1 = 51.50
    lon1 = -5.8

    x1, y1 = proj_x_y(lat1, lon1)

    # Point en bas à droite de la carte
    lat2 = 41
    lon2 = 10

    x2, y2 = proj_x_y(lat2, lon2)

    x, y = proj_x_y(lat, lon)

    # Dimension en pixels du fond de carte
    largeur_carte = 252
    hauteur_carte = 242

    X = largeur_carte * (x - x1) / (x2 - x1)
    Y = hauteur_carte * (y - y1) / (y2 - y1)

    # Dimensions en pixel du point sur la carte
    largeur_point = 24
    hauteur_point = 24

    return [X - largeur_point / 2, Y - hauteur_point / 2]


def generate(nom_ville, nom_departement, population, code_insee, type_ville):
    print(f"{code_insee};{nom_ville}")

    # Calcul des coordonnées de la ville
    response = requests.get(
        f"https://geo.api.gouv.fr/communes/{code_insee}?fields=centre"
    )

    response_json = response.json()

    lon = response_json["centre"]["coordinates"][0]
    lat = response_json["centre"]["coordinates"][1]

    lat_d, lat_m, lat_s, lat_dir = deg_to_dms(lat, "lat")
    lon_d, lon_m, lon_s, lon_dir = deg_to_dms(lon, "lon")

    img_x, img_y = img_x_y(lat, lon)

    # Image du blason
    blason_url = blasons[code_insee]["URL"]

    # Génération du HTML
    output = template.render(
        nom_ville=nom_ville,
        nom_departement=nom_departement,
        population=f"{int(population):,d}".replace(",", " "),
        lat_d=lat_d,
        lat_m=lat_m,
        lat_dir=lat_dir,
        lon_d=lon_d,
        lon_m=lon_m,
        lon_dir=lon_dir,
        img_x=img_x,
        img_y=img_y,
        blason_url=blason_url,
    )

    html_file = f"{images_directory}/{type_ville}_{code_insee}.html"
    back_file = f"{images_directory}/{type_ville}_{code_insee}_back.png"
    front_file = f"{images_directory}/{type_ville}_{code_insee}_front.png"

    with open(html_file, "w") as stream:
        stream.write(output)

    # Génération des images recto et verso
    page.goto(f"file://{html_file}")

    screenshot_bytes = page.locator(".back").screenshot()
    image = Image.open(io.BytesIO(screenshot_bytes))

    if printer_studio:
        # Rotation pour PrinterStudio
        image = image.transpose(Image.Transpose.ROTATE_270)

    image.save(back_file)

    screenshot_bytes = page.locator(".front").screenshot()
    image = Image.open(io.BytesIO(screenshot_bytes))

    if printer_studio:
        # Rotation pour PrinterStudio
        image = image.transpose(Image.Transpose.ROTATE_90)

    image.save(front_file)

    os.unlink(html_file)


templates_directory = f"{pathlib.Path(__file__).parent}/templates"
images_directory = f"{pathlib.Path(__file__).parent}/images"

jinja2_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(templates_directory)
)

template = jinja2_environment.get_template("index.html")

regions = {}
departements = {}
donnees_communes = {}
communes = {}
arrondissements = {}
blasons = {}

with open("data/v_region_2024.csv") as file:
    reader = csv.DictReader(file)

    for nom_region in reader:
        regions[nom_region["REG"]] = nom_region

with open("data/v_departement_2024.csv") as file:
    reader = csv.DictReader(file)

    for nom_departement in reader:
        departements[nom_departement["DEP"]] = nom_departement

with open("data/v_arrondissement_2024.csv") as file:
    reader = csv.DictReader(file)

    for arrondissement in reader:
        arrondissements[arrondissement["ARR"]] = arrondissement

with open("data/donnees_communes.csv") as file:
    reader = csv.DictReader(file, delimiter=";")

    for donnees_commune in reader:
        donnees_communes[donnees_commune["COM"]] = donnees_commune

with open("data/v_commune_2024.csv") as file:
    reader = csv.DictReader(file)

    for commune in reader:
        # Pas d'ancienne commune
        if commune["TYPECOM"] == "COM":
            communes[commune["COM"]] = commune

            # Population de la commune (parfois disponible au niveau de la commune parente)
            if donnees_communes.get(commune["COM"]):
                communes[commune["COM"]]["PMUN"] = donnees_communes[commune["COM"]][
                    "PMUN"
                ]

with open("data/blasons.csv") as file:
    reader = csv.DictReader(file, delimiter=";")

    for blason in reader:
        blasons[blason["CODE"]] = blason

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    # Boucle principale
    for arrondissement in arrondissements.values():
        code_departement = arrondissement["DEP"]
        code_region = arrondissement["REG"]
        code_insee = arrondissement["CHEFLIEU"]

        nom_ville = communes[code_insee]["LIBELLE"]

        # Correction cosmétique
        if nom_ville == "Château-Chinon (Ville)":
            nom_ville = "Château-Chinon"

        nom_departement = departements[code_departement]["LIBELLE"]
        nom_region = regions[code_region]["LIBELLE"]

        population = communes[code_insee]["PMUN"]

        prefecture = departements[code_departement]["CHEFLIEU"]

        if code_insee == prefecture:
            type_ville = "prefecture"
        else:
            type_ville = "sous_prefecture"

        # France métropolitaine uniquement
        if code_departement in ["971", "972", "973", "974", "976"]:
            continue

        generate(
            nom_ville=nom_ville,
            nom_departement=nom_departement,
            population=population,
            code_insee=code_insee,
            type_ville=type_ville,
        )

    # Ajouts manuels
    generate(
        nom_ville="Castanet-Tolosan",
        nom_departement="Haute-Garonne",
        population="14903",
        code_insee="31113",
        type_ville="commune",
    )

    browser.close()

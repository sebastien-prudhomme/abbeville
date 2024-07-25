# Préparation

Pré-requis : Linux et environnement Python avec Poetry
Attention : des paquets vont être installés au niveau système !

```
poetry install
poetry run playwright install
poetry run playwright install-deps
```

# Génération des données pour les blasons

```
poetry run python generate_blasons.py > data/blasons.csv
```

# Génération des images dans le répertoire images

```
poetry run python abbeville.py
```

# Sources

Fond de carte simplifié à partir de : https://commons.wikimedia.org/wiki/File:France_location_map-Regions_and_departements-2016.svg

Point sur la carte : https://commons.wikimedia.org/wiki/File:City_locator_14.svg

Code officiel géographique 2024 : https://www.insee.fr/fr/information/7766585

Recensement 2021 (corrigé en ajoutant les 3 villes avec arrondissement) : https://www.insee.fr/fr/statistiques/7739582

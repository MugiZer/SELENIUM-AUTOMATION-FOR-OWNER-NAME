import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import json

from scraper.parsers import parse_result_json, parse_result_page


SAMPLE_HTML = """
<html>
  <header class="page-header">
    <div class="content-header-extras">
      <ul class="list-inline">
        <li class="list-inline-item"><div><div>Montréal</div><div>2023-2025</div></div></li>
      </ul>
    </div>
  </header>
  <section>
    <h2 id="proprietaires">Propriétaires</h2>
    <ul class="list">
      <li class="list-item">
        <div class="list-item-content"><div></div><div>John Doe</div></div>
      </li>
      <li class="list-item">
        <div class="list-item-content"><div></div><div>Acme Inc</div></div>
      </li>
    </ul>
  </section>
  <section>
    <h2 id="identification">Identification</h2>
    <dl>
      <dt>Numéro de matricule</dt><dd>1234-56-7890</dd>
      <dt>Numéro de compte foncier</dt><dd>30 - F26131400</dd>
    </dl>
  </section>
  <section>
    <h2 id="caracteristiques">Caractéristiques</h2>
    <h3 class="h4">Caractéristiques du bâtiment principal</h3>
    <dl>
      <dt>Nombre de logements</dt><dd>4</dd>
    </dl>
  </section>
  <section>
    <h2 id="valeur">Valeur</h2>
    <section>
      <h3>Rôle courant</h3>
      <dl>
        <dt>Terrain</dt><dd>12 345 $</dd>
        <dt>Bâtiment</dt><dd>23 456 $</dd>
        <dt>Total</dt><dd>35 801 $</dd>
      </dl>
    </section>
    <section>
      <h3>Rôle antérieur</h3>
      <dl>
        <dt>Total</dt><dd>30 000 $</dd>
      </dl>
    </section>
    <section>
      <table>
        <tr><th>Sous-catégorie</th><th>Pourcentage</th></tr>
        <tr><td>Résidentiel</td><td>80 %</td></tr>
        <tr><td>Commercial</td><td>20 %</td></tr>
      </table>
    </section>
  </section>
</html>
"""


SAMPLE_JSON = {
    "pageProps": {
        "sections": [
            {
                "id": "header",
                "data": {
                    "items": [
                        {"label": "Municipalité", "value": "Montréal"},
                        {"label": "Période du rôle", "value": "2023-2025"},
                    ]
                },
            },
            {
                "id": "proprietaires",
                "title": "Propriétaires",
                "items": [
                    {"value": "John Doe"},
                    {"value": "Acme Inc"},
                ],
            },
            {
                "id": "identification",
                "rows": [
                    {"label": "Numéro de matricule", "value": "1234-56-7890"},
                    {"label": "Numéro de compte foncier", "value": "30 - F26131400"},
                ],
            },
            {
                "id": "caracteristiques",
                "title": "Caractéristiques du bâtiment principal",
                "rows": [
                    {"label": "Nombre de logements", "value": "4"},
                ],
            },
            {
                "id": "valeur",
                "sections": [
                    {
                        "title": "Rôle courant",
                        "rows": [
                            {"label": "Terrain", "value": "12 345 $"},
                            {"label": "Bâtiment", "value": "23 456 $"},
                            {"label": "Total", "value": "35 801 $"},
                        ],
                    },
                    {
                        "title": "Rôle antérieur",
                        "rows": [
                            {"label": "Total", "value": "30 000 $"},
                        ],
                    },
                    {
                        "title": "Répartition",
                        "rows": [
                            {"cells": [{"text": "Sous-catégorie"}, {"text": "Pourcentage"}]},
                            {"cells": [{"text": "Résidentiel"}, {"text": "80 %"}]},
                            {"cells": [{"text": "Commercial"}, {"text": "20 %"}]},
                        ],
                    },
                ],
            },
        ]
    }
}


def test_parse_result_page_extracts_fields():
    result = parse_result_page(SAMPLE_HTML)
    assert result["municipality"] == "Montréal"
    assert result["fiscal_years"] == "2023-2025"
    assert result["owner_names"] == "John Doe; Acme Inc"
    assert result["owner_type"] == "corporation"
    assert result["matricule"] == "1234-56-7890"
    assert result["tax_account_number"] == "30 - F26131400"
    assert result["nb_logements"] == "4"
    assert result["assessed_terrain_current"] == "12345"
    assert result["assessed_batiment_current"] == "23456"
    assert result["assessed_total_current"] == "35801"
    assert result["assessed_total_previous"] == "30000"
    distribution = json.loads(result["tax_distribution_json"])
    assert distribution[0]["subcategory"] == "Résidentiel"
    assert distribution[0]["percentage"] == "80"


def test_parse_result_json_prefers_embedded_html():
    result = parse_result_json(SAMPLE_JSON)
    assert result["owner_names"] == "John Doe; Acme Inc"
    assert result["owner_type"] == "corporation"
    assert result["matricule"] == "1234-56-7890"
    assert result["tax_account_number"] == "30 - F26131400"
    assert result["assessed_total_current"] == "35801"
    assert result["assessed_total_previous"] == "30000"
    distribution = json.loads(result["tax_distribution_json"])
    assert distribution[0]["subcategory"] == "Résidentiel"
    assert distribution[0]["percentage"] == "80"


def test_parse_result_json_falls_back_to_html():
    payload = {
        "pageProps": {
            "content": {
                "html": SAMPLE_HTML,
            }
        }
    }
    result = parse_result_json(payload)
    assert result["owner_names"] == "John Doe; Acme Inc"

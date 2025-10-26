# Montréal Role d'évaluation Scraper

This project automates the Montréal Rôle d’évaluation foncière workflow for CSV or Google Sheets inputs. It enriches rows with owner and assessment data while respecting ToS-friendly scraping practices (rate limiting, retries, and stealth browser behaviors).

## Features

- Playwright (Chromium) automation with basic stealth evasion.
- Supports CSV and Google Sheets sources via a unified CLI.
- Retries with exponential backoff and jittered delays between requests.
- SQLite cache prevents duplicate work on re-runs.
- Deterministic output schema appended to each data source.
- Atomic CSV overwrites, timestamped backups, and snapshot exports.
- Google Sheets batching with rollback-aware retry handling.
- Structured logging to console and `logs/run.log`.

## Requirements

- Python 3.11
- Playwright dependencies (Chromium browser binaries)

Install Python dependencies:

```bash
pip install -r requirements.txt
playwright install
```

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

| Variable | Description |
| --- | --- |
| `MONTREAL_EMAIL` | Optional: account email used when `--login` is supplied. |
| `MONTREAL_PASSWORD` | Optional: password for the Montréal account. |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Path to a Google service account JSON file or the JSON string itself. Required for Sheets mode. |
| `SHEET_NAME` / `SHEET_TAB` | Defaults for CLI flags. |
| `DELAY_MIN` / `DELAY_MAX` | Default jitter window (seconds). |
| `CACHE_PATH` | Path to the SQLite cache file. |
| `LOG_LEVEL` | Logging verbosity (e.g., `INFO`). |

## Google Sheets Setup

1. Create a Google Cloud project and enable the Sheets API.
2. Generate a service account with the "Editor" role.
3. Download the service account JSON and share your spreadsheet with the service account email.
4. Provide the JSON file path (or inline JSON string) via `GOOGLE_SERVICE_ACCOUNT_JSON`.

## CLI Usage

```bash
python main.py --csv ./input/mtl_targets.csv --max 250 --delay-min 1.5 --delay-max 3.0
python main.py --sheet "MTL Plex Leads" --tab "20-40" --from-row 2
python main.py --csv ./input/mtl_targets.csv --headful
python main.py --sheet "MTL Plex Leads" --tab "20-40" --login
```

### Output Columns

Each processed row gains the following columns:

- `owner_names`
- `owner_type`
- `matricule`
- `tax_account_number`
- `municipality`
- `fiscal_years`
- `nb_logements`
- `assessed_terrain_current`
- `assessed_batiment_current`
- `assessed_total_current`
- `assessed_total_previous`
- `tax_distribution_json`
- `last_fetched_at`
- `source_url`
- `status`

## Logging

Logs are written to stdout and `logs/run.log` via a rotating handler. Adjust verbosity with the `LOG_LEVEL` environment variable.

## Testing

Unit tests cover the HTML parser logic:

```bash
pytest
```

## Troubleshooting

- **Playwright missing browsers**: run `playwright install`.
- **Authentication failures**: ensure `MONTREAL_EMAIL` and `MONTREAL_PASSWORD` are set and valid.
- **Sheets authentication**: confirm the spreadsheet is shared with the service account email and the JSON credentials are correct.
- **429 or 5xx responses**: the scraper retries automatically with exponential backoff while keeping rate limits.

## Appendix: DevTools Data (verbatim)

The following section is reproduced verbatim from the project brief to ensure selector fidelity.

✳️ DEVTOOLS DATA (append EXACTLY, do not modify)

https://montreal.ca/role-evaluation-fonciere/adresse

API NETWORK :

1)When we fill numéro d immeuble :

Request URL
https://www.google-analytics.com/g/collect?v=2&tid=G-X85NG0G8NT&gtm=45je5a11v9134341101z89134342162za200zb9134342162zd9134342162&_p=1759709177686&gcd=13l3l3l3l1l1&npa=0&dma=0&cid=1605043035.1759704688&ul=en-us&sr=1280x720&uaa=x86&uab=64&uafvl=Chromium%3B140.0.7339.185%7CNot%253DA%253FBrand%3B24.0.0.0%7CGoogle%2520Chrome%3B140.0.7339.185&uamb=0&uam=&uap=Windows&uapv=19.0.0&uaw=0&are=1&frm=0&pscdl=&_eu=AAAAAAQ&_s=1&tag_exp=101509157~103116026~103200004~103233427~104527907~104528500~104573694~104684208~104684211~104948813~115480710~115834636~115834638&sid=1759709127&sct=2&seg=1&dl=https%3A%2F%2Fmontreal.ca%2Frole-evaluation-fonciere%2Fadresse&dt=R%C3%B4le%20d%E2%80%99%C3%A9valuation%20fonci%C3%A8re&en=page_view&tfd=5478

Request Method
POST
Status Code
204 No Content
Remote Address
142.250.69.46:443
Referrer Policy
strict-origin-when-cross-origin
Request URL
https://www.google-analytics.com/g/collect?v=2&tid=G-X85NG0G8NT&gtm=45je5a11v9134341101za200zb9134342162zd9134342162&_p=1759709177686&gcd=13l3l3l3l1l1&npa=0&dma=0&cid=1605043035.1759704688&ul=en-us&sr=1280x720&uaa=x86&uab=64&uafvl=Chromium%3B140.0.7339.185%7CNot%253DA%253FBrand%3B24.0.0.0%7CGoogle%2520Chrome%3B140.0.7339.185&uamb=0&uam=&uap=Windows&uapv=19.0.0&uaw=0&are=1&frm=0&pscdl=&_eu=AEEAAAQ&_s=2&tag_exp=101509157~103116026~103200004~103233427~104527907~104528500~104573694~104684208~104684211~104948813~115480710~115834636~115834638&sid=1759709127&sct=2&seg=1&dl=https%3A%2F%2Fmontreal.ca%2Frole-evaluation-fonciere%2Fadresse&dt=R%C3%B4le%20d%E2%80%99%C3%A9valuation%20fonci%C3%A8re&en=form_start&ep.form_id=%C2%ABR6%C2%BB&ep.form_name=&ep.form_destination=https%3A%2F%2Fmontreal.ca%2Frole-evaluation-fonciere%2Fadresse%2Fliste&epn.form_length=13&ep.first_field_id=radix-%C2%ABr9%C2%BB&ep.first_field_name=civicNumber&ep.first_field_type=&epn.first_field_position=1&_et=4612&tfd=10492

2)when we fill Nom de la rue :
Request URL
https://montreal.ca/_next/data/info-recherche-2-3-13/fr-CA/role-evaluation-fonciere.json

Request Method
GET
Status Code
200 OK
Remote Address
104.18.7.89:443
Referrer Policy
strict-origin-when-cross-origin
Request URL
https://montreal.ca/info-recherche/_next/static/css/406ef883613c4fbc.css

Request Method
GET
Status Code
200 OK (from disk cache)
Remote Address
104.18.7.89:443
Referrer Policy
strict-origin-when-cross-origin
equest URL
https://montreal.ca/info-recherche/api/evaluation-fonciere/gem/streets?q=Bishop&page=1&size=10

Request Method
GET
Status Code
304 Not Modified
Remote Address
104.18.6.89:443
Referrer Policy
strict-origin-when-cross-origin
Request URL
https://www.google-analytics.com/g/collect?v=2&tid=G-X85NG0G8NT&gtm=45je5a11v9134341101z89134342162za200zb9134342162zd9134342162&_p=1759706936984&gcd=13l3l3l3l1l1&npa=0&dma=0&cid=1605043035.1759704688&ul=en-us&sr=1280x720&uaa=x86&uab=64&uafvl=Chromium%3B140.0.7339.185%7CNot%253DA%253FBrand%3B24.0.0.0%7CGoogle%2520Chrome%3B140.0.7339.185&uamb=0&uam=&uap=Windows&uapv=19.0.0&uaw=0&are=1&frm=0&pscdl=&_eu=AAAAAAQ&_s=1&tag_exp=101509157~103116026~103200004~103233427~104527906~104528500~104684208~104684211~104948813~115480710~115616986~115834636~115834638~115868795~115868797&sid=1759704706&sct=1&seg=1&dl=https%3A%2F%2Fmontreal.ca%2Frole-evaluation-fonciere%2Fadresse&dt=R%C3%B4le%20d%E2%80%99%C3%A9valuation%20fonci%C3%A8re&en=page_view&tfd=5989

Request URL
https://montreal.ca/info-recherche/api/evaluation-fonciere/gem/streets?q=Rue+Bishop%2C+Arrondissement+de+Ville-Marie+%28Montr%C3%A9al%29&page=1&size=10

Request Method
GET
Status Code
304 Not Modified
Remote Address
104.18.6.89:443
Referrer Policy
strict-origin-when-cross-origin
Request URL
https://www.google-analytics.com/g/collect?v=2&tid=G-X85NG0G8NT&gtm=45je5a11v9134341101za200zb9134342162zd9134342162&_p=1759706936984&gcd=13l3l3l3l1l1&npa=0&dma=0&cid=1605043035.1759704688&ul=en-us&sr=1280x720&uaa=x86&uab=64&uafvl=Chromium%3B140.0.7339.185%7CNot%253DA%253FBrand%3B24.0.0.0%7CGoogle%2520Chrome%3B140.0.7339.185&uamb=0&uam=&uap=Windows&uapv=19.0.0&uaw=0&are=1&frm=0&pscdl=&_eu=AEEAAAQ&_s=2&tag_exp=101509157~103116026~103200004~103233427~104527906~104528500~104684208~104684211~104948813~115480710~115616986~115834636~115834638~115868795~115868797&sid=1759704706&sct=1&seg=1&dl=https%3A%2F%2Fmontreal.ca%2Frole-evaluation-fonciere%2Fadresse&dt=R%C3%B4le%20d%E2%80%99%C3%A9valuation%20fonci%C3%A8re&en=form_start&ep.form_id=%C2%ABR6%C2%BB&ep.form_name=&ep.form_destination=https%3A%2F%2Fmontreal.ca%2Frole-evaluation-fonciere%2Fadresse%2Fliste&epn.form_length=13&ep.first_field_id=radix-%C2%ABrc%C2%BB&ep.first_field_name=streetNameCombobox&ep.first_field_type=&epn.first_field_position=2&_et=9062&tfd=15071

after you click search and new page loads

Request URL
https://api.montreal.ca/api/city-services/citizen/v2/organisations?limit=100

Request Method
GET
Status Code
304 Not Modified
Remote Address
104.18.7.89:443
Referrer Policy
strict-origin-when-cross-origin

Request URL
https://montreal.ca/_next/data/info-recherche-2-3-13/fr-CA/role-evaluation-fonciere.json

Request Method
GET
Status Code
200 OK
Remote Address
104.18.7.89:443
Referrer Policy
strict-origin-when-cross-origin

Request URL
https://montreal.ca/_next/data/info-recherche-2-3-13/fr-CA/role-evaluation-fonciere.json

Request Method
GET
Status Code
200 OK
Remote Address
104.18.7.89:443
Referrer Policy
strict-origin-when-cross-origin

Request URL
https://montreal.ca/_next/data/info-recherche-2-3-13/fr-CA/role-evaluation-fonciere/adresse.json

Request Method
GET
Status Code
200 OK
Remote Address
104.18.7.89:443
Referrer Policy
strict-origin-when-cross-origin

Request URL
https://montreal.ca/info-recherche/_next/static/css/406ef883613c4fbc.css

Request Method
GET
Status Code
200 OK (from disk cache)
Remote Address
104.18.7.89:443
Referrer Policy
strict-origin-when-cross-origin

Request URL
https://montreal.ca/info-recherche/_next/static/css/b184c00d65df50f6.css

Request Method
GET
Status Code
200 OK (from disk cache)
Remote Address
104.18.7.89:443
Referrer Policy
strict-origin-when-cross-origin

Request URL
https://www.google-analytics.com/g/collect?v=2&tid=G-X85NG0G8NT&gtm=45je5a11v9134341101z89134342162za200zb9134342162zd9134342162&_p=1759709531675&gcd=13l3l3l3l1l1&npa=0&dma=0&cid=1605043035.1759704688&ul=en-us&sr=1280x720&uaa=x86&uab=64&uafvl=Chromium%3B140.0.7339.185%7CNot%253DA%253FBrand%3B24.0.0.0%7CGoogle%2520Chrome%3B140.0.7339.185&uamb=0&uam=&uap=Windows&uapv=19.0.0&uaw=0&are=1&frm=0&pscdl=&_eu=AAAAAAQ&_s=1&tag_exp=101509157~103116026~103200004~103233427~104527906~104528500~104573694~104684208~104684211~104948813~115480710~115616985~115834636~115834638&sid=1759709127&sct=2&seg=1&dl=https%3A%2F%2Fmontreal.ca%2Frole-evaluation-fonciere%2Fadresse%2Fliste&dr=https%3A%2F%2Fmontreal.ca%2Frole-evaluation-fonciere%2Fadresse&dt=R%C3%B4le%20d%E2%80%99%C3%A9valuation%20fonci%C3%A8re&en=page_view&tfd=5994

when you click on confirmed address

Request URL
https://montreal.ca/_next/data/info-recherche-2-3-13/fr-CA/role-evaluation-fonciere/adresse/liste.json

Request Method
GET
Status Code
200 OK
Remote Address
104.18.6.89:443
Referrer Policy
strict-origin-when-cross-origin

Request URL
https://montreal.ca/info-recherche/_next/static/css/17b088d930ab19b4.css

Request Method
GET
Status Code
200 OK (from disk cache)
Remote Address
104.18.7.89:443
Referrer Policy
strict-origin-when-cross-origin

Request URL
https://www.google-analytics.com/g/collect?v=2&tid=G-X85NG0G8NT&gtm=45je5a11v9134341101z89134342162za200zb9134342162zd9134342162&_p=1759709701553&gcd=13l3l3l3l1l1&npa=0&dma=0&cid=1605043035.1759704688&ul=en-us&sr=1280x720&uaa=x86&uab=64&uafvl=Chromium%3B140.0.7339.185%7CNot%253DA%253FBrand%3B24.0.0.0%7CGoogle%2520Chrome%3B140.0.7339.185&uamb=0&uam=&uap=Windows&uapv=19.0.0&uaw=0&are=1&frm=0&pscdl=&_eu=AAAAAAQ&_s=1&tag_exp=101509157~103116026~103200004~103233427~104527906~104528501~104573694~104684208~104684211~104948813~115480709~115834636~115834638&sid=1759709127&sct=2&seg=1&dl=https%3A%2F%2Fmontreal.ca%2Frole-evaluation-fonciere%2Fadresse%2Fliste%2Fresultat&dr=https%3A%2F%2Fmontreal.ca%2Frole-evaluation-fonciere%2Fadresse%2Fliste&dt=R%C3%B4le%20d%E2%80%99%C3%A9valuation%20fonci%C3%A8re&en=page_view&tfd=5789

FINAL URL WHERE THE ADRESSES AND DATA COMES FROM : Request URL
https://montreal.ca/_next/data/info-recherche-2-3-13/fr-CA/role-evaluation-fonciere/adresse/liste.json

Request Method
GET
Status Code
200 OK
Remote Address
104.18.6.89:443
Referrer Policy
strict-origin-when-cross-origin

—--------------------

ELEMENTS :

Numéro d immeuble :

<label data-test="label" id="«rt»" for="radix-«rs»" data-invalid="true">Numéro d'immeuble</label>

<div class="_TextInput-small_o1hr5_21 input-group-icon"><input data-test="input" required="" maxlength="6" pattern="^[0-9]{1,5}([a-zA-Z]{0,1})$" title="" id="radix-«rs»" class="form-control is-invalid" name="civicNumber" aria-describedby="radix-«ru» radix-«r15»" fdprocessedid="8nk3al" data-gtm-form-interact-field-id="1" data-invalid="true"><button type="button" data-test="clear" hidden="" class="btn-clear"><span data-test="icon" aria-hidden="true" focusable="false" class="icon icon-md icon-x-circle"></span><span style="position: absolute; border: 0px; width: 1px; height: 1px; padding: 0px; margin: -1px; overflow: hidden; clip: rect(0px, 0px, 0px, 0px); white-space: nowrap; overflow-wrap: normal;">Supprimer le texte saisi</span></button></div> <input data-test="input" required="" maxlength="6" pattern="^[0-9]{1,5}([a-zA-Z]{0,1})$" title="" id="radix-«rs»" class="form-control is-invalid" name="civicNumber" aria-describedby="radix-«ru» radix-«r15»" fdprocessedid="8nk3al" data-gtm-form-interact-field-id="1" data-invalid="true">

<span id="radix-«r15»" data-test="invalid" class="invalid-feedback is-invalid"><span data-test="icon" aria-hidden="true" focusable="false" class="icon icon-xs icon-exclamation"></span><span style="position: absolute; border: 0px; width: 1px; height: 1px; padding: 0px; margin: -1px; overflow: hidden; clip: rect(0px, 0px, 0px, 0px); white-space: nowrap; overflow-wrap: normal;">Erreur</span>Le numéro d'immeuble est requis.</span>

Nom de la rue :

<span id="radix-«r11»" data-test="help" class="form-text">Entrez le nom de la rue et faites une sélection.</span>

<div data-test="combobox" class="_Root_1ssad_1"><div class="input-group-icon input-group-icon-left"><input data-test="input" required="" aria-busy="false" role="combobox" autocomplete="off" aria-autocomplete="list" aria-haspopup="true" aria-expanded="false" title="" id="radix-«rv»" class="form-control is-invalid" value="" name="streetNameCombobox" fdprocessedid="os361qh" data-gtm-form-interact-field-id="2" data-invalid="true"><span data-test="icon" aria-hidden="true" class="icon icon-color-neutral-stroke icon-search"></span><button type="button" data-test="clear" hidden="" class="btn-clear"><span data-test="icon" aria-hidden="true" focusable="false" class="icon icon-md icon-x-circle"></span><span style="position: absolute; border: 0px; width: 1px; height: 1px; padding: 0px; margin: -1px; overflow: hidden; clip: rect(0px, 0px, 0px, 0px); white-space: nowrap; overflow-wrap: normal;">Supprimer le texte saisi</span></button></div><div data-test="listbox" class="_Content_1ssad_15 dropdown-menu _Root_1lysn_1" style="top: auto; bottom: 100%; max-height: calc(437.333px - 0.5rem);"></div><input type="hidden" value="" name="streetGeneric"><input type="hidden" value="" name="streetName"><input type="hidden" value="" name="noCity"><input type="hidden" value="" name="boroughNumber"><input type="hidden" value="" name="streetNameOfficial"></div> <div class="input-group-icon input-group-icon-left"><input data-test="input" required="" aria-busy="false" role="combobox" autocomplete="off" aria-autocomplete="list" aria-haspopup="true" aria-expanded="false" title="" id="radix-«rv»" class="form-control is-invalid" value="" name="streetNameCombobox" fdprocessedid="os361qh" data-gtm-form-interact-field-id="2" data-invalid="true"><span data-test="icon" aria-hidden="true" class="icon icon-color-neutral-stroke icon-search"></span><button type="button" data-test="clear" hidden="" class="btn-clear"><span data-test="icon" aria-hidden="true" focusable="false" class="icon icon-md icon-x-circle"></span><span style="position: absolute; border: 0px; width: 1px; height: 1px; padding: 0px; margin: -1px; overflow: hidden; clip: rect(0px, 0px, 0px, 0px); white-space: nowrap; overflow-wrap: normal;">Supprimer le texte saisi</span></button></div> <input data-test="input" required="" aria-busy="false" role="combobox" autocomplete="off" aria-autocomplete="list" aria-haspopup="true" aria-expanded="false" title="" id="radix-«rv»" class="form-control is-invalid" value="" name="streetNameCombobox" fdprocessedid="os361qh" data-gtm-form-interact-field-id="2" data-invalid="true">

cliquer sur bouton rechercher :

<button data-test="submit" form="«R6»" type="submit" class="btn-squared btn btn-primary" fdprocessedid="zlzwzw">Rechercher</button>

sélectionner une adresse : cliquer sur adresse

<dl class="dl-list separator"><dt>Adresse</dt><dd>1463 Rue Bishop (Montréal)</dd></dl> <ul data-test="list-group" class="_Root_piya8_1 list-group list-group-teaser list-group-complex"><li data-test="item" tabindex="0" class="focus:informative list-group-item list-group-item-action" role="listitem"><div class="row no-gutters"><div class="col"><div class="row no-gutters"><div class="col"><div data-test="title" class="list-group-item-title"><dl class="dl-list separator"><dt>Adresse</dt><dd>1463 Rue Bishop (Montréal)</dd></dl></div><div data-test="content" class="list-group-item-content empty-placeholder"><dl class="dl-list separator font:sm"><div><dt>Numéro de compte foncier</dt><dd>30 - F26131400</dd></div><div><dt>Numéro de matricule</dt><dd>9839-77-3228-4-000-0000</dd></div></dl></div></div></div></div><div class="col-auto ml-2"><div data-test="action-list" class="list-group-actions"><form method="post" action="/role-evaluation-fonciere/adresse/liste/resultat"><input type="hidden" value="1036820" name="evalUnitId"><button data-test="button" type="submit" class="btn-squared btn-icon btn btn-link"><span data-test="icon" aria-hidden="true" focusable="false" class="icon icon-md icon-chevron-right"></span><span style="position: absolute; border: 0px; width: 1px; height: 1px; padding: 0px; margin: -1px; overflow: hidden; clip: rect(0px, 0px, 0px, 0px); white-space: nowrap; overflow-wrap: normal;">Soumettre</span></button></form></div></div></div></li></ul> <li data-test="item" tabindex="0" class="focus:informative list-group-item list-group-item-action" role="listitem"><div class="row no-gutters"><div class="col"><div class="row no-gutters"><div class="col"><div data-test="title" class="list-group-item-title"><dl class="dl-list separator"><dt>Adresse</dt><dd>1463 Rue Bishop (Montréal)</dd></dl></div><div data-test="content" class="list-group-item-content empty-placeholder"><dl class="dl-list separator font:sm"><div><dt>Numéro de compte foncier</dt><dd>30 - F26131400</dd></div><div><dt>Numéro de matricule</dt><dd>9839-77-3228-4-000-0000</dd></div></dl></div></div></div></div><div class="col-auto ml-2"><div data-test="action-list" class="list-group-actions"><form method="post" action="/role-evaluation-fonciere/adresse/liste/resultat"><input type="hidden" value="1036820" name="evalUnitId"><button data-test="button" type="submit" class="btn-squared btn-icon btn btn-link"><span data-test="icon" aria-hidden="true" focusable="false" class="icon icon-md icon-chevron-right"></span><span style="position: absolute; border: 0px; width: 1px; height: 1 px; padding: 0px; margin: -1px; overflow: hidden; clip: rect(0px, 0px, 0px, 0px); white-space: nowrap; overflow-wrap: normal;">Soumettre</span></button></form></div></div></div></li> <div class="row no-gutters"><div class="col"><div class="row no-gutters"><div class="col"><div data-test="title" class="list-group-item-title"><dl class="dl-list separator"><dt>Adresse</dt><dd>1463 Rue Bishop (Montréal)</dd></dl></div><div data-test="content" class="list-group-item-content empty-placeholder"><dl class="dl-list separator font:sm"><div><dt>Numéro de compte foncier</dt><dd>30 - F26131400</dd></div><div><dt>Numéro de matricule</dt><dd>9839-77-3228-4-000-0000</dd></div></dl></div></div></div></div><div class="col-auto ml-2"><div data-test="action-list" class="list-group-actions"><form method="post" action="/role-evaluation-fonciere/adresse/liste/resultat"><input type="hidden" value="1036820" name="evalUnitId"><button data-test="button" type="submit" class="btn-squared btn-icon btn btn-link"><span data-test="icon" aria-hidden="true" focusable="false" class="icon icon-md icon-chevron-right"></span><span style="position: absolute; border: 0px; width: 1px; height: 1px; padding: 0px; margin: -1px; overflow: hidden; clip: rect(0px, 0px, 0px, 0px); white-space: nowrap; overflow-wrap: normal;">Soumettre</span></button></form></div></div></div> <div class="col"><div class="row no-gutters"><div class="col"><div data-test="title" class="list-group-item-title"><dl class="dl-list separator"><dt>Adresse</dt><dd>1463 Rue Bishop (Montréal)</dd></dl></div><div data-test="content" class="list-group-item-content empty-placeholder"><dl class="dl-list separator font:sm"><div><dt>Numéro de compte foncier</dt><dd>30 - F26131400</dd></div><div><dt>Numéro de matricule</dt><dd>9839-77-3228-4-000-0000</dd></div></dl></div></div></div></div> <div class="col-auto ml-2"><div data-test="action-list" class="list-group-actions"><form method="post" action="/role-evaluation-fonciere/adresse/liste/resultat"><input type="hidden" value="1036820" name="evalUnitId"><button data-test="button" type="submit" class="btn-squared btn-icon btn btn-link"><span data-test="icon" aria-hidden="true" focusable="false" class="icon icon-md icon-chevron-right"></span><span style="position: absolute; border: 0px; width: 1px; height: 1px; padding: 0px; margin: -1px; overflow: hidden; clip: rect(0px, 0px, 0px, 0px); white-space: nowrap; overflow-wrap: normal;">Soumettre</span></button></form></div></div></div>

<button data-test="submit" form="«R6»" type="submit" class="btn-squared btn btn-primary" fdprocessedid="zlzwzw">Rechercher</button>

end page with relevant data (owner info, etc…)

{ … (keep the big JSON with sections/owners/caracteristiques/etc exactly as you shared) … }

To login into account :

where to click when entering montreal.ca

<button type="button" class="btn navbar-btn navbar-btn-icon btn-login btn-hide-label-md d-lg-inline-flex" id="shell-login-button" aria-label="Mon compte"><span class="icon icon-user-circle" aria-hidden="true"></span><span class="btn-label">Mon compte</span></button>

<span class="icon icon-user-circle" aria-hidden="true"></span>

<span class="btn-label">Mon compte</span>

where to enter email :

<input type="text" id="signInName" autofocus="" aria-describedby="signInName-error" fdprocessedid="xqic1a">

where to enter password :

<input type="password" id="password" autocomplete="current-password" aria-required="true" aria-describedby="password-error" fdprocessedid="3o0tfw">

where to click after putting login info to login :

<button id="next" type="submit" form="localAccountForm" fdprocessedid="pmstej">Me connecter</button>

Final note for Codex

Generate all files, wire the CLI, and make sure CSV overwrite + Sheets update in-row + snapshot export are working out of the box.

Add README.md explaining Google service account setup and Playwright install (playwright install).

Include unit tests for parsers.py (given the selectors) with sample HTML snippets.

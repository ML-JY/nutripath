# NutriPath: Nutrigenomic Recipe Explorer

A Flask + vanilla HTML/CSS/JavaScript MVP with local CSV data and Plotly.js.
The flow is pathway emphasis → bioactive compounds → cuisine-tagged ingredients
→ recipe concepts. Calories do not influence recommendations.

**Educational research demo only. Not medical advice, diagnosis, treatment, or
an individualized diet recommendation. Cannot replace a clinician or registered
dietitian.** This custom Nutri-Score is unrelated to the front-of-pack food label.

## Local start

Use Python 3.11 or later, then run from this directory:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Windows activation: `.venv\Scripts\activate`. Open http://127.0.0.1:5000.
Run checks with `python -m unittest discover -s tests -v`.

Routes: `/` overview; `/preferences` SNP panel; `/dashboard` results;
`/recipes` recipe output. The latter three share the live explorer to keep
controls and current results accessible. POST JSON to `/api/recommend` or
`/api/export`:

```json
{"snps":["MTHFR"],"diet":"vegan_nuts","cuisine":"Chinese","priority":50,"sensitivity":50,"flavor":65}
```

No file uploads, accounts, external scientific API calls, or database server.
Plotly is loaded from a pinned CDN URL. Without that CDN, rankings and recipes
still work and the interface reports unavailable charts.

## Data and evidence

`database.csv` has one row per ingredient–compound–gene edge. Cuisine tags use
`|`; overlapping tags are allowed. 48 ingredients and 49 edges are provided across Chinese, Western, Thai, Japanese, Indian, Spanish, and British cuisines.
Columns include signed gene weights, SNP factors, dimensionless concentrations,
pathway, effect, cooking-loss fraction, restrictions, recipe role, preparation,
cuisine-affinity scores, USDA reference energy and FDC ID, PMID, evidence level, food category, allergens, serving grams, and method-specific preparation and loss columns. New pantry items have blank USDA metadata pending curation; blank values never mean zero calories.

USDA energy metadata is rounded kcal/100 g for the referenced food form:
cooked brown rice, firm calcium-set tofu, raw vegetables and walnuts, and raw
farmed Atlantic salmon. It is reference metadata, not a calculated recipe total.
Food forms and preparation change real nutrient values. FDC records can be
opened with `https://fdc.nal.usda.gov/food-details/<usda_fdc_id>/nutrients`.
See [USDA documentation](https://fdc.nal.usda.gov/data-documentation/).
USDA does **not** supply the hypothetical molecular indices or gene weights.

All `compound_concentration` values are **synthetic normalized abundance indices
per 100 g**, not measured mg or µg. Isoflavone, carotenoid, glucosinolate and
omega-3 labels include compound-class proxies. Coefficients, SNP modifiers,
cooking degradation and cuisine-affinity values are author-assigned demo values.
The model needs curated quantitative measurements and validation before research
use beyond demonstration. Do not mix measured concentrations with these indices.

Background references (not validation of numerical weights or recipes):

- [PMID 25788000](https://pubmed.ncbi.nlm.nih.gov/25788000/): systematic review
  of MTHFR 677C>T and blood folate concentrations.
- [PMID 15100171](https://pubmed.ncbi.nlm.nih.gov/15100171/): laboratory COMT
  inhibition by tea catechins and bioflavonoids, including quercetin. This is not
  evidence that eating onion produces the modeled effect.
- [PMID 25332476](https://pubmed.ncbi.nlm.nih.gov/25332476/): APOE and responses
  to meals differing in fat composition. It does not establish a salmon/ALA
  prescription or direct APOE activation.

Blank PMIDs explicitly mean pending validation. Every recipe includes a
recipe-specific PMID placeholder, rather than a fabricated citation. Graph
activation labels include hypothetical indirect support and should not be read
as experimentally demonstrated transcriptional activation. Inhibition does not
automatically mean harm; the negative sign is a modeling convention.

## Score definition

For each eligible ingredient, sum its compound–gene rows:

```text
base = concentration_index × signed_gene_weight × SNP_factor × pathway_weight
allergen_penalty = 1000 if nut restriction matches else 0
cooking_penalty = max(base, 0) × cooking_loss_fraction × sensitivity / 100
NutriScore = Σ(base − allergen_penalty − cooking_penalty)
```

Allergic and non-vegan ingredients are hard-excluded from results and recipes
before ranking, even if their hypothetical score could overcome a penalty.
Thus eligible ingredients have zero allergen penalty. The cooking penalty
reduces modeled positive contributions, never rewards destruction of inhibitors.
Sensitivity changes penalty strength, not temperature, method, or actual loss.
Each CSV preparation matches its assumed loss fraction; those fractions have
not been experimentally validated.

A single pathway slider cannot independently set three dimensions. Its defined
trajectory is methylation at 0, antioxidant at 50, and lipid at 100, with linear
interpolation and a 10% floor for each pathway:

```text
x = priority / 100
raw = [max(0, 1−2x), 1−abs(2x−1), max(0, 2x−1)]
weights = 0.1 + 0.7 × raw                 # sum = 1
science_rank = 50 + 50 × tanh(NutriScore / 50)
blended_rank = flavor/100 × science_rank + (1−flavor/100) × cuisine_affinity
```

At flavor 100, ranking is monotonic in Nutri-Score; at 0, only manually assigned
cuisine affinity drives ranking, with Nutri-Score as tie-breaker. The interface
shows both scores separately. Flavor never changes Nutri-Score itself.
Recipes take the highest-ranked eligible base, protein, vegetable, and an extra
vegetable/garnish, plus cuisine-specific seasonings and explicit cooking oil when required. Protein-family preferences constrain only the protein role. A second recipe uses an alternative vegetable and extra when distinct.
These are cuisine-inspired dishes, not claims of authentic traditional cooking. Each cuisine has distinct staples, seasonings, and a default method, with optional method overrides.
Shared ingredients are deliberately tagged for multiple cuisines; Thai excludes
walnuts in this small dataset. All named ingredients come from the eligible set.

The graph shows the first recipe's compound–gene edges; width follows absolute
serving-adjusted weighted contribution. The radar sums the first recipe's signed contributions
by pathway after scaling each ingredient by its serving grams / 100, then plots `100 × tanh(max(0, sum) / 100)` on a fixed 0–100 scale.
Negative support totals clip to zero. Neither chart represents measured gene
expression or a percent of nutritional requirements. Recipe scores sum per-food
indices multiplied by serving grams / 100. These are still synthetic indices, not biological efficacy. Slider events recompute all
outputs; discrete recipe selections need not change on every single increment.

## Genetic presets and privacy

Checkboxes represent presence, not allele dosage: MTHFR rs1801133 T (CT/TT),
COMT rs4680 A (GA/AA), and a known APOE ε4 haplotype. APOE ε4 involves rs429358
and rs7412; this app does not infer haplotypes from single SNP calls. Unchecked
means unknown/unmodeled, not a negative test. SNP-to-pathway demand is a toy
assumption and cannot diagnose deficiency or metabolic need.

Inputs persist in this browser tab's sessionStorage for navigation; Reset clears
the selected presets. Inputs are sent in POST bodies for calculation, not stored
server-side, placed in query strings, or exported as genotype data. Flask itself
does not log request bodies; review any host/proxy logging policy before using
real genetic information. No real genetic information is needed for this demo.

## Limitations

Small curated demonstration dataset; mixed population-level and in-vitro evidence
only. No individual clinical validation, ancestry calibration, dose response,
bioavailability, genotype dosage, gene–gene interactions, medication interactions,
nutrient adequacy checks, or long-term outcome prediction. Cooking can increase
bioaccessibility or generate new compounds, which a loss-only model omits.
Nut flags do not assess cross-contact or other allergens; tofu contains soy and
salmon is fish. Check product labels. Recipe references are background sources,
not scientific validation of personalized dietary benefit.

## GitHub and Render deployment

1. Create a GitHub repository and commit the contents of this directory at its
   root. Do not commit `.venv` or personal genetic data.
2. On Render, create a **Web Service** connected to that repository. Select
   Python and a free instance if available for your account.
3. Build command: `pip install -r requirements.txt`.
4. Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`.
5. Deploy. Test the four routes, cuisine/restriction switches, sliders, and CSV
   export on the assigned HTTPS address. If you committed the enclosing folder,
   set Render's Root Directory to `nutripath`.

Alternatively use Render's Blueprint flow with the included `render.yaml` when
these files are at repository root. No secrets or external database are needed.
Free-service cold starts can make the first calculation slower.
See [Render's Flask guide](https://render.com/docs/deploy-flask).

## GitHub Pages deployment

GitHub Pages serves static files and cannot execute Flask/Python. Deploy the
working app to Render; use Pages for a project landing page linking to it.
This preserves a single origin and requires no CORS configuration. Do not upload
Jinja templates as working static pages.

For an optional Pages landing page, create `docs/index.html`, replacing the
example Render URL with your assigned URL:

```html
<!doctype html>
<html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NutriPath</title>
<h1>NutriPath: Nutrigenomic Recipe Explorer</h1>
<p>Explore a transparent nutrigenomics demonstration.</p>
<p><a href="https://YOUR-SERVICE.onrender.com">Open the interactive app</a></p>
<p>Educational research demo only. Not medical advice, diagnosis, treatment, or
an individualized diet recommendation. Cannot replace a clinician or registered dietitian.</p>
</html>
```

Commit that file. In GitHub **Settings → Pages**, select **Deploy from a branch**,
then your branch and `/docs`. Save and open the published Pages URL. The landing
page is static; the interactive app continues to run on Render.
See [GitHub Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site).

## Expanded choices and cooking methods

- Seven cuisines: Chinese, Western, Thai, Japanese, Indian, Spanish, British.
- Dietary patterns: everything, vegetarian, vegan, pescatarian, nut-free, vegan + nut-free.
- Independent exclusions: nuts, gluten, dairy, soy, eggs, fish, sesame. Multiple selections combine as hard exclusions. Pescatarian excludes meat, but the current dataset has no meat or poultry to begin with.
- Protein families: any, beans/lentils/tofu, fish, eggs, dairy. A conflict such as vegan + fish yields no recipe and a clear explanation; restrictions are never silently relaxed.
- Cooking: cuisine favorite, gentle steaming, pan sauté, oven roasting, gentle simmering. Every CSV edge has `prep_<method>` and `loss_<method>` fields. The default cuisine method is resolved in `recipes.py`.
- Pantry browsing: the ingredient shelf contains 300 searchable food forms and 100 flavor/spice choices. Selected foods are hard requirements in the generated recipe, including cross-cuisine adaptations; a food-group dropdown filters the ranking table only.
- Dish choice: the preferences page offers 350 recognizable dish variations (50 each across Chinese, Western, Thai, Japanese, Indian, Spanish, and British cuisines). Choose a dish family first, then let the molecular model adapt the exact shelf ingredients to it.
- Expand an ingredient to inspect its concentration index, signed gene weight, SNP factor, pathway weight, cooking loss, contribution, USDA metadata, and background evidence status.

Method loss fractions are deliberately synthetic. Relative to the seed steam fraction, sauté uses 1.15×, roasting 1.5×, and simmering 1.35× (capped at 0.85). Seasonings, uncooked garnishes, oils, and already-cooked grains retain the same specified fraction across methods. This is an illustrative contrast, not a claim that one method universally preserves more nutrients. Cooking can increase bioaccessibility and different food forms require different evidence.

Heat instructions vary by ingredient group, including different times for roots and leafy greens. Grains and legumes labeled cooked must already be fully cooked. Fish instructions require 63°C / 145°F in the center; egg instructions require 71°C / 160°F. Optional aromatics are prepared separately, so they can be omitted by restrictions without referencing excluded sauce ingredients. Added cooking oil is listed in the CSV, ingredient list, and score.

The primary data source remains `database.csv`; the server makes no external scientific API requests. Cuisine configuration and recipe assembly live in `recipes.py`. Molecular scoring and JSON validation live in `app.py`.

## Artwork

Original images were made with the built-in image-generation tool and saved in `static/food-journal.png` and `static/cuisine-studies.png`. The latter is a 4×2 contact sheet displayed as CSS background tiles, not eight downloads. Artwork is labeled serving inspiration; it does not depict each dynamically generated recipe exactly. Prompts are recorded in `ARTWORK.md`.

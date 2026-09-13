"""NutriPath — README quick start: pip install -r requirements.txt; python app.py.

GitHub: commit this directory; Render: gunicorn app:app. See README.md for
methodology and hosting. Educational model only; never clinical advice.
All compound concentrations are dimensionless DEMO indices, not lab measurements.
"""
import csv
import io
import math
from pathlib import Path

from flask import Flask, jsonify, render_template, request, Response, redirect
from recipes import CUISINE_INFO, METHODS, DIETS, EXCLUSIONS, PROTEINS, GROUPS, DISH_OPTIONS, DISH_BY_ID, make_recipes
from catalog import food_catalog, flavor_catalog, selected_food_records

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024
ROOT = Path(__file__).resolve().parent
CUISINES = tuple(CUISINE_INFO)
PATHWAYS = ('Methylation', 'Antioxidant', 'Lipid')
SNPS = {
    'MTHFR': 'MTHFR rs1801133 — T allele present (CT/TT)',
    'COMT': 'COMT rs4680 — A allele present (GA/AA)',
    'APOE': 'APOE ε4 carrier — known haplotype (two loci)',
}
DISCLAIMER = ('Educational research demo only. Not medical advice, diagnosis, '
              'treatment, or an individualized diet recommendation. '
              'Cannot replace a clinician or registered dietitian.')
COOKING_METHODS = ['raw','steaming','boiling','poaching','simmering','stewing','pressure cooking','slow cooking','baking','roasting','grilling','broiling','air frying','pan sauté','stir frying','wok cooking','braising','smoking','fermenting','pickling','dehydrating','sun drying','microwaving','blanching','parboiling','flash frying','deep frying','chargrilling','barbecuing','tempura frying','confit']
with (ROOT / 'database.csv').open(newline='', encoding='utf-8') as source:
    DATABASE = list(csv.DictReader(source))


def preferences(data):
    """Reject malformed requests instead of silently accepting unknown variants."""
    if not isinstance(data, dict):
        raise ValueError('Expected a JSON object.')
    cuisine = data.get('cuisine', 'Chinese')
    diet = data.get('diet', 'none')
    snps = data.get('snps', [])
    if not isinstance(cuisine, str) or cuisine not in CUISINES or not isinstance(diet, str) or diet not in DIETS:
        raise ValueError('Unknown cuisine or dietary restriction.')
    if (not isinstance(snps, list) or any(not isinstance(s, str) or s not in SNPS for s in snps)
            or len(snps) != len(set(snps))):
        raise ValueError('Choose only the listed variant presets, without duplicates.')
    exclusions = data.get('exclusions', [])
    if not isinstance(exclusions, list) or any(not isinstance(e, str) or e not in EXCLUSIONS for e in exclusions):
        raise ValueError('Choose only the listed ingredient exclusions.')
    method, protein = data.get('method', 'auto'), data.get('protein', 'any')
    if not isinstance(method, str) or method not in METHODS or not isinstance(protein, str) or protein not in PROTEINS:
        raise ValueError('Unknown cooking method or protein preference.')
    dish = data.get('dish') or next(d['id'] for d in DISH_OPTIONS if d['cuisine'] == cuisine)
    if not isinstance(dish, str) or dish not in DISH_BY_ID or DISH_BY_ID[dish]['cuisine'] != cuisine:
        raise ValueError('Choose a dish from the selected cuisine.')
    result = dict(cuisine=cuisine, diet=diet, snps=snps, exclusions=sorted(set(exclusions)),
                  method=method, protein=protein,
                  dish=dish,
                  resolved_method=CUISINE_INFO[cuisine]['method'] if method == 'auto' else method,
                  selected_foods=data.get('selected_foods', []), selected_flavors=data.get('selected_flavors', []))
    if (not isinstance(result['selected_foods'], list) or not isinstance(result['selected_flavors'], list)
            or any(not isinstance(x, str) for x in result['selected_foods'] + result['selected_flavors'])):
        raise ValueError('Selected foods and flavors must be text IDs.')
    for name, default in [('priority', 50), ('sensitivity', 50), ('flavor', 65)]:
        value = data.get(name, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f'{name} must be a number from 0 to 100.')
        if not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError(f'{name} must be between 0 and 100.')
        result[name] = value
    return result


def pathway_weights(priority):
    """One slider traces a simplex: methylation -> antioxidant -> lipid.

    A 10% floor keeps every pathway represented; weights always sum to 1.
    This is a constrained three-way balance, not three independent controls.
    """
    x = priority / 100
    raw = (max(0, 1 - 2*x), 1 - abs(2*x - 1), max(0, 2*x - 1))
    return dict(zip(PATHWAYS, [0.1 + 0.7*w for w in raw]))


def calculate(p):
    weights = pathway_weights(p['priority'])
    ingredients = {}
    excluded = set()
    selected_bases = {sid.rsplit('-', 1)[0].replace('-', ' ').lower() for sid in p['selected_foods']}
    for row in DATABASE:
        row_base = row['ingredient'].lower()
        selected_override = row_base in selected_bases or row_base.rstrip('s') in selected_bases
        # An explicit shelf selection is a deliberate cuisine adaptation. It
        # remains eligible even when the seed tag is missing that cuisine.
        if p['cuisine'] not in row['cuisine_tags'].split('|') and not selected_override:
            continue
        # Hard exclusion prevents a high scientific score overriding an allergy.
        blocked = set(p['exclusions'])
        if 'nuts' in p['diet']:
            blocked.add('nuts')
        allergic = bool(blocked.intersection(row['allergens'].split('|')))
        nonvegan = ('vegan' in p['diet'] and row['vegan'] != '1') or (
            p['diet'] == 'vegetarian' and row['category'] == 'fish')
        allergen_penalty = 1000.0 if allergic else 0.0
        factor = float(row['snp_impact_weight']) if row['snp_gene'] in p['snps'] else 1.0
        base = (float(row['compound_concentration']) * float(row['gene_regulation_weight'])
                * factor * weights[row['pathway']])
        # Penalize lost positive benefit only: destroying an inhibitor is not
        # claimed to improve health. Signed inhibition remains a negative term.
        loss = max(base, 0) * float(row['loss_' + p['resolved_method']]) * p['sensitivity']/100
        contribution = base - allergen_penalty - loss
        if allergic or nonvegan:
            excluded.add(row['ingredient'])
            continue
        item = ingredients.setdefault(row['ingredient'], dict(
            name=row['ingredient'], score=0, cooking_penalty=0, allergen_penalty=0,
            flavor=float(row['flavor_' + p['cuisine'].lower()]) or (72.0 if selected_override else 0.0),
            role=row['role'], category=row['category'], group=GROUPS[row['category']],
            serving_g=float(row['serving_g']), allergens=row['allergens'],
            preparation=row['prep_' + p['resolved_method']],
            kcal_per_100g=float(row['usda_kcal_per_100g']) if row['usda_kcal_per_100g'] else None,
            usda_id=row['usda_fdc_id'],
            pathways=dict.fromkeys(PATHWAYS, 0.0), interactions=[]))
        item['score'] += contribution
        item['cooking_penalty'] += loss
        item['pathways'][row['pathway']] += contribution
        item['interactions'].append(dict(
            compound=row['compound'], gene=row['target_gene'], effect=row['effect'],
            description=row['evidence_note'], pmid=row['pmid'], value=contribution,
            evidence=row['evidence_level'], concentration=float(row['compound_concentration']),
            gene_weight=float(row['gene_regulation_weight']), snp_factor=factor,
            pathway=row['pathway'], pathway_weight=weights[row['pathway']],
            cooking_loss=float(row['loss_' + p['resolved_method']]), cooking_penalty=loss, base=base))
    ranked = list(ingredients.values())
    # Fixed scale avoids min-max changes caused solely by filter membership.
    # Nutri-Score is preserved; flavor affects a separately labeled rank score.
    for item in ranked:
        scientific = 50 + 50 * math.tanh(item['score']/50)
        f = p['flavor']/100
        selected_bonus = 10 if item['name'].lower() in selected_bases else 0
        item['rank_score'] = f*scientific + (1-f)*item['flavor'] + selected_bonus
        # Ingredient-level preview uses only locally stored metadata.
        item['nutrition_score'] = round(max(1, min(100, (55 if item['kcal_per_100g'] is not None else 35)
                                             + (15 if item['role'] in ('vegetable','legume','base') else 5))), 1)
    ranked.sort(key=lambda item: (-item['rank_score'], -item['score'], item['name']))
    # Selected catalogue foods are explicit requirements. They receive a
    # zero-score placeholder until their molecular evidence is curated, but
    # still appear in recipes exactly as selected.
    selected_names = {r['base'] for r in selected_food_records(p['selected_foods'])}
    known_names = {i['name'].lower().replace(' (cooked)','').replace(' (shelled)','') for i in ranked}
    for record in selected_food_records(p['selected_foods']):
        if record['base'] in known_names or record['base'].rstrip('s') in known_names:
            continue
        if p['exclusions'] and any(x in record['allergens'].split('|') for x in p['exclusions']):
            continue
        if 'nuts' in p['diet'] and 'nuts' in record['allergens']:
            continue
        if 'vegan' in p['diet'] and not record['vegan']:
            continue
        ranked.append(dict(name=record['name'], score=0.0, cooking_penalty=0.0,
                           allergen_penalty=0.0, flavor=72.0, rank_score=72.0,
                           role=record['role'], category=record['category'], group=record['group'],
                           serving_g=100.0, allergens=record['allergens'], preparation=f'Prepare 100 g {record["name"].lower()} according to its food-safe package directions.',
                           kcal_per_100g=None, usda_id='', pathways=dict.fromkeys(PATHWAYS, 0.0), interactions=[]))
    ranked.sort(key=lambda item: (-item['rank_score'], -item['score'], item['name']))
    recipes = make_recipes(ranked, p)
    selected = recipes[0]['ingredients'] if recipes else []
    chosen = [item for item in ranked if item['name'] in selected]
    portions = recipes[0]['portions'] if recipes else {}
    # Fixed-scale bounded radar; no implied percentage of biological function.
    support = [100*math.tanh(max(0, sum(i['pathways'][w]*portions[i['name']]/100 for i in chosen))/100)
               for w in PATHWAYS]
    # A separate, transparent 1–100 nutrition preview. It rewards a diverse
    # mix of food groups and USDA energy metadata; it is not a medical rating.
    nutrition_items = chosen or ranked[:6]
    group_count = len({i['category'] for i in nutrition_items})
    evidence_count = sum(i['kcal_per_100g'] is not None for i in nutrition_items)
    diversity = min(35, group_count * 7)
    data_quality = min(35, evidence_count / max(1, len(nutrition_items)) * 35)
    plant_bonus = min(20, sum(i['role'] in ('vegetable', 'base', 'legume', 'garnish') for i in nutrition_items) * 4)
    nutrition_score = round(max(1, min(100, 10 + diversity + data_quality + plant_bonus)), 1)
    nutrition = dict(score=nutrition_score, scale='1–100', groups=group_count,
                     USDA_items=evidence_count,
                     note='Educational nutrition preview based on food-group variety and available USDA energy metadata; it is not a nutrient adequacy or health diagnosis.')
    return dict(preferences=p, weights=weights, ranked=ranked, recipes=recipes,
                support=support, pathways=PATHWAYS, graph_ingredients=selected,
                excluded_count=len(excluded), disclaimer=DISCLAIMER, graph_portions=portions,
                cuisine_info=CUISINE_INFO[p['cuisine']], method_label=METHODS[p['resolved_method']],
                groups={i['category']:i['group'] for i in ranked}, nutrition=nutrition)


@app.context_processor
def shared():
    return dict(disclaimer=DISCLAIMER, cuisines=CUISINES, snps=SNPS,
                cuisine_info=CUISINE_INFO, methods=METHODS, diets=DIETS, exclusions=EXCLUSIONS,
                proteins=PROTEINS, dishes=DISH_OPTIONS, cooking_methods=COOKING_METHODS,
                food_count=len(food_catalog()), flavor_count=len(flavor_catalog()))


@app.get('/')
def home():
    return render_template('home.html', page='home')


@app.get('/preferences')
@app.get('/dashboard')
@app.get('/recipes')
def retired_recipe_pages():
    """Legacy bookmarks now land on the ingredient nutrition calculator."""
    return redirect('/ingredients', code=302)


@app.get('/ingredients')
def ingredients():
    return render_template('ingredients.html', page='ingredients')

@app.get('/plate')
def plate():
    return render_template('plate.html', page='plate')

@app.get('/cooking')
def cooking_science():
    return render_template('cooking.html', page='cooking')

@app.get('/suggestions')
def suggestions():
    meals = {
      'Chinese':['Ginger tofu with bok choy and brown rice','Steamed salmon, edamame and greens','Mushroom vegetable stir-fry with jasmine rice','Lentil and cabbage congee'],
      'Western':['Roasted salmon, broccoli and quinoa','Lentil ratatouille with whole-grain bread','Greek yogurt, berries and oats','White bean vegetable stew'],
      'Thai':['Lime tofu curry with vegetables','Tom yum-style shrimp and rice','Basil chicken with green beans','Coconut lentil soup with herbs'],
      'Japanese':['Miso salmon with edamame and rice','Soba noodles with tofu and vegetables','Sushi-style bowl with tuna and cucumber','Mushroom nabe with greens'],
      'Indian':['Chana masala with brown rice','Dal, spinach and whole-grain roti','Aloo gobi with lentils','Palak paneer with cucumber salad'],
      'Spanish':['White bean and tomato stew','Paella-style brown rice with vegetables','Gazpacho with chickpea salad','Grilled sardines with peppers'],
      'British':['Pea and mint soup with whole-grain toast','Roast salmon, potatoes and greens','Lentil shepherd\'s pie','Bean and vegetable cottage pie']}
    selected = request.args.get('cuisine')
    if selected in meals:
        meals = {selected: meals[selected]}
    return render_template('suggestions.html', page='suggestions', meals=meals, selected_cuisine=selected if selected in meals else None)

@app.get('/journey')
def nutrient_journey():
    return render_template('journey.html', page='journey')

@app.get('/principles')
def principles():
    return render_template('principles.html', page='principles')


@app.get('/api/catalog')
def catalog():
    foods, flavors = food_catalog(), flavor_catalog()
    return jsonify(foods=foods, flavors=flavors, food_count=len(foods), flavor_count=len(flavors))


@app.post('/api/recommend')
def recommend():
    return jsonify(calculate(preferences(request.get_json(silent=True))))


@app.post('/api/export')
def export():
    report = calculate(preferences(request.get_json(silent=True)))
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['NutriPath recipe report', DISCLAIMER])
    # Genetic selections intentionally omitted from downloaded reports.
    p = report['preferences']
    writer.writerow(['Cuisine', p['cuisine'], 'Diet', p['diet'], 'Pathway slider', p['priority'],
                     'Sensitivity', p['sensitivity'], 'Flavor flexibility', p['flavor'],
                     'Method', p['resolved_method'], 'Dish', DISH_BY_ID[p['dish']]['name'],
                     'Protein', p['protein'], 'Exclusions', '; '.join(p['exclusions'])])
    writer.writerow(['Recipe', 'Servings', 'Ingredients', 'Instructions', 'Demo Nutri-Score', 'Background PMIDs', 'Limitations'])
    for r in report['recipes']:
        writer.writerow([r['name'], r['servings'], '; '.join(r['quantities']),
                         ' '.join(r['instructions']), round(r['score'], 3),
                         '; '.join(r['references']), r['limitation']])
    return Response(output.getvalue(), mimetype='text/csv', headers={
        'Content-Disposition': 'attachment; filename=nutripath-recipes.csv'})


@app.errorhandler(ValueError)
def invalid(error):
    return jsonify(error=str(error)), 400


@app.after_request
def privacy(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


if __name__ == '__main__':
    app.run(port=5000)

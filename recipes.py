"""Cuisine structure and recipe assembly, kept separate from molecular scoring."""
CUISINE_INFO = {
    'Chinese': {'index':0, 'note':'Ginger, bok choy & savory soy', 'method':'saute', 'title':'Ginger garden rice', 'finish':'Serve the vegetables and protein over rice. Spoon over the ginger dressing.'},
    'Western': {'index':1, 'note':'Lemon, whole grains & olive oil', 'method':'roast', 'title':'Lemon harvest plate', 'finish':'Arrange the grain, protein and vegetables on a plate. Finish with the lemon dressing.'},
    'Thai': {'index':2, 'note':'Coconut, lime & fragrant basil', 'method':'simmer', 'title':'Coconut–lime garden bowl', 'finish':'Serve over rice with the coconut dressing. Fold in the lime and Thai basil just before eating.'},
    'Japanese': {'index':3, 'note':'Miso, edamame & crisp nori', 'method':'steam', 'title':'Garden donburi', 'finish':'Arrange the toppings on rice. Add any selected miso dressing and finish with nori strips.'},
    'Indian': {'index':4, 'note':'Chickpeas, cumin & golden turmeric', 'method':'simmer', 'title':'Golden masala bowl', 'finish':'Coat the protein and vegetables in the cumin–turmeric sauce. Serve with the grain; fold in fresh coriander at the end.'},
    'Spanish': {'index':5, 'note':'White beans, peppers & smoked paprika', 'method':'saute', 'title':'Smoky paprika rice', 'finish':'Fold the rice, protein and vegetables together with the paprika seasoning. Serve in a shallow dish.'},
    'British': {'index':6, 'note':'Golden potatoes, peas & garden herbs', 'method':'roast', 'title':'Sunday garden plate', 'finish':'Arrange the potato or grain, protein and vegetables on a warm plate. Finish with the selected garden herbs.'},
}
METHODS = {'auto':'Cuisine favorite', 'steam':'Gentle steaming', 'saute':'Pan sauté', 'roast':'Oven roasting', 'simmer':'Gentle simmering'}
DIETS = {'none':'Everything on the table', 'vegetarian':'Vegetarian', 'vegan':'Vegan', 'pescatarian':'Pescatarian', 'nuts':'Nut-free', 'vegan_nuts':'Vegan + nut-free'}
EXCLUSIONS = {'nuts':'Nuts', 'gluten':'Gluten', 'dairy':'Dairy', 'soy':'Soy', 'egg':'Eggs', 'fish':'Fish', 'sesame':'Sesame'}
PROTEINS = {'any':'Let the recipe choose', 'legume':'Beans, lentils & tofu', 'fish':'Fish', 'egg':'Eggs', 'dairy':'Paneer & dairy'}
GROUPS = {'grain':'Grains', 'root':'Roots & potatoes', 'leafy':'Leafy greens', 'cruciferous':'Cruciferous vegetables', 'vegetable':'Other vegetables', 'legume':'Beans & legumes', 'fish':'Fish', 'egg':'Eggs', 'dairy':'Dairy', 'nuts':'Nuts & seeds', 'herb':'Herbs', 'spice':'Spices', 'sauce':'Sauces', 'oil':'Oils'}

# Familiar dish names keep the chooser approachable while each recipe remains
# a cuisine-inspired adaptation of the user's selected shelf ingredients.
_DISHES = {
    'Chinese': ['Mapo tofu','Chow mein noodles','Yangzhou fried rice','Hot-and-sour soup','Wonton soup','Jiaozi dumplings','Congee','Buddha\'s delight','Kung pao vegetables','Scallion pancakes'],
    'Western': ['Ratatouille','Minestrone','Lemon herb traybake','Harvest grain bowl','Vegetable lasagne','Salmon sheet pan','Stuffed peppers','Mediterranean pasta','Roasted root plate','White bean stew'],
    'Thai': ['Tom yum soup','Green curry','Pad Thai noodles','Thai basil stir-fry','Larb-inspired bowl','Massaman curry','Tom kha soup','Som tam-inspired salad','Red curry','Pineapple fried rice'],
    'Japanese': ['Sushi-inspired bowl','Miso soup','Soba noodle bowl','Salmon donburi','Onigiri plate','Yakisoba noodles','Nabe hot pot','Chirashi bowl','Japanese curry','Agedashi tofu'],
    'Indian': ['Chana masala','Dal tadka','Palak paneer','Vegetable biryani','Aloo gobi','Rajma masala','Sambar','Baingan bharta','Kitchari','Tandoori traybake'],
    'Spanish': ['Paella-inspired rice','Tortilla española','Gazpacho','Escalivada','Fabada-inspired beans','Patatas bravas','Pisto manchego','Spanish lentil stew','Sofrito noodles','White bean tapas bowl'],
    'British': ['Shepherd\'s pie-inspired bowl','Fish pie','Vegetable pasty plate','Cottage pie','Pea and mint soup','Jacket potato','Sunday roast plate','Bubble and squeak','Leek and potato soup','Ploughman\'s plate'],
}
_VARIANTS = ['classic','weeknight','garden','market','spice-forward']
DISH_OPTIONS = [dict(id=f"{c.lower()}-{i}-{v}", name=f'{name} · {variant}', cuisine=c, method=CUISINE_INFO[c]['method'])
                for c, names in _DISHES.items() for i, name in enumerate(names) for v, variant in enumerate(_VARIANTS)]
DISH_BY_ID = {d['id']: d for d in DISH_OPTIONS}


def make_recipes(ranked, p):
    """Rank within culinary roles; never fill a missing role with excluded food."""
    cuisine, method = p['cuisine'], p['resolved_method']
    info = CUISINE_INFO[cuisine]
    selected_bases = {sid.rsplit('-', 1)[0].replace('-', ' ').lower()
                      for sid in p.get('selected_foods', [])}

    def selected(item):
        """Match shelf IDs such as ``carrot-raw`` to scored ingredient names."""
        name = item['name'].lower()
        base = name.rsplit(' (', 1)[0] if ' (' in name else name
        return name in selected_bases or base in selected_bases or base.rstrip('s') in selected_bases

    recipes = []
    for offset in (0, 1, 2, 3):
        chosen = []
        for role in ('base', 'protein', 'vegetable'):
            pool = [i for i in ranked if i['role'] == role and
                    (role != 'protein' or p['protein'] == 'any' or i['category'] == p['protein'])]
            if not pool:
                return []
            preferred = [i for i in pool if selected(i)]
            available = preferred or pool
            chosen.append(available[min(offset, len(available)-1)] if role == 'vegetable' else available[0])
        # Explicit shelf selections are hard requirements, even when they are
        # a cross-cuisine adaptation or a catalogue item without a score.
        for item in ranked:
            if selected(item) and item not in chosen and item['role'] not in ('seasoning', 'cooking_fat'):
                chosen.append(item)
        extras = [i for i in ranked if i not in chosen and i['role'] in ('vegetable', 'garnish')]
        extras.sort(key=lambda i: (not selected(i), -i['rank_score']))
        if extras:
            chosen.append(extras[min(offset, len(extras)-1)])
        # Preserve dependencies in cooking steps even when science ranks change.
        seasoning_order = {'Cumin':0, 'Turmeric':1, 'Garlic':0, 'Smoked paprika':1}
        chosen.extend(sorted((i for i in ranked if i['role'] == 'seasoning'),
                             key=lambda i: (seasoning_order.get(i['name'], 2), i['name'])))
        # Oil is explicitly listed and scored, not an untracked pantry addition.
        if method in ('saute', 'roast'):
            fat = next((i for i in ranked if i['role'] == 'cooking_fat'), None)
            if fat:
                chosen.append(fat)
        names = [i['name'] for i in chosen]
        if any(set(r['ingredients']) == set(names) for r in recipes):
            continue
        portions = {i['name']: i['serving_g'] for i in chosen}
        prelude = {
            'steam':'Set a steamer over gently boiling water. Cook ingredients separately for their listed times.',
            'saute':'Warm the listed cooking oil in a nonstick pan over medium heat. Cook in batches; add a splash of water if needed.',
            'roast':'Heat the oven to 200°C (390°F). Use the listed cooking oil on a lined tray.',
            'simmer':'Bring a shallow pan of water to a gentle simmer. Cook ingredients separately, then drain before combining.',
        }[method]
        if method == 'roast' and any(i['category'] == 'fish' for i in chosen):
            prelude += ' Keep fish separate from vegetables.'
        # Sauce ingredients can be excluded; never mention an excluded sauce.
        preparations = [i['preparation'] for i in chosen if i['role'] != 'cooking_fat']
        excluded_seasoning = p['exclusions'] or p['diet'] in ('nuts', 'vegan_nuts')
        finish = ('Combine the prepared components and the listed seasonings. '
                  'This version adapts the cuisine to your exclusions.') if excluded_seasoning else info['finish']
        main_pathway = max(('Methylation', 'Antioxidant', 'Lipid'), key=lambda w:
                           sum(i['pathways'][w]*portions[i['name']]/100 for i in chosen))
        recipes.append(dict(
            name=f"{DISH_BY_ID.get(p.get('dish'), {}).get('name', info['title'])}: {chosen[2]['name']} & {chosen[1]['name'].rsplit(' (', 1)[0]}",
            cuisine=cuisine, illustration_index=info['index'], ingredients=names,
            servings=1, portions=portions, method=METHODS[method],
            quantities=[f"{i['serving_g']:g} g {i['name']}" for i in chosen],
            instructions=[prelude]+preparations+[finish],
            score=sum(i['score']*portions[i['name']]/100 for i in chosen),
            time='35–45 min' if method=='roast' else '20–30 min',
            why=f"{chosen[2]['name']} and {chosen[1]['name']} fit your settings within their food groups. {main_pathway} has the largest modeled contribution in this serving.",
            references=sorted({e['pmid'] for i in chosen for e in i['interactions'] if e['pmid']}),
            limitation='Cuisine-inspired cooking concept; substitutions and methods are adaptations, not claims of traditional authenticity. '
                       'Score is serving-adjusted but uses synthetic molecular indices. Background studies do not validate this recipe. '
                       'Recipe-specific PMID: pending validation.'))
    return recipes

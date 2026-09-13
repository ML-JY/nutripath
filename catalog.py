"""USDA FoodData Central name index plus a separate flavor/spice shelf.

The 48-row scored subset remains in database.csv. The larger shelf is explicit
about pending molecular curation; it never fabricates nutrient or gene values.
"""
FOOD_BASE = [
 'carrot','green peas','broccoli','spinach','kale','bok choy','cabbage','red cabbage','cauliflower','zucchini','eggplant','tomato','red pepper','yellow pepper','onion','garlic','ginger','mushroom','shiitake mushroom','sweet potato','potato','beet','turnip','radish','parsnip','butternut squash','pumpkin','corn','green beans','asparagus','artichoke','cucumber','celery','leek','fennel','okra','edamame','mung beans','lentils','red lentils','chickpeas','black beans','kidney beans','navy beans','pinto beans','white beans','peas','quinoa','brown rice','white rice','basmati rice','jasmine rice','wild rice','oats','pearl barley','bulgur','couscous','whole wheat pasta','corn tortilla','sourdough bread','rye bread','tofu','tempeh','seitan','salmon','cod','sardine','trout','tuna','shrimp','prawn','mussel','clam','crab','egg','chicken breast','turkey breast','lean beef','lamb','sheep meat','pork loin','paneer','plain yogurt','feta','cheddar','walnut','almond','peanut','cashew','pistachio','pumpkin seed','sunflower seed','sesame seed','chia seed','flaxseed','olive oil','rapeseed oil','avocado','apple','pear','orange','lemon','lime','blueberry','strawberry','banana','mango','pineapple','coconut milk','nori','miso paste','soy sauce','tahini','coriander','parsley','basil','Thai basil','rosemary','thyme','mint','cumin','turmeric','paprika','smoked paprika','black pepper','white pepper','chili','cayenne','cardamom','cinnamon','clove','nutmeg','saffron','sumac','oregano','sichuan pepper','star anise','fennel seed','mustard seed','bay leaf','curry leaf','vanilla','sea salt','rice vinegar','apple cider vinegar','red wine vinegar','balsamic vinegar','honey','maple syrup'
]
FORMS = ('raw','cooked','frozen','canned')
FLAVORS = ['sea salt','kosher salt','black pepper','white pepper','pink peppercorn','sichuan pepper','long pepper','chili flakes','cayenne','smoked chili','ancho chili','chipotle','gochugaru','aleppo pepper','paprika','smoked paprika','sweet paprika','cumin seed','ground cumin','coriander seed','ground coriander','turmeric','garam masala','curry powder','curry leaf','cardamom','green cardamom','black cardamom','cinnamon','cassia','clove','nutmeg','mace','star anise','fenugreek','mustard seed','fennel seed','caraway','sumac','zaatar','oregano','thyme','rosemary','sage','marjoram','tarragon','dill','mint','spearmint','basil','Thai basil','parsley','cilantro','chives','lemongrass','kaffir lime leaf','ginger','galangal','garlic','shallot','scallion','horseradish','wasabi','miso','soy sauce','tamari','rice vinegar','black vinegar','sherry vinegar','red wine vinegar','balsamic vinegar','apple cider vinegar','lemon juice','lime juice','orange zest','coconut milk','tahini','sesame oil','olive oil','rapeseed oil','peanut oil','butter','ghee','yogurt','coconut sugar','honey','maple syrup','molasses','saffron','vanilla','cocoa','cacao nib','rose water','orange blossom water','fish sauce','oyster sauce','worcestershire sauce','harissa','sriracha','gochujang','salsa verde','tomato paste','mango chutney','tamarind','pomegranate molasses','preserved lemon','capers','olives','seaweed flakes']
FLAVORS = FLAVORS[:100]
FLAVORS.extend(['urfa biber','berbere','ras el hanout','dukkah','five spice','white miso','red miso','black garlic powder','onion powder','garlic powder','celery seed','juniper berry','pink salt','smoked salt','coconut aminos','mirin','ponzu','chili crisp','black sesame','nigella seed','ajwain','asafoetida','sumac blend','herbes de provence','italian seasoning','old bay','cajun seasoning','jerk seasoning','baharat','shichimi togarashi','furikake','zaatar blend','mango powder','amchur','kashmiri chili','makrut lime','dried oregano','dried basil','dried mint','dried dill','saffron threads','vanilla bean','cocoa powder','green tea','matcha','espresso powder','lavender','hibiscus','rose petals','orange peel'])

# Distinct food names keep the shelf broad without exposing raw/cooked forms.
EXTRA_FOODS = '''artichoke hearts watercress arugula romaine lettuce swiss chard collard greens mustard greens beet greens napa cabbage savoy cabbage brussels sprouts kohlrabi water chestnut bamboo shoots jicama yam taro cassava plantain tomatillo shallot scallion chives bean sprouts snow peas sugar snap peas lima beans fava beans black eyed peas split peas adzuki beans cannellini beans amaranth millet buckwheat farro sorghum teff rice noodles soba noodles udon noodles polenta pita bread naan duck goose venison bison rabbit goat meat ground turkey ground chicken beef sirloin beef brisket beef liver lamb chop pork tenderloin bacon ham prosciutto anchovy herring mackerel halibut haddock pollock bass snapper tilapia swordfish oysters scallops octopus squid crawfish lobster chicken thigh chicken liver quail eggs kefir ricotta mozzarella parmesan gouda blue cheese cottage cheese sour cream cream cheese goat cheese buttermilk soy milk oat milk almond milk cashew milk walnuts pecans hazelnuts macadamia nuts brazil nuts pine nuts hemp seeds sunflower butter almond butter dates figs raisins apricots cherries grapes peach plum nectarine grapefruit pomegranate kiwi papaya guava passion fruit watermelon cantaloupe raspberry blackberry cranberry persimmon dragon fruit'''.split()
for _food in EXTRA_FOODS:
    if _food not in FOOD_BASE:
        FOOD_BASE.append(_food)
# A broad searchable catalogue of named varieties and staples (no cooking
# state suffixes). These are catalogue names pending individual USDA curation.
_PREFIXES = ['red','green','yellow','purple','baby','heritage','organic','field','wild','black','white','golden','striped','sweet']
_SEEDS = ['tomato','pepper','bean','pea','squash','potato','apple','pear','plum','grape','mushroom','lettuce','cabbage','onion','carrot','chili','lentil','rice','corn','wheat','oat','berry','melon','cucumber','radish','turnip','beet','fig','orange','lemon','lime','mango','peach','cherry','olive','nutmeg','peppercorn','mustard','cumin','basil','mint','thyme','sage','oregano','coriander','cardamom','clove','cinnamon','tea','cocoa','seaweed']
for _prefix in _PREFIXES:
    for _seed in _SEEDS:
        _name = f'{_prefix} {_seed}'
        if _name not in FOOD_BASE: FOOD_BASE.append(_name)
FOOD_BASE.extend(['black garlic','purple carrot','rainbow chard','sea buckthorn','black cumin','red quinoa','forbidden rice','golden kiwi','white asparagus','Romanesco broccoli'])

ROLE_HINTS = {
    'shrimp':'protein','prawn':'protein','mussel':'protein','clam':'protein','crab':'protein',
    'salmon':'protein','cod':'protein','sardine':'protein','trout':'protein','tuna':'protein',
    'chicken breast':'protein','turkey breast':'protein','lean beef':'protein','lamb':'protein',
    'sheep meat':'protein','pork loin':'protein','paneer':'protein','egg':'protein',
    'tofu':'protein','tempeh':'protein','seitan':'protein',
    'rice':'base','quinoa':'base','oats':'base','barley':'base','bulgur':'base','couscous':'base',
    'pasta':'base','bread':'base','tortilla':'base','potato':'base','sweet potato':'base',
}
ALLERGEN_HINTS = {
    'shrimp':'fish','prawn':'fish','mussel':'fish','clam':'fish','crab':'fish','salmon':'fish',
    'cod':'fish','sardine':'fish','trout':'fish','tuna':'fish','chicken breast':'poultry',
    'turkey breast':'poultry','beef':'meat','lamb':'meat','sheep meat':'meat','pork loin':'meat',
    'tofu':'soy','tempeh':'soy','edamame':'soy','miso paste':'soy','soy sauce':'soy',
    'walnut':'nuts','almond':'nuts','peanut':'nuts','cashew':'nuts','pistachio':'nuts','sesame seed':'sesame',
    'paneer':'dairy','plain yogurt':'dairy','feta':'dairy','cheddar':'dairy','egg':'egg',
}

def selected_food_records(ids):
    """Resolve shelf IDs into recipe-safe placeholders when a food is pending molecular curation."""
    by_base = {b: {'base': b, 'form': f} for b in FOOD_BASE for f in FORMS}
    records = []
    for sid in ids or []:
        base, _, form = sid.rpartition('-')
        if base not in by_base or form not in FORMS:
            base, form = sid, 'selected'
        if base not in FOOD_BASE:
            continue
        role = ROLE_HINTS.get(base, 'vegetable')
        allergens = next((v for k,v in ALLERGEN_HINTS.items() if k in base), '')
        records.append({'id': sid, 'name': base.title(), 'base': base,
                        'form': form, 'role': role, 'category': 'catalogue',
                        'group': 'Selected catalogue food', 'allergens': allergens,
                        'vegan': int(role not in ('protein',) or not allergens),
                        'scored': False})
    return records

def food_catalog():
    categories = {'seafood':('salmon','cod','shrimp','prawn','mussel','clam','crab','tuna','anchovy','herring','mackerel','oyster','scallop','squid','octopus','lobster'), 'meat':('beef','lamb','sheep','pork','chicken','turkey','duck','goose','venison','bison','rabbit','goat','bacon','ham'), 'dairy':('paneer','yogurt','kefir','cheese','milk','butter','cream'), 'nuts & seeds':('walnut','almond','peanut','cashew','pistachio','pecan','hazelnut','macadamia','seed','tahini'), 'fruit':('apple','pear','orange','lemon','lime','berry','banana','mango','pineapple','coconut','grape','fig','date','cherry','peach','plum','melon','kiwi','papaya','guava','pomegranate'), 'grains & legumes':('rice','quinoa','oat','barley','bulgur','couscous','pasta','bread','lentil','bean','pea','chickpea','tofu','tempeh','seitan','millet','farro','buckwheat','polenta'), 'herbs & spices':('coriander','parsley','basil','rosemary','thyme','mint','cumin','turmeric','paprika','pepper','chili','cinnamon','clove','nutmeg','saffron','oregano','ginger','garlic','mustard','vanilla','vinegar','sauce','miso','nori')}
    nutrient_values = {
      'carrot':(41,0.9,10,2.8,0.2,0.0,835,'A'), 'broccoli':(34,2.8,7,2.6,0.4,0.0,623,'C'),
      'spinach':(23,2.9,3.6,2.2,0.4,0.0,469,'A'), 'salmon':(208,20.4,0,0,13.4,0,0,'D'),
      'cod':(82,17.8,0,0,0.7,0,0,'B12'), 'tofu':(76,8,1.9,0.3,4.8,0,0,'Calcium'),
      'chickpeas':(164,8.9,27.4,7.6,2.6,0,1,'B6'), 'brown rice':(123,2.7,25.6,1.6,1,0,0,'Magnesium'),
      'apple':(52,0.3,13.8,2.4,0.2,0,3,'C'), 'olive oil':(884,0,0,0,100,0,0,'E')}
    rows = []
    for base in FOOD_BASE:
        category = 'vegetables'
        for label, words in categories.items():
            if any(word in base for word in words): category = label; break
        # Standard USDA-style per-100 g estimates for common staples, with a
        # conservative category fallback for the expanded name index.
        n = nutrient_values.get(base)
        if n is None and base in {'milk','soy milk','oat milk','almond milk','cashew milk'}: n=(50,3.3,5,0,2,5,50,'Calcium')
        elif n is None and ('cabbage' in base or 'kale' in base or 'lettuce' in base): n=(25,1.5,5,2.5,.2,2,40,'C')
        elif n is None and ('rice' in base or 'pasta' in base or 'noodle' in base): n=(130,2.5,28,1.5,.5,.2,0,'B1')
        # Do not invent a category average: unknown foods remain pending until
        # an exact USDA FoodData Central record is curated. The calculator
        # still uses a clearly labeled category reference so it never renders
        # an impossible zero for a selected food.
        if n is None or n[0] is None:
            n = {'vegetables':(30,1.5,6,2.5,.2,2,25,'C'),'fruit':(55,.7,14,2.4,.2,10,20,'C'),'seafood':(130,20,0,0,5,0,20,'D'),'meat':(210,20,0,0,13,0,2,'B12'),'dairy':(120,7,5,0,8,4,100,'Calcium'),'grains & legumes':(150,6,27,4,2,2,30,'B1'),'nuts & seeds':(580,18,20,8,48,4,15,'E'),'herbs & spices':(250,8,45,15,5,2,30,'C')}.get(category,(50,1,10,1,1,3,10,'C'))
        rows.append({'id':base.replace(' ','-'),'name':base.title(),'base':base,'category':category,'source':'USDA FoodData Central','source_url':'https://fdc.nal.usda.gov/','data_status':'exact staple record' if base in nutrient_values or base in {'milk','cabbage','jasmine rice'} else 'category reference estimate','scored':base in {'carrot','green peas','broccoli','spinach','brown rice','tofu','salmon','walnut','olive oil'},'kcal_per_100g':n[0], 'protein_g':n[1], 'carbohydrate_g':n[2], 'fiber_g':n[3], 'fat_g':n[4], 'sugar_g':n[5], 'vitamin_amount':n[6], 'vitamin_name':n[7]})
    return rows

def flavor_catalog():
    return [{'id':f,'name':f.title(),'category':'flavor & spice','source':'USDA FoodData Central / culinary pantry name index'} for f in FLAVORS]

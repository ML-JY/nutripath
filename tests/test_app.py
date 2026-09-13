"""Run: python -m unittest discover -s tests -v"""
import csv
import io
import unittest
from app import app, calculate, preferences, pathway_weights, DATABASE, CUISINES


class NutriPathTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_pages_and_disclaimer(self):
        for path in ('/', '/preferences', '/dashboard', '/recipes'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Educational research demo only', response.data)

    def test_every_cuisine_and_restriction(self):
        for cuisine in CUISINES:
            for diet in ('none', 'vegan', 'nuts', 'vegan_nuts'):
                result = calculate(preferences(dict(cuisine=cuisine, diet=diet)))
                eligible = {r['ingredient'] for r in DATABASE
                            if cuisine in r['cuisine_tags'].split('|')
                            and not ('vegan' in diet and r['vegan'] == '0')
                            and not ('nuts' in diet and r['nut_allergen'] == '1')}
                self.assertEqual({i['name'] for i in result['ranked']}, eligible)
                self.assertTrue(result['recipes'])
                for recipe in result['recipes']:
                    self.assertTrue(set(recipe['ingredients']) <= eligible)

    def test_weights_and_formula(self):
        for priority in range(101):
            self.assertAlmostEqual(sum(pathway_weights(priority).values()), 1)
        result = calculate(preferences(dict(priority=0, sensitivity=100, snps=['MTHFR'])))
        rice = next(i for i in result['ranked'] if i['name'] == 'Brown rice')
        base = 12 * .6 * 1.3 * .8
        self.assertAlmostEqual(rice['score'], base - base*.1)

    def test_cooking_penalty_and_snps(self):
        low = calculate(preferences(dict(sensitivity=0)))
        high = calculate(preferences(dict(sensitivity=100)))
        scores = {i['name']:i['score'] for i in low['ranked']}
        self.assertTrue(all(i['score'] <= scores[i['name']] for i in high['ranked']))
        variant = calculate(preferences(dict(snps=['MTHFR'])))
        baseline = calculate(preferences({}))
        score = lambda r: next(i['score'] for i in r['ranked'] if i['name']=='Spinach')
        self.assertGreater(score(variant), score(baseline))

    def test_slider_effects(self):
        baseline = calculate(preferences(dict(flavor=100, priority=0)))
        lipid = calculate(preferences(dict(flavor=100, priority=100)))
        self.assertNotEqual(baseline['ranked'][0]['name'], lipid['ranked'][0]['name'])
        self.assertNotEqual(baseline['support'], lipid['support'])
        traditional = calculate(preferences(dict(flavor=0, cuisine='Western')))
        scientific = calculate(preferences(dict(flavor=100, cuisine='Western')))
        self.assertNotEqual(traditional['recipes'], scientific['recipes'])

    def test_validation(self):
        for payload in ([], None, {'priority':-1}, {'priority':True}, {'priority':'50'},
                        {'flavor':101}, {'snps':['unknown']}, {'snps':['COMT','COMT']},
                        {'snps':[{}]}, {'cuisine':'French'}, {'diet':'keto'},
                        {'method':'deep fry'}, {'protein':'chicken'}, {'exclusions':['unknown']},
                        {'exclusions':'soy'}, {'method':[]}, {'diet':{}}, {'priority':float('inf')}):
            self.assertEqual(self.client.post('/api/recommend', json=payload).status_code,400)
        self.assertEqual(self.client.post('/api/recommend',data='bad',content_type='application/json').status_code,400)

    def test_export_recalculates_and_omits_genotype(self):
        response = self.client.post('/api/export',json={'snps':['MTHFR'],'diet':'vegan_nuts'})
        self.assertEqual(response.status_code,200)
        rows = list(csv.reader(io.StringIO(response.get_data(as_text=True))))
        self.assertIn('Educational research demo',rows[0][1])
        self.assertNotIn('MTHFR',response.get_data(as_text=True))
        self.assertNotIn('Salmon',response.get_data(as_text=True))
        self.assertNotIn('Walnuts',response.get_data(as_text=True))
        self.assertGreater(len(rows),3)

    def test_methods_change_instructions_and_loss(self):
        steamed = calculate(preferences({'cuisine':'Indian','method':'steam'}))
        roasted = calculate(preferences({'cuisine':'Indian','method':'roast'}))
        scores = lambda result: {i['name']:i for i in result['ranked']}
        self.assertNotEqual(scores(steamed)['Cauliflower']['score'],scores(roasted)['Cauliflower']['score'])
        self.assertIn('steam',scores(steamed)['Cauliflower']['preparation'])
        self.assertIn('roast',scores(roasted)['Cauliflower']['preparation'])
        for result in (steamed,roasted):
            recipe=result['recipes'][0]
            self.assertAlmostEqual(recipe['score'],sum(scores(result)[name]['score']*g/100 for name,g in recipe['portions'].items()))

    def test_all_exclusions_and_protein_empty_state(self):
        for cuisine in CUISINES:
            result=calculate(preferences({'cuisine':cuisine,'diet':'vegan','exclusions':['soy','gluten','nuts','sesame','egg','fish','dairy']}))
            self.assertTrue(result['recipes'],cuisine)
            for item in result['ranked']:
                self.assertFalse(item['allergens'])
            self.assertFalse(any(i['category'] in ('fish','egg','dairy') for i in result['ranked']))
        empty=calculate(preferences({'cuisine':'British','diet':'vegan','protein':'fish'}))
        self.assertEqual(empty['recipes'],[])
        self.assertEqual(empty['graph_ingredients'],[])
        self.assertEqual(empty['support'],[0,0,0])

    def test_distinct_cuisine_pantry(self):
        expected={'Indian':'Cumin','Spanish':'Smoked paprika','British':'Rosemary','Chinese':'Ginger','Thai':'Thai basil','Japanese':'Nori','Western':'Lemon juice'}
        for cuisine, anchor in expected.items():
            r=calculate(preferences({'cuisine':cuisine}))
            self.assertIn(anchor,r['recipes'][0]['ingredients'])

    def test_selected_shelf_ingredients_are_used(self):
        result = calculate(preferences({'cuisine':'Chinese',
                                        'selected_foods':['carrot-raw','broccoli-cooked','tofu-raw']}))
        first = result['recipes'][0]['ingredients']
        self.assertIn('Carrot', first)
        self.assertIn('Broccoli', first)
        self.assertIn('Tofu', first)
        # A selected scored item is preferred over the otherwise highest-ranked vegetable.
        self.assertEqual(first[1], 'Tofu')

    def test_selected_food_can_be_a_cuisine_adaptation(self):
        result = calculate(preferences({'cuisine':'Spanish',
                                        'selected_foods':['carrot-raw','broccoli-cooked','tofu-raw']}))
        first = result['recipes'][0]['ingredients']
        self.assertIn('Carrot', first)
        self.assertIn('Broccoli', first)
        self.assertIn('Tofu', first)


if __name__ == '__main__':
    unittest.main()

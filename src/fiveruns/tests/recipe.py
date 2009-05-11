#require File.dirname(__FILE__) << "/helper"
from fiveruns import dash
from mock import Mock, patch
import unittest
import helper

class RecipeTest(unittest.TestCase):
    def setUp(self):
        dash.recipes.registry.clear()
        self.config = dash.configure(app_token='ABC123')
    
    def tearDown(self):
        pass

    def testRegisterRecipe(self):
        recipe1 = dash.recipe('foo', 'http://example.com')
        self.assertEqual(dash.recipes.registry[('foo', 'http://example.com')], recipe1)

    def testDuplicateRecipe(self):
        recipe1 = dash.recipe('foo', 'http://example.com')
        self.assertRaises(dash.recipes.DuplicateRecipe, dash.recipe, 'foo', 'http://example.com')

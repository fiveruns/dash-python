import unittest
from protocol import InfoPayloadTest
from recipe import RecipeTest

def test_suite():
    suite = unittest.makeSuite(InfoPayloadTest)
    suite.addTest(unittest.makeSuite(RecipeTest))
    return suite

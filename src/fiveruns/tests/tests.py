import unittest
from protocol import InfoPayloadTest
from recipe import RecipeTest

def test_suite():
    tests = [InfoPayloadTest,
             RecipeTest]
    
    individual_suites = [unittest.makeSuite(test) for test in tests]
    
    def reduce_func(suite, test):
        suite.addTest(test)
        return suite
    return reduce(reduce_func, individual_suites)

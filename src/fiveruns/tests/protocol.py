#require File.dirname(__FILE__) << "/helper"
from fiveruns import dash
from mock import Mock, patch, patch_object
import unittest
import helper

def mock_send(status, reason, body):
    mocked_send = Mock()
    mocked_send.return_value = (status, reason, body)
    return mocked_send

class InfoPayloadTest(unittest.TestCase):
    def setUp(self):
        dash.recipes.registry.clear()
        self.config = dash.configure(app_token='ABC123')
    
    def tearDown(self):
        pass

    def testPayloadSendSuccessful(self):
        payload = dash.protocol.InfoPayload(self.config)
        self.assertEqual(True, payload.send())
    testPayloadSendSuccessful = patch('fiveruns.dash.protocol.send', mock_send(201, 'Created', 'InfoPayload: Successful body'))(testPayloadSendSuccessful)
    

    def testPayloadSendFailed(self):
        payload = dash.protocol.InfoPayload(self.config)
        self.assertEqual(False, payload.send())
    testPayloadSendFailed = patch('fiveruns.dash.protocol.send', mock_send(404, 'Not Found', 'InfoPayload: This is the body of a failed Payload Send Request'))(testPayloadSendFailed)
    
    def testPayloadSendUnknownError(self):
        payload = dash.protocol.InfoPayload(self.config)
        self.assertEqual(False, payload.send())
    testPayloadSendUnknownError = patch('fiveruns.dash.protocol.send', mock_send(500, 'Server Error', 'InfoPayload: This is the body of an unknown error with a Send Request'))(testPayloadSendUnknownError)

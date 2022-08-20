import unittest
import time
from source import lambda_function
from lib import alexa_message as message
from threading import Thread
from test import bottle_test_server as ms


class TestCommon(unittest.TestCase):

    def test_not_implemented(self):
        self.maxDiff = None
        request = message.AlexaRequest().set_header(
            namespace="Alexa.NotImplementedInterface", name="Alexa").get()
        response = lambda_function.lambda_handler(request, None)
        self.assertIsNotNone(response)
        self.assertEqual(response['event']['header']['namespace'], 'Alexa')
        self.assertEqual(response['event']['header']['name'], 'ErrorResponse')
        self.assertEqual(response['event']['payload']
                         ['type'], 'INVALID_DIRECTIVE')


class TestAcceptGrant(unittest.TestCase):
    def test_accept_grant_no_code(self):
        request = message.AlexaAuthorizationRequest(
            grant_code=None, grantee_token='0101').get()
        response = lambda_function.lambda_handler(request, None)
        self.assertIsNotNone(response)


class TestDiscovery(unittest.TestCase):

    def test_discovery_good_token(self):
        self.maxDiff = None
        request = message.AlexaDiscoveryRequest(token='0101').get()
        response = lambda_function.lambda_handler(request, None)

        self.assertEqual(response['event']['header']
                         ['namespace'], 'Alexa.Discovery')
        self.assertEqual(response['event']['header']
                         ['name'], 'Discover.Response')

        interfaces = []
        for endpoint in response['event']['payload']['endpoints']:
            for capability in endpoint['capabilities']:
                interfaces.append(capability['interface'])
        self.assertIn('Alexa.ToggleController', interfaces)

        endpoints = []
        for endpoint in response['event']['payload']['endpoints']:
            endpoints.append(endpoint['endpointId'])
        self.assertIn('spa_test_1', endpoints)

    def test_discovery_bad_token(self):
        request = message.AlexaDiscoveryRequest(token='0000').get()
        response = lambda_function.lambda_handler(request, None)

        self.assertEqual(response['event']['header']
                         ['namespace'], 'Alexa.Discovery')
        self.assertEqual(response['event']['header']
                         ['name'], 'Discovery.ErrorResponse')


class TestToggle(unittest.TestCase):

    def test_toggle(self):
        request = message.AlexaToggleRequest(
            endpointId='spa_test_1', token="0101", action="TurnOn", instance='Spa.Lights').get()
        response = lambda_function.lambda_handler(request, None)

        self.assertEqual(response['context']['properties']
                         [0]['instance'], 'Spa.Lights')
        self.assertEqual(response['context']['properties'][0]['value'], 'On')

        request = message.AlexaToggleRequest(
            endpointId='spa_test_1', token="0101", action="TurnOff", instance='Spa.Lights').get()
        response = lambda_function.lambda_handler(request, None)

        self.assertEqual(response['context']['properties']
                         [0]['instance'], 'Spa.Lights')
        self.assertNotEqual(response['context']
                            ['properties'][0]['value'], 'On')


mock_server = Thread(target=ms.run_server)
mock_server.daemon = True
mock_server.start()
time.sleep(.1)

if __name__ == '__main__':
    unittest.main()

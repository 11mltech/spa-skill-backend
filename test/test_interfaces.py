from argparse import Namespace
import unittest
from source import lambda_function
from lib import alexa_message as message


def print_handler_response(response):
    m = 40
    print(m*'-')
    print((m/2)*'-' + 'HANDLER RESPONSE' + (m/2)*'-')
    print(m*'-')
    print(response)
    print(m*'-')


class TestCommon(unittest.TestCase):

    def test_not_implemented(self):
        self.maxDiff = None
        context = message.AlexaContext().get()
        request = message.AlexaRequest(
            namespace="Alexa.NotImplementedInterface").get()
        expected = message.AlexaResponse(namespace='Alexa', name='ErrorResponse', payload={
            'type': 'INTERFACE_NOT_IMPLEMENTED',
            'message': 'The interface namespace declared in directive is not implemented in handler.'}).get()
        response = lambda_function.lambda_handler(request, context)
        self.assertIsNotNone(response)
        self.assertEqual(response['event']['header']['namespace'], 'Alexa')
        self.assertEqual(response['event']['header']['name'], 'ErrorResponse')
        self.assertEqual(response['event']['payload']
                         ['type'], 'INTERFACE_NOT_IMPLEMENTED')

class TestDiscovery(unittest.TestCase):

    def test_discovery_good_token(self):
        self.maxDiff = None
        context = message.AlexaContext().get()
        request = message.AlexaDiscoveryRequest(
            namespace="Alexa.Discovery", name="Discover", token="0101").get()
        response = lambda_function.lambda_handler(request, context)

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
        context = message.AlexaContext().get()
        request = message.AlexaDiscoveryRequest(
            namespace="Alexa.Discovery", name="Discover", token="0000").get()
        response = lambda_function.lambda_handler(request, context)

        self.assertEqual(response['event']['header']
                         ['namespace'], 'Alexa.Discovery')
        self.assertEqual(response['event']['header']
                         ['name'], 'Discovery.ErrorResponse')

class TestToggle(unittest.TestCase):

    def test_toggle(self):
        context = message.AlexaContext().get()
        request = message.AlexaToggleRequest(
            namespace="Alexa.ToggleController", name="TurnOn", token="0101").get()
        response = lambda_function.lambda_handler(request, context)
    
        self.assertTrue(1==0)



if __name__ == '__main__':
    unittest.main()

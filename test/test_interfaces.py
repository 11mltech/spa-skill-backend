import unittest
import os
import time
import pytest
from source import lambda_function
from lib import alexa_message as message
from lib.request_handler import RequestFactory, ReportState
from threading import Thread
from test import bottle_test_server as ms
from contextlib import suppress


os.environ['cloud_host'] = 'localhost'
os.environ['cloud_port'] = '3434'
os.environ['cloud_schema'] = 'http'

# os.environ['cloud_host'] = 'milonet.duckdns.org'
# os.environ['cloud_port'] = ''
# os.environ['cloud_schema'] = 'https'


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
        self.assertEqual(response['event']['header']
                         ['namespace'], 'Alexa.Authorization')
        self.assertEqual(response['event']['header']['name'], 'ErrorResponse')
        self.assertEqual(response['event']['payload']
                         ['type'], 'ACCEPT_GRANT_FAILED')

    def test_accept_grant_no_token(self):
        request = message.AlexaAuthorizationRequest(
            grant_code="invalid_code", grantee_token=None).get()
        response = lambda_function.lambda_handler(request, None)
        self.assertIsNotNone(response)
        self.assertEqual(response['event']['header']
                         ['namespace'], 'Alexa.Authorization')
        self.assertEqual(response['event']['header']['name'], 'ErrorResponse')
        self.assertEqual(response['event']['payload']
                         ['type'], 'ACCEPT_GRANT_FAILED')


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
                if capability['interface'] == 'Alexa.ToggleController':
                    self.assertIn("capabilityResources", capability.keys())
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


class TestReportState(unittest.TestCase):
    def test_directive(self):
        request = message.AlexaStateRequest(
            endpointId='spa_test_1', token="0101").get()
        self.assertIn('directive', request)
        self.assertIn('header', request['directive'])
        self.assertIn('namespace', request['directive']['header'])
        self.assertIn('name', request['directive']['header'])
        self.assertIn('messageId', request['directive']['header'])
        self.assertEqual(request['directive']['header']['namespace'], 'Alexa')
        self.assertEqual(request['directive']['header']['name'], 'ReportState')
        self.assertIn('endpoint', request['directive'])
        self.assertIn('scope', request['directive']['endpoint'])
        self.assertIn('type', request['directive']['endpoint']['scope'])
        self.assertEqual(request['directive']['endpoint']
                         ['scope']['type'], 'BearerToken')
        self.assertIn('token', request['directive']['endpoint']['scope'])
        self.assertEqual(request['directive']['endpoint']
                         ['scope']['token'], '0101')
        self.assertIn('endpointId', request['directive']['endpoint'])
        self.assertEqual(request['directive']['endpoint']
                         ['endpointId'], 'spa_test_1')

    def test_handler(self):
        request = message.AlexaStateRequest(
            endpointId='este-es-nuestro.access.token', token="0101").get()
        response = ReportState(request).handle_request()
        self.assertIn('event', response)
        self.assertIn('header', response['event'])
        self.assertIn('namespace', response['event']['header'])
        self.assertEqual(response['event']['header']['namespace'], 'Alexa')
        self.assertEqual(response['event']['header']['name'], 'StateReport')
        self.assertNotEqual(response['event']['header']['messageId'],
                            request['directive']['header']['messageId'])

        self.assertIn('context', response)

        properties = response['context']['properties']
        self.assertTrue(len(properties) > 0)
        self.assertTrue(0) 

    def test_response(self):
        response = message.StateResponse(endpoint_id='spa_test_1').get()
        self.assertEqual(response['event']['header']['namespace'], 'Alexa')
        self.assertEqual(response['event']['header']['name'], 'StateReport')
        self.assertIn('endpoint', response['event'])
        self.assertIn('endpointId', response['event']['endpoint'])
        self.assertEqual(response['event']['endpoint']
                         ['endpointId'], 'spa_test_1')

        self.assertIn('context', response)
        self.assertIn('properties', response['context'])

    def test_begin_to_end(self):
        request = message.AlexaStateRequest(
            endpointId='este-es-nuestro.access.token', token="0101").get()
        response = lambda_function.lambda_handler(request, None)
        self.assertIn('event', response)
        self.assertIn('header', response['event'])
        self.assertIn('namespace', response['event']['header'])
        self.assertEqual(response['event']['header']['namespace'], 'Alexa')
        self.assertEqual(response['event']['header']['name'], 'StateReport')


mock_server = Thread(target=ms.run_server)
mock_server.daemon = True
mock_server.start()
time.sleep(.1)

if __name__ == '__main__':
    unittest.main()

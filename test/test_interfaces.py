import unittest
import os
import time
from urllib.error import HTTPError
import pytest
from source import lambda_function
from lib import alexa_message as message
from lib.request_handler import RequestFactory, ReportState, Toggle
from lib.cloud_apis import DeviceCloud
import urllib.error
import json
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

    def test_directive(self):
        endpointId = "spa_test_1"
        token = "0101"
        action = "TurnOn"
        request = message.AlexaToggleRequest(endpointId, token, action).get()
        self.assertIn('directive', request)
        self.assertIn('header', request['directive'])
        self.assertIn('namespace', request['directive']['header'])
        self.assertIn('name', request['directive']['header'])
        self.assertIn('messageId', request['directive']['header'])
        self.assertEqual(request['directive']['header']
                         ['namespace'], 'Alexa.ToggleController')
        self.assertEqual(request['directive']['header']['name'], 'TurnOn')
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

    def test_server(self):
        server = DeviceCloud()
        endpointId = "spa_test_1"
        token = "0101"
        action = "TurnOn"
        instance = 'Spa.Lights'
        # with self.assertRaises(urllib.error.HTTPError):
        #     server.update_device_state('no-endpoint', instance, action, token)
        response = json.loads(server.update_device_state(
            endpointId, instance, action, token))
        self.assertEqual(
            response, {'status': {'endpoint_id': 'spa_test_1', 'state': 'On'}})

    def test_handler(self):
        endpointId = "spa_test_1"
        token = "0101"
        action = "TurnOn"
        request = message.AlexaToggleRequest(endpointId, token, action).get()
        response = Toggle(request).handle_request()
        self.assertIn('event', response)
        self.assertIn('header', response['event'])
        self.assertIn('namespace', response['event']['header'])
        self.assertEqual(response['event']['header']['namespace'], 'Alexa')
        self.assertEqual(response['event']['header']['name'], 'Response')
        self.assertNotEqual(response['event']['header']['messageId'],
                            request['directive']['header']['messageId'])

        self.assertIn('context', response)
        self.assertIn('properties', response['context'])
        found = False
        for prop in response['context']['properties']:
            with suppress(KeyError):
                if prop['instance'] == "Spa.Lights":
                    found = True
                    self.assertEqual(prop['namespace'],
                                      'Alexa.ToggleController')
                    self.assertEqual(prop['name'], 'toggleState')
                    self.assertEqual(prop['value'], 'On')
        self.assertTrue(found)

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
            endpointId='spa_test_2', token="0202").get()
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
                         ['scope']['token'], '0202')
        self.assertIn('endpointId', request['directive']['endpoint'])
        self.assertEqual(request['directive']['endpoint']
                         ['endpointId'], 'spa_test_2')

    def test_server(self):
        server = DeviceCloud()
        with self.assertRaises(urllib.error.HTTPError):
            server.report_state('no-endpoint')
        response = json.loads(server.report_state('spa_test_2'))
        self.assertEqual(response, {'lights': 'Off'})

    def test_handler(self):
        request = message.AlexaStateRequest(
            endpointId='spa_test_2', token='0202').get()
        response = ReportState(request).handle_request()
        self.assertIn('event', response)
        self.assertIn('header', response['event'])
        self.assertIn('namespace', response['event']['header'])
        self.assertEqual(response['event']['header']['namespace'], 'Alexa')
        self.assertEqual(response['event']['header']['name'], 'StateReport')
        self.assertNotEqual(response['event']['header']['messageId'],
                            request['directive']['header']['messageId'])

        self.assertIn('context', response)
        self.assertIn('properties', response['context'])
        found = False
        for prop in response['context']['properties']:
            with suppress(KeyError):
                if prop['instance'] == "Spa.Lights":
                    found = True
                    self.assertEqual(prop['namespace'], 'Alexa.ToggleController')
                    self.assertEqual(prop['name'], 'toggleState')
                    self.assertEqual(prop['value'], 'Off')
        self.assertTrue(found)

    def test_get_properties(self):
        request = message.AlexaStateRequest(
            endpointId='spa_test_2', token='0202').get()
        properties = ReportState(request).get_properties()
        self.assertTrue(properties, {'Spa.Lights': 'Off'})

        request = message.AlexaStateRequest(
            endpointId='no-endpoint', token='0111').get()
        with self.assertRaises(urllib.error.HTTPError):
            properties = ReportState(request).get_properties()

    def test_response(self):
        response = message.StateResponse(endpointId='spa_test_2').get()
        self.assertEqual(response['event']['header']['namespace'], 'Alexa')
        self.assertEqual(response['event']['header']['name'], 'StateReport')
        self.assertIn('endpoint', response['event'])
        self.assertIn('endpointId', response['event']['endpoint'])
        self.assertEqual(response['event']['endpoint']
                         ['endpointId'], 'spa_test_2')

        self.assertIn('context', response)
        self.assertIn('properties', response['context'])

    def test_begin_to_end(self):
        request = message.AlexaStateRequest(
            endpointId='spa_test_2', token="0202").get()
        response = lambda_function.lambda_handler(request, None)
        self.assertIn('event', response)
        self.assertIn('header', response['event'])
        self.assertIn('namespace', response['event']['header'])
        self.assertEqual(response['event']['header']['namespace'], 'Alexa')
        self.assertEqual(response['event']['header']['name'], 'StateReport')
        self.assertNotEqual(response['event']['header']['messageId'],
                            request['directive']['header']['messageId'])
        self.assertEqual(response['event']['header']['correlationToken'],
                         request['directive']['header']['correlationToken'])
        self.assertIn('endpointId', response['event']['endpoint'])
        self.assertEqual(response['event']['endpoint']
                         ['endpointId'], 'spa_test_2')
        self.assertIn('context', response)
        self.assertIn('properties', response['context'])
        self.assertEqual(response['context']['properties'], [{
            "namespace": "Alexa.ToggleController",
            "instance": "Spa.Lights",
            "name": "toggleState",
            "value": "Off"
        }])


mock_server = Thread(target=ms.run_server)
mock_server.daemon = True
mock_server.start()
time.sleep(.1)

if __name__ == '__main__':
    unittest.main()

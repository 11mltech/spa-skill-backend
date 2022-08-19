import unittest
from source import lambda_function
from lib import alexa_message as message
from threading import Thread
from bottle import Bottle, run, response


spa_map = {
    "0101": "spa_test_1",
    "0202": "spa_test_2",
    "0303": "spa_test_3"
}

spa_state = {
    "spa_test_1":
    {
        'lights': 'Off'
    },
    "spa_test_2":
    {
        'lights': 'Off'
    },
    "spa_test_3":
    {
        'lights': 'Off'
    }
}

app = Bottle()


def run_server():
    run(app, host='localhost', port=3434)


@app.route('/spa/discovery/<token>')
def discovery(token=None):

    try:
        return {
            "endpoints": [
                {
                    "endpoint_id": spa_map[token]
                }
            ]
        }
    except KeyError:
        response.status = 400
        return 'Token does not match any existing spa'


@app.route('/spa/updatestate/lights/<value>/<token>')
def device_update(value=None, token=None):
    try:
        spa = spa_map[token]
    except KeyError:
        response.status = 400
        return 'Token does not match any existing spa'

    try:
        spa_state[spa] = 'Off' if value == 'TurnOff' else 'On'
        return {
            "status":
                {
                    "endpoint_id": spa,
                    "state": spa_state[spa]
                }
        }
    except KeyError:
        response.status = 400
        return 'Internal spa-token pair map error'


mock_server = Thread(target=run_server)
mock_server.daemon = True
mock_server.start()


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
        request = message.AlexaRequest().set_header(
            namespace="Alexa.NotImplementedInterface", name="Alexa").get()
        # expected = message.AlexaResponse(namespace='Alexa', name='ErrorResponse', payload={
        #     'type': 'INTERFACE_NOT_IMPLEMENTED',
        #     'message': 'The interface namespace declared in directive is not implemented in handler.'}).get()
        response = lambda_function.lambda_handler(request, None)
        self.assertIsNotNone(response)
        self.assertEqual(response['event']['header']['namespace'], 'Alexa')
        self.assertEqual(response['event']['header']['name'], 'ErrorResponse')
        self.assertEqual(response['event']['payload']
                         ['type'], 'INTERFACE_NOT_IMPLEMENTED')


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

        self.assertEqual(response['context']['properties'][0]['instance'], 'Spa.Lights')
        self.assertEqual(response['context']['properties'][0]['value'], 'On')

        request = message.AlexaToggleRequest(
            endpointId='spa_test_1', token="0101", action="TurnOff", instance='Spa.Lights').get()
        response = lambda_function.lambda_handler(request, None)

        self.assertEqual(response['context']['properties'][0]['instance'], 'Spa.Lights')
        self.assertNotEqual(response['context']['properties'][0]['value'], 'On')


if __name__ == '__main__':
    unittest.main()

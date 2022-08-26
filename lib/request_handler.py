from lib.alexa_message import AlexaResponse, ErrorResponse, DiscoveryResponse, StateResponse
from lib.cloud_apis import DeviceCloud

import logging
import json
import urllib.request
import urllib.parse
from urllib.error import HTTPError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

client_id = 'alexa-id'
client_secret = 'alexa-secret'

name_request = {'AcceptGrant': 'AcceptGrant',
                'Discover': 'Discover',
                'TurnOn': 'Toggle',
                'TurnOff': 'Toggle',
                'ReportState': 'ReportState'}


class RequestHandler():
    def __init__(self, request):
        self.request = request
        self.server = DeviceCloud()
        self.correlationToken = self.request['directive']['header']['correlationToken']

    def handle_request(self):
        return AlexaResponse().get()


class AcceptGrant(RequestHandler):
    def handle_request(self):
        auth_code = self.request["directive"]["payload"]["grant"]["code"]

        # The Login With Amazon API for getting access and refresh tokens from an auth code.
        lwa_token_url = "https://api.amazon.com/auth/o2/token"

        data = urllib.parse.urlencode(
            {
                "grant_type": "authorization_code",
                "code": auth_code,
                "client_id": client_id,
                "client_secret": client_secret
            }
        ).encode("utf-8")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        }

        logger.info(f'AcceptGrant POST data: {data}')

        url_request = urllib.request.Request(
            lwa_token_url, data, headers, "POST")

        try:
            with urllib.request.urlopen(url_request) as response:
                """
                Response will contain the following:
                - access_token: Used in events and asynchronous responses to directives that you send to the Alexa event gateway.
                - refresh_token: Used to obtain a new access_token from LWA when this one expires.
                - token_type: Expected token type is Bearer.
                - expires_in: Number of seconds until access_token expires (expected to be 3600, or one hour).
                """
                lwa_tokens = json.loads(response.read().decode("utf-8"))

                # TODO: Save the LWA tokens in a secure location, such as AWS Secrets Manager.
                logger.info("Success!")
                logger.info(f"access_token: {lwa_tokens['access_token']}")
                logger.info(f"refresh_token: {lwa_tokens['refresh_token']}")
                logger.info(f"token_type: {lwa_tokens['token_type']}")
                logger.info(f"expires_in: {lwa_tokens['expires_in']}")
        except HTTPError as http_error:
            logger.error(
                f"An error occurred: {http_error.read().decode('utf-8')}")
            response = ErrorResponse(namespace="Alexa.Authorization",
                                     typ='ACCEPT_GRANT_FAILED',
                                     message="Failed to retrieve the LWA tokens from the user's auth code.")
        else:
            # Build the success response to send to Alexa
            response = AlexaResponse(namespace="Alexa.Authorization",
                                     name="AcceptGrant.Response",
                                     correlationToken=self.correlationToken)
        return response.get()


class Discover(RequestHandler):
    def handle_request(self):
        discovery_response = DiscoveryResponse(
            namespace='Alexa.Discovery', name='Discover.Response', correlationToken=self.correlationToken)

        # Create the response and add capabilities.
        capability_alexa = discovery_response.create_payload_endpoint_capability()

        spa_lights_capability_resources = discovery_response.create_capability_resources(
            value_text='Spa Lights')
        capability_alexa_togglecontroller = discovery_response.create_payload_endpoint_capability(
            interface='Alexa.ToggleController',
            instance='Spa.Lights',
            supported=[{'name': 'toggleState'}],
            capabilityResources=spa_lights_capability_resources,
            retrievable=True)

        # Get user's information from cloud server with token provided in request
        try:
            toggle_response = json.loads(self.server.device_discovery(
                token=self.request['directive']['payload']['scope']['token']))
        except HTTPError as http_error:
            logger.error(
                f"An error occurred: {http_error.read().decode('utf-8')}")
            return ErrorResponse(
                namespace='Alexa.Discovery',
                name='Discovery.ErrorResponse',
                typ='DISCOVERY_FAILED',
                message='Got HTTPError for directive request').get()

        # Gather endpoints with response and send back to Alexa
        for endpoint in toggle_response['endpoints']:
            discovery_response.add_payload_endpoint(
                endpoint['endpoint_id'],
                capabilities=[capability_alexa,
                              capability_alexa_togglecontroller])
        return discovery_response.get()


class ReportState(RequestHandler):
    def __init__(self, request):
        super().__init__(request)
        self.endpoint = self.request['directive']['endpoint']['endpointId']
        self.inst_namespace = {
            "lights": "Alexa.ToggleController"
        }
        self.inst_name = {
            "lights": "toggleState"
        }

    def handle_request(self):
        state_response = StateResponse(
            correlationToken=self.correlationToken, endpointId=self.endpoint)
        status = json.loads(self.server.report_state(self.endpoint))
        for key in status:
            state_response.add_context_property(namespace=self.inst_namespace[key],
                                                instance='Spa.'+key.capitalize(), name=self.inst_name[key], value=status[key])

        return state_response.get()
    
    # TODO: unused
    def get_properties(self):
        response = json.loads(self.server.report_state(self.endpoint))
        properties = []
        for key in response:
            prop = {}
            # TODO: de donde saco el namespace y el name? de la directiva no porque es reportState. En algun lado tiene que haber
            # un registro de las interfaces habilitadas para el endpoint. Deberian ser siempre las mismas.
            prop['instance'] = 'Spa.' + key.capitalize()
            prop['namespace'] = 'Alexa.ToggleController'
            prop['name'] = 'toggleState'
            prop['value'] = response[key].capitalize()
            properties.append(prop)

        return properties


class Toggle(RequestHandler):
    def handle_request(self):
        endpoint_id = self.request['directive']['endpoint']['endpointId']
        instance = self.request['directive']['header']['instance']
        token = self.request['directive']['endpoint']['scope']['token']
        value = self.request['directive']['header']['name']

        try:
            response = json.loads(
                self.server.update_device_state(endpoint_id, instance, value, token))
        except HTTPError:
            return AlexaResponse(
                namespace='Alexa.ToggleController',
                name='ToggleController.ErrorResponse',
                payload={'type': 'HTTP_ERROR', 'message': 'Got HTTPError for directive request. Token not found'}).get()

        toggle_response = AlexaResponse(
            namespace='Alexa', name='Response', token=token, correlationToken=self.correlationToken)
        toggle_response.add_context_property(namespace="Alexa.ToggleController",
                                             instance=instance, name='toggleState', value=response['status']['state'])
        return toggle_response.get()

# Error itself doesn't handle an interface request, but acts as an AlexaResponse wrapper for errors


class RequestFactory():
    def create_request_response(self, request):
        messageId = request['directive']['header']['messageId']
        # Validate the request is an Alexa smart home directive.
        if 'directive' not in request:
            return ErrorResponse(typ='INVALID_DIRECTIVE', message='Directive not in message').get()

        # Check the payload version.
        payload_version = request['directive']['header']['payloadVersion']
        if payload_version != '3':
            return ErrorResponse(typ='INVALID_DIRECTIVE', message='This skill only supports Smart Home API version 3').get()

        # Create handler for directive
        name = request['directive']['header']['name']
        try:
            targetclass = name_request[name]
        except KeyError:
            return ErrorResponse(typ='INVALID_DIRECTIVE', message='Unimplemented interface.').get()
        return globals()[targetclass](request).handle_request()

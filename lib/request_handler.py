from lib.alexa_message import AlexaResponse, ErrorResponse
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

namespace_request = {'Alexa.Authorization': 'AcceptGrant',
                     'Alexa.Discovery': 'Discover',
                     'Alexa.ToggleController': 'Toggle'}


class RequestHandler():
    def __init__(self, request):
        self.request = request
        self.server = DeviceCloud()

    def handle_request(self):
        return AlexaResponse()


class AcceptGrant(RequestHandler):
    def handle_request(self):
        auth_code = self.request["directive"]["payload"]["grant"]["code"]
        message_id = self.request["directive"]["header"]["messageId"]

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
            response = ErrorResponse(messageId=message_id,
                                     namespace="Alexa.Authorization",
                                     typ='ACCEPT_GRANT_FAILED',
                                     message="Failed to retrieve the LWA tokens from the user's auth code.")
        else:
            # Build the success response to send to Alexa
            response = AlexaResponse(namespace="Alexa.Authorization",
                                     name="AcceptGrant.Response",
                                     messageId=message_id)
        return response.get()


class Discover(RequestHandler):
    def handle_request(self):
        discovery_response = AlexaResponse(
            namespace='Alexa.Discovery', name='Discover.Response')

        # Create the response and add capabilities.
        capability_alexa = discovery_response.create_payload_endpoint_capability()
        capability_alexa_powercontroller = discovery_response.create_payload_endpoint_capability(
            interface='Alexa.PowerController',
            supported=[{'name': 'powerState'}])
        capability_alexa_togglecontroller = discovery_response.create_payload_endpoint_capability(
            interface='Alexa.ToggleController',
            supported=[{'name': 'toggleState', 'instance': 'Spa.Lights'}])
        capability_alexa_endpointhealth = discovery_response.create_payload_endpoint_capability(
            interface='Alexa.EndpointHealth',
            supported=[{'name': 'connectivity'}])

        # Get user's information from cloud server with token provided in request
        try:
            toggle_response = json.loads(self.server.device_discovery(
                token=self.request['directive']['payload']['scope']['token']))
        except:
            return AlexaResponse(
                namespace='Alexa.Discovery',
                name='Discovery.ErrorResponse',
                payload={'type': 'HTTP_ERROR', 'message': 'Got HTTPError for directive request. Token not found'}).get()

        # Gather endpoints with response and send back to Alexa
        for endpoint in toggle_response['endpoints']:
            discovery_response.add_payload_endpoint(
                friendly_name='Spa',
                endpoint_id=endpoint['endpoint_id'],
                capabilities=[capability_alexa,
                              capability_alexa_powercontroller,
                              capability_alexa_togglecontroller,
                              capability_alexa_endpointhealth, ])
        return discovery_response.get()


class Toggle(RequestHandler):
    def handle_request(self):
        endpoint_id = self.request['directive']['endpoint']['endpointId']
        instance = self.request['directive']['header']['instance']
        token = self.request['directive']['endpoint']['scope']['token']
        correlation_token = self.request['directive']['header']['correlationToken']
        value = self.request['directive']['header']['name']

        if instance == 'Spa.Lights':
            device = 'lights'
        else:
            device = 'Unmaped device'

        try:
            response = json.loads(
                self.server.update_device_state(endpoint_id, device, value, token))
        except HTTPError:
            return AlexaResponse(
                namespace='Alexa.ToggleController',
                name='ToggleController.ErrorResponse',
                payload={'type': 'HTTP_ERROR', 'message': 'Got HTTPError for directive request. Token not found'}).get()

        toggle_response = AlexaResponse(
            namespace='Alexa', name='Response', token=token, correlation_token=correlation_token)
        toggle_response.add_context_property(namespace="Alexa.ToggleController",
                                             instance=instance, name='toggleState', value=response['status']['state'])
        return toggle_response.get()

# Error itself doesn't handle an interface request, but acts as an AlexaResponse wrapper for errors


class RequestFactory():
    def create_request_response(self, request):
        messageId = request['directive']['header']['messageId']
        # Validate the request is an Alexa smart home directive.
        if 'directive' not in request:
            return ErrorResponse(messageId=messageId, typ='INVALID_DIRECTIVE', message='Directive not in message').get()

        # Check the payload version.
        payload_version = request['directive']['header']['payloadVersion']
        if payload_version != '3':
            return ErrorResponse(messageId=messageId, typ='INVALID_DIRECTIVE', message='This skill only supports Smart Home API version 3').get()

        # Create handler for directive
        namespace = request['directive']['header']['namespace']
        try:
            targetclass = namespace_request[namespace]
        except KeyError:
            return ErrorResponse(messageId=messageId, typ='INVALID_DIRECTIVE', message='Unimplemented interface.').get()
        return globals()[targetclass](request).handle_request()

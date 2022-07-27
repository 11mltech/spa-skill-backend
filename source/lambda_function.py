# -*- coding: utf-8 -*-

# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# SPDX-License-Identifier: LicenseRef-.amazon.com.-AmznSL-1.0
# Licensed under the Amazon Software License (the "License")
# You may not use this file except in
# compliance with the License. A copy of the License is located at http://aws.amazon.com/asl/
#
# This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific
# language governing permissions and limitations under the License.


import json
from urllib import response
import logging
import datetime
import urllib.request
import urllib.parse
from urllib.error import HTTPError
from datetime import datetime, timezone

# local modules
from lib.alexa_response import AlexaResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# TODO: Update with your Client Id for calling the Login with Amazon (LWA) API.
client_id = "Your Client Id"
# TODO: Update with your Client Secret for calling the LWA API.
client_secret = "Your Client Secret"
# TODO: Update with your Endpoint Id.
endpoint_id = "device_id"

def lambda_handler(request, context):

    # Dump the request for logging - check the CloudWatch logs.
    logger.info('lambda_handler request  -----')
    logger.info(json.dumps(request))

    server = DeviceCloud()

    if context is not None:
        print('lambda_handler context  -----')
        print(context)

    # Validate the request is an Alexa smart home directive.
    if 'directive' not in request:
        alexa_response = AlexaResponse(
            name='ErrorResponse',
            payload={'type': 'INVALID_DIRECTIVE',
                     'message': 'Missing key: directive, Is the request a valid Alexa Directive?'})
        return send_response(alexa_response.get())

    # Check the payload version.
    payload_version = request['directive']['header']['payloadVersion']
    if payload_version != '3':
        alexa_response = AlexaResponse(
            name='ErrorResponse',
            payload={'type': 'INTERNAL_ERROR',
                     'message': 'This skill only supports Smart Home API version 3'})
        return send_response(alexa_response.get())

    # Crack open the request to see the request.
    name = request['directive']['header']['name']
    namespace = request['directive']['header']['namespace']

    # Handle the incoming request from Alexa based on the namespace.
    if namespace == 'Alexa.Authorization':
        if name == 'AcceptGrant':
            response = handle_accept_grant(request)
            auth_response = AlexaResponse(message_id=response['event']['header']['messageId'], 
                                namespace=response['event']['header']['namespace'],
                                name=response['event']['header']['name'],
                                payload=response['event']['payload'])
            return send_response(auth_response.get())

    elif namespace == 'Alexa.Discovery':
        if name == 'Discover':
            # The request to discover the devices the skill controls.
            discovery_response = AlexaResponse(namespace='Alexa.Discovery', name='Discover.Response')
            # Create the response and add the light bulb capabilities.
            capability_alexa = discovery_response.create_payload_endpoint_capability()
            capability_alexa_powercontroller = discovery_response.create_payload_endpoint_capability(
                interface='Alexa.PowerController',
                supported=[{'name': 'powerState'}])
            capability_alexa_togglecontroller = discovery_response.create_payload_endpoint_capability(
                interface='Alexa.ToggleController',
                supported=[{'name': 'toggleState', 'instance':'Spa.Lights'}])
            capability_alexa_endpointhealth = discovery_response.create_payload_endpoint_capability(
                interface='Alexa.EndpointHealth',
                supported=[{'name': 'connectivity'}])
            discovery_response.add_payload_endpoint(
                friendly_name='Sample Light Bulb',
                endpoint_id='sample-bulb-01',
                capabilities=[capability_alexa, 
                              capability_alexa_powercontroller,
                              capability_alexa_togglecontroller,
                              capability_alexa_endpointhealth,])
            return send_response(discovery_response.get())

    elif namespace == 'Alexa.PowerController':
        # The directive to TurnOff or TurnOn the light bulb.
        # Note: This example code always returns a success response.
        endpoint_id = request['directive']['endpoint']['endpointId']
        power_state_value = 'OFF' if name == 'TurnOff' else 'ON'
        correlation_token = request['directive']['header']['correlationToken']

        # Check for an error when setting the state.
        device_set = update_device_state(endpoint_id=endpoint_id, state='powerState', value=power_state_value)
        if not device_set:
            return AlexaResponse(
                name='ErrorResponse',
                payload={'type': 'ENDPOINT_UNREACHABLE', 'message': 'Unable to reach endpoint database.'}).get()

        directive_response = AlexaResponse(correlation_token=correlation_token)
        directive_response.add_context_property(namespace='Alexa.PowerController', name='powerState', value=power_state_value)
        return send_response(directive_response.get())

    elif namespace == 'Alexa.ToggleController':
        return AlexaResponse(
            name='ErrorResponse',
            messageId='1234',
            payload={'type': 'TOGGLE_ERROR', 'message': 'ToggleController is not implemented in handler.'}).get()
    else:
        return AlexaResponse(
            name='ErrorResponse',
            messageId='1234',
            payload={'type': 'INTERFACE_NOT_IMPLEMENTED', 'message': 'The interface namespace declared in directive is not implemented in handler.'}).get()


# Send the response
def send_response(response):
    print('lambda_handler response -----')
    print(json.dumps(response))
    return response

class DeviceCloud:

    def __init__(self, **kwargs):
        self.address = kwargs.get('address', 'https://milonet.duckdns.org')
        self.endpoints = {
            "verify": "spa-auth/verify"
        }

    # Check if user exists in server, using accessToken provided by directive
    def verify_user(self, **kwargs):
        url = self.address + self.endpoints['verify']
        values = {'token' : kwargs.get('accessToken', '')}
        data = urllib.parse.urlencode(values)
        data = data.encode('ascii') # data should be bytes
        req = urllib.request.Request(url, data)
        with urllib.request.urlopen(req) as response:
            the_page = response.read()
        logger.info(f'GET {url} response status code: {response.status}')
        return response.headers

# Make the call to your device cloud for control
def update_device_state(endpoint_id, state, value):
    attribute_key = state + 'Value'
    # result = stubControlFunctionToYourCloud(endpointId, token, request);
    return True

def get_utc_timestamp(seconds=None):
    return datetime.now(timezone.utc).isoformat()


def handle_accept_grant(alexa_request):
    auth_code = alexa_request["directive"]["payload"]["grant"]["code"]
    message_id = alexa_request["directive"]["header"]["messageId"]

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

    url_request = urllib.request.Request(lwa_token_url, data, headers, "POST")

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
        logger.error(f"An error occurred: {http_error.read().decode('utf-8')}")

        # Build the failure response to send to Alexa
        response = {
            "event": {
                "header": {
                    "messageId": message_id,
                    "namespace": "Alexa.Authorization",
                    "name": "ErrorResponse",
                    "payloadVersion": "3"
                },
                "payload": {
                    "type": "ACCEPT_GRANT_FAILED",
                    "message": "Failed to retrieve the LWA tokens from the user's auth code."
                }
            }
        }
    else:
        # Build the success response to send to Alexa
        response = {
            "event": {
                "header": {
                    "namespace": "Alexa.Authorization",
                    "name": "AcceptGrant.Response",
                    "messageId": message_id,
                    "payloadVersion": "3"
                },
                "payload": {}
            }
        }

    logger.info(f"accept grant response: {json.dumps(response)}")

    return response
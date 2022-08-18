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
import os
from urllib import response
import logging
import datetime
import urllib.request
import urllib.parse
from urllib.error import HTTPError
from datetime import datetime, timezone

# local modules
from lib.alexa_message import AlexaResponse

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

    if context is not None:
        logger.info('lambda_handler context  -----')
        logger.info(context)
    else:
        logger.info('lambda_handler context is None')

    response = RequestHandler(request)
    
    send_response(response)

# Send the response
def send_response(response):
    print('lambda_handler response -----')
    print(json.dumps(response))
    return response


class DeviceCloud:

    def __init__(self, **kwargs):
        self.address = kwargs.get('address', 'http://localhost:3434')
        self.endpoints = {
            "base": "spa",
            "discovery": "discovery",
            "update_state": "updatestate"
        }

    # Check if user exists in server, using accessToken provided by directive
    def device_discovery(self, **kwargs):
        url = "/".join([self.address, self.endpoints['base'],
                       self.endpoints['discovery'], kwargs.get('token')])
        return self.get_request(url)

    def update_device_state(self, endpoint_id, device, value, token):
        url = "/".join([self.address, self.endpoints['base'],
                       self.endpoints['update_state'], device, value, token])
        return self.get_request(url)

    def get_request(self, url):
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req) as response:
                the_page = response.read()
            logger.info(f'GET {url} response status code: {response.status}')
            return the_page
        except urllib.error.HTTPError as HTTPError:
            logger.error(f'GET {url} response error')
            raise HTTPError


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

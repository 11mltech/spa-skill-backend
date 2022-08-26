import uuid
import random
import datetime
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_utc_timestamp(seconds=None):
    return datetime.now(timezone.utc).isoformat()


class AlexaResponse:

    def __init__(self, **kwargs):

        self.context_properties = []
        self.payload_endpoints = []

        # Set up the response structure.
        self.context = {}
        self.event = {
            'header': {
                'namespace': kwargs.get('namespace', 'Alexa'),
                'name': kwargs.get('name', 'Response'),
                'messageId': kwargs.get('messageId', str(uuid.uuid4())),
                'payloadVersion': kwargs.get('payload_version', '3')
            },
            'endpoint': {
                "scope": {
                    "type": "BearerToken",
                    "token": kwargs.get('token', 'INVALID')
                },
                "endpointId": kwargs.get('endpointId', 'INVALID')
            },
            'payload': kwargs.get('payload', {})
        }

        self.event['header']['correlationToken'] = kwargs.get(
            'correlationToken', 'INVALID')

        if 'cookie' in kwargs:
            self.event['endpoint']['cookie'] = kwargs.get('cookie', '{}')

        # No endpoint property in an AcceptGrant or Discover response event.
        if self.event['header']['name'] == 'AcceptGrant.Response' or self.event['header']['name'] == 'Discover.Response':
            self.event.pop('endpoint')

    def add_context_property(self, **kwargs):
        self.context_properties.append(self.create_context_property(**kwargs))
        self.context_properties.append(self.create_context_property())

    def add_cookie(self, key, value):

        if "cookies" in self is None:
            self.cookies = {}

        self.cookies[key] = value

    def add_payload_endpoint(self, endpointId, **kwargs):
        self.payload_endpoints.append(
            self.create_payload_endpoint(endpointId, **kwargs))

    def create_context_property(self, **kwargs):
        return {
            'namespace': kwargs.get('namespace', 'Alexa.EndpointHealth'),
            'name': kwargs.get('name', 'connectivity'),
            'value': kwargs.get('value', {'value': 'OK'}),
            'instance': kwargs.get('instance', 'no-instance'),
            'timeOfSample': get_utc_timestamp(),
            'uncertaintyInMilliseconds': kwargs.get('uncertainty_in_milliseconds', 0)
        }

    def create_payload_endpoint(self, endpointId, **kwargs):
        # Return the proper structure expected for the endpoint.
        # All discovery responses must include the additionAttributes
        additionalAttributes = {
            'manufacturer': kwargs.get('manufacturer', 'Applied Computer Controls'),
            'model': kwargs.get('model_name', 'ACCSSPA-MODEL-NAME'),
        }

        endpoint = {
            'capabilities': kwargs.get('capabilities', []),
            'description': kwargs.get('description', 'spa-description'),
            'displayCategories': kwargs.get('display_categories', ['THERMOSTAT', 'LIGHT']),
            'endpointId': endpointId,
            'friendlyName': kwargs.get('friendly_name', 'ACC Spa'),
            'manufacturerName': kwargs.get('manufacturer_name', 'Applied Computer Controls')
        }

        endpoint['additionalAttributes'] = kwargs.get(
            'additionalAttributes', additionalAttributes)
        if 'cookie' in kwargs:
            endpoint['cookie'] = kwargs.get('cookie', {})

        return endpoint

    def create_payload_endpoint_capability(self, **kwargs):
        # All discovery responses must include the Alexa interface
        capability = {
            'type': kwargs.get('type', 'AlexaInterface'),
            'interface': kwargs.get('interface', 'Alexa'),
            'version': kwargs.get('version', '3'),
        }

        if 'instance' in kwargs:
            capability['instance'] = kwargs.get('instance')
        if 'capabilityResources' in kwargs:
            capability['capabilityResources'] = kwargs.get(
                'capabilityResources')

        supported = kwargs.get('supported', None)
        if supported:
            capability['properties'] = {}
            capability['properties']['supported'] = supported
            capability['properties']['proactivelyReported'] = kwargs.get(
                'proactively_reported', False)
            capability['properties']['retrievable'] = kwargs.get(
                'retrievable', False)
        return capability
    
    def create_capability_resources(self, **kwargs):
        return {
            "friendlyNames":
            [{
                "@type": kwargs.get('@type', 'text'),
                "value": {
                    "text": kwargs.get('value_text', 'Spa toggleswitch'),
                    "locale": kwargs.get('locale', 'en-US')
                }
            }]
        }

    def get(self, remove_empty=True):

        response = {
            'context': self.context,
            'event': self.event
        }

        if len(self.context_properties) > 0:
            response['context']['properties'] = self.context_properties

        if len(self.payload_endpoints) > 0:
            response['event']['payload']['endpoints'] = self.payload_endpoints

        if remove_empty:
            if len(response['context']) < 1:
                response.pop('context')

        if 'ErrorResponse' in response['event']['header']['name']:
            logger.error(f"response: {response}")
        else:
            logger.info(f"response: {response}")
        return response

    def set_payload(self, payload):
        self.event['payload'] = payload

    def set_payload_endpoint(self, payload_endpoints):
        self.payload_endpoints = payload_endpoints

    def set_payload_endpoints(self, payload_endpoints):
        if 'endpoints' not in self.event['payload']:
            self.event['payload']['endpoints'] = []

        self.event['payload']['endpoints'] = payload_endpoints

class StateResponse(AlexaResponse):
    def __init__(self, **kwargs):
        super().__init__(namespace='Alexa', name='StateReport', **kwargs)
    
        self.context = kwargs.get('context', {"properties":[]})


class ErrorResponse(AlexaResponse):
    def __init__(self, **kwargs):
        self.messageId = kwargs.get('messageId', str(uuid.uuid4()))
        self.typ = kwargs.get('typ', 'INTERNAL_ERROR')
        self.message = kwargs.get(
            'message', "An error occurred that isn't described by one of the other error types")

        super().__init__(payload={'type': self.typ, 'message': self.message},
                         namespace=kwargs.get('namespace', 'Alexa'),
                         name=kwargs.get('name', 'ErrorResponse'),
                         messageId=self.messageId)
        self.event.pop('endpoint')
# Usage: pass arguments as json or use methods to populate request. Pass scope method as parameter for set_endpoint


class DiscoveryResponse(AlexaResponse):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_example(self):
        return {
            "event": {
                "header": {
                    "namespace": "Alexa.Discovery",
                    "name": "Discover.Response",
                    "messageId": "b1800c2e-f67b-43a3-972d-b26b3d028a05",
                    "payloadVersion": "3"
                },
                "payload": {
                    "endpoints": [
                        {
                            "capabilities": [
                                {
                                    "type": "AlexaInterface",
                                    "interface": "Alexa",
                                    "version": "3"
                                },
                                {
                                    "type": "AlexaInterface",
                                    "interface": "Alexa.ToggleController",
                                    "version": "3",
                                    "instance": "Spa.Lights",
                                    "retrievable": True,
                                    "properties": {
                                            "supported": [
                                                {
                                                    "name": "toggleState"
                                                }
                                            ]
                                    },
                                    "capabilityResources": {
                                        "friendlyNames": [
                                            {
                                                "@type": "text",
                                                "value": {
                                                    "text": "Spa lights",
                                                    "locale": "en-US"
                                                }
                                            }]
                                    }
                                }
                            ],
                            "description": "spa-description",
                            "displayCategories": [
                                "THERMOSTAT",
                            ],
                            "endpointId": "spa_test_4",
                            "friendlyName": "ACC Spa",
                            "manufacturerName": "Applied Computer Controls",
                            "additionalAttributes": {
                                "manufacturer": "Applied Computer Controls",
                                "model": "ACCSSPA-MODEL-NAME"
                            }
                        }
                    ]
                }
            }
        }


class AlexaRequest:
    def __init__(self, **kwargs):
        # Set up the request structure.

        self.header = kwargs.get('header', {})
        self.endpoint = kwargs.get('endpoint', {})
        self.payload = kwargs.get('payload', {})

    def set_header(self, namespace, name, **kwargs):
        self.header = {
            "namespace": namespace,
            "name": name,
            "messageId": str(uuid.uuid4()),
            "correlationToken": kwargs.get('correlationToken', str(uuid.uuid4())),
            "payloadVersion": "3"
        }
        return self

    def set_payload(self, payload, **kwargs):
        self.payload = payload
        return self

    def set_endpoint(self, endpointId, scope, **kwargs):
        self.endpoint = {
            "endpointId": endpointId,
            "cookie": kwargs.get('cookie', None),
            'scope': scope
        }
        return self

    def get(self):
        return {
            'directive': {
                'header': self.header,
                'endpoint': self.endpoint,
                'payload': self.payload
            }
        }


class AlexaDiscoveryRequest(AlexaRequest):
    def __init__(self, **kwargs):

        super().__init__()

        self.set_header(namespace="Alexa.Discovery", name="Discover")
        self.set_payload(
            {'scope': {"type": 'BearerToken', "token": kwargs.get('token', None)}})

    def get(self):
        return {
            'directive': {
                'header': self.header,
                'payload': self.payload
            }
        }


class AlexaToggleRequest(AlexaRequest):
    def __init__(self, endpointId, token, action="TurnOn", **kwargs):

        super().__init__()
        self.set_header(namespace="Alexa.ToggleController", name=action,
                        instance=kwargs.get('instance', 'Spa.Lights'))
        self.set_endpoint(
            endpointId, {"type": 'BearerToken', "token": token}, cookie=None)

    def set_header(self, namespace, name, instance):
        super().set_header(namespace, name)
        self.header['instance'] = instance
        return self


class AlexaAuthorizationRequest(AlexaRequest):
    def __init__(self, grant_code, grantee_token, **kwargs):
        super().__init__(**kwargs)
        self.set_header(namespace="Alexa.Authorization", name="AcceptGrant")
        self.set_payload({
            "grant": {
                "type": "OAuth2.AuthorizationCode",
                "code": grant_code
            },
            "grantee": {
                "type": "BearerToken",
                "token": grantee_token
            }})


class AlexaStateRequest(AlexaRequest):
    def __init__(self, endpointId, token, **kwargs):
        super().__init__(**kwargs)
        self.set_header(namespace="Alexa", name="ReportState")
        self.set_endpoint(
            endpointId, {"type": 'BearerToken', "token": token}, cookie=None)
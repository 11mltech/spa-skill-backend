import uuid
import random
import datetime


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
                "endpointId": kwargs.get('endpoint_id', 'INVALID')
            },
            'payload': kwargs.get('payload', {})
        }

        if 'correlation_token' in kwargs:
            self.event['header']['correlation_token'] = kwargs.get(
                'correlation_token', 'INVALID')

        if 'cookie' in kwargs:
            self.event['endpoint']['cookie'] = kwargs.get('cookie', '{}')

        # No endpoint property in an AcceptGrant or Discover request.
        if self.event['header']['name'] == 'AcceptGrant.Response' or self.event['header']['name'] == 'Discover.Response':
            self.event.pop('endpoint')

    def add_context_property(self, **kwargs):
        self.context_properties.append(self.create_context_property(**kwargs))
        self.context_properties.append(self.create_context_property())

    def add_cookie(self, key, value):

        if "cookies" in self is None:
            self.cookies = {}

        self.cookies[key] = value

    def add_payload_endpoint(self, **kwargs):
        self.payload_endpoints.append(self.create_payload_endpoint(**kwargs))

    def create_context_property(self, **kwargs):
        return {
            'namespace': kwargs.get('namespace', 'Alexa.EndpointHealth'),
            'name': kwargs.get('name', 'connectivity'),
            'value': kwargs.get('value', {'value': 'OK'}),
            'instance': kwargs.get('instance', 'no-instance'),
            'timeOfSample': datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            'uncertaintyInMilliseconds': kwargs.get('uncertainty_in_milliseconds', 0)
        }

    def create_payload_endpoint(self, **kwargs):
        # Return the proper structure expected for the endpoint.
        # All discovery responses must include the additionAttributes
        additionalAttributes = {
            'manufacturer': kwargs.get('manufacturer', 'Whole Electronic Solutions'),
            'model': kwargs.get('model_name', 'Sample Model'),
            'serialNumber': kwargs.get('serial_number', 'U11112233456'),
            'firmwareVersion': kwargs.get('firmware_version', '1.24.2546'),
            'softwareVersion': kwargs.get('software_version', '1.036'),
            'customIdentifier': kwargs.get('custom_identifier', 'Sample custom ID')
        }

        endpoint = {
            'capabilities': kwargs.get('capabilities', []),
            'description': kwargs.get('description', 'spa controller application'),
            'displayCategories': kwargs.get('display_categories', ['THERMOSTAT']),
            'endpointId': kwargs.get('endpoint_id', 'endpoint_' + "%0.6d" % random.randint(0, 999999)),
            'friendlyName': kwargs.get('friendly_name', 'wes-spa'),
            'manufacturerName': kwargs.get('manufacturer_name', 'Whole Electronic Solutions')
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
            'version': kwargs.get('version', '3')
        }
        supported = kwargs.get('supported', None)
        if supported:
            capability['properties'] = {}
            capability['properties']['supported'] = supported
            capability['properties']['proactivelyReported'] = kwargs.get(
                'proactively_reported', False)
            capability['properties']['retrievable'] = kwargs.get(
                'retrievable', False)
        return capability

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

        return response

    def set_payload(self, payload):
        self.event['payload'] = payload

    def set_payload_endpoint(self, payload_endpoints):
        self.payload_endpoints = payload_endpoints

    def set_payload_endpoints(self, payload_endpoints):
        if 'endpoints' not in self.event['payload']:
            self.event['payload']['endpoints'] = []

        self.event['payload']['endpoints'] = payload_endpoints


# Usage: pass arguments as json or use methods to populate request. Pass scope method as parameter for set_endpoint
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
            "correlationToken": kwargs.get('correlationToken', None),
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

    def scope(self, token, type='BearerToken'):
        return {
            "type": type,
            "token": token
        }

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
        self.set_payload({'scope': self.scope(kwargs.get('token', None))})

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
        self.set_endpoint(endpointId, self.scope(token), cookie=None)

    def set_header(self, namespace, name, instance):
        super().set_header(namespace, name)
        self.header['instance'] = instance
        return self

import unittest
from source import lambda_function


class TestHandler(unittest.TestCase):

    def test_handler(self):
        self.maxDiff = None
        context = {'aws_request_id': 'c048b9bf-e5d8-442f-9164-0d3a50668bce',
                   'log_group_name': '/aws/lambda/spa-skill-backend',
                   'log_stream_name': '2022/07/27/[$LATEST]99b8d584e06f4cef81c559257fb24dd7',
                   'function_name': 'spa-skill-backend',
                   'memory_limit_in_mb': '128',
                   'function_version': '$LATEST',
                   'invoked_function_arn': 'arn:aws:lambda:us-east-1:329531334150:function:spa-skill-backend',
                   'client_context': None,
                   'identity': None}

        request = {
            "directive": {
                "header": {
                    "namespace": "Alexa.NotImplementedInterface",
                    "instance": "Spa.Lights",
                    "name": "TurnOn",
                            "messageId": "1234",
                            "correlationToken": "an opaque correlation token",
                            "payloadVersion": "3"},
                "endpoint": {
                    "scope": {
                        "type": "BearerToken",
                                "token": "an OAuth2 bearer token"},
                    "endpointId": "endpoint ID",
                    "cookie": {}},
                "payload": {}
            }
        }
        expected = {
            'event': {
                'header': {
                    'namespace': 'Alexa',
                    'name': 'ErrorResponse',
                    'messageId': '1234',
                    'payloadVersion': '3'},
                'endpoint': {
                    'scope': {
                        'type': 'BearerToken', 'token': 'INVALID'},
                    'endpointId': 'INVALID'},
                'payload': {
                    'type': 'INTERFACE_NOT_IMPLEMENTED',
                            'message': 'The interface namespace declared in directive is not implemented in handler.'}
            }
        }
        response = lambda_function.lambda_handler(request, context)
        # print(20*'-')
        # print('HANDLER RESPONSE')
        # print(20*'-')
        # print(response)
        # print(20*'-')
        self.assertEqual(response, expected)


if __name__ == '__main__':
    unittest.main()

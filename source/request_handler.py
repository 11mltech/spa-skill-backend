class RequestHandler:
    def __init__(request):






    

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
            toggle_response = handle_accept_grant(request)
            auth_response = AlexaResponse(message_id=toggle_response['event']['header']['messageId'],
                                          namespace=toggle_response['event']['header']['namespace'],
                                          name=toggle_response['event']['header']['name'],
                                          payload=toggle_response['event']['payload'])
            return send_response(auth_response.get())

    elif namespace == 'Alexa.Discovery':
        if name == 'Discover':
            # The request to discover the devices the skill controls.
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
                toggle_response = json.loads(server.device_discovery(
                    token=request['directive']['payload']['scope']['token']))
            except HTTPError:
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
            return send_response(discovery_response.get())

    elif namespace == 'Alexa.PowerController':
        # The directive to TurnOff or TurnOn the light bulb.
        # Note: This example code always returns a success response.
        endpoint_id = request['directive']['endpoint']['endpointId']
        power_state_value = 'OFF' if name == 'TurnOff' else 'ON'
        correlation_token = request['directive']['header']['correlationToken']

        # Check for an error when setting the state.
        device_set = server.update_device_state(
            endpoint_id=endpoint_id, state='powerState', value=power_state_value)
        if not device_set:
            return AlexaResponse(
                name='ErrorResponse',
                payload={'type': 'ENDPOINT_UNREACHABLE', 'message': 'Unable to reach endpoint database.'}).get()

        directive_response = AlexaResponse(correlation_token=correlation_token)
        directive_response.add_context_property(
            namespace='Alexa.PowerController', name='powerState', value=power_state_value)
        return send_response(directive_response.get())

    elif namespace == 'Alexa.ToggleController':

        endpoint_id = request['directive']['endpoint']['endpointId']
        instance = request['directive']['header']['instance']
        token = request['directive']['endpoint']['scope']['token']
        correlation_token = request['directive']['header']['correlationToken']
        value = request['directive']['header']['name']

        if instance == 'Spa.Lights':
            device = 'lights'
        else:
            device = 'Unmaped device'

        try:
            response = json.loads(
                server.update_device_state(endpoint_id, device, value, token))
        except HTTPError:
            return AlexaResponse(
                namespace='Alexa.ToggleController',
                name='ToggleController.ErrorResponse',
                payload={'type': 'HTTP_ERROR', 'message': 'Got HTTPError for directive request. Token not found'}).get()

        toggle_response = AlexaResponse(
            namespace='Alexa', name='Response', token=token, correlation_token=correlation_token)
        toggle_response.add_context_property(namespace="Alexa.ToggleController",
                                             instance=instance, name='toggleState', value=response['status']['state'])
        return send_response(toggle_response.get())

    else:
        return AlexaResponse(
            name='ErrorResponse',
            messageId=request['directive']['header']['messageId'],
            payload={'type': 'INTERFACE_NOT_IMPLEMENTED', 'message': 'The interface namespace declared in directive is not implemented in handler.'}).get()

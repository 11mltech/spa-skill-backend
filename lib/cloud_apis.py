import urllib.request
import urllib.parse
from urllib.error import HTTPError
from urllib import response

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# TODO: Update with your Client Id for calling the Login with Amazon (LWA) API.
client_id = "Your Client Id"
# TODO: Update with your Client Secret for calling the LWA API.
client_secret = "Your Client Secret"
# TODO: Update with your Endpoint Id.
endpoint_id = "device_id"


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

import urllib.request
import urllib.parse
from urllib.error import HTTPError
from urllib import response
import os

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DeviceCloud:

    def __init__(self, **kwargs):
        self.schema = os.getenv('cloud_schema')
        self.host = os.getenv('cloud_host')
        self.port = os.getenv('cloud_port')
        if self.port == '':
            self.url = f'{self.schema}://{self.host}'
        else:
            self.url = f'{self.schema}://{self.host}:{self.port}'
        self.endpoints = {
            "base": "spa",
            "discovery": "discovery",
            "update_state": "updatestate",
            "report_state": "reportstate"
        }

    # Check if user exists in server, using accessToken provided by directive
    def device_discovery(self, **kwargs):
        url = "/".join([self.url, self.endpoints['base'],
                       self.endpoints['discovery'], kwargs.get('token')])
        return self.get_request(url)

    def update_device_state(self, endpoint_id, instance, value, token):
        device = instance.split(".")[1].lower()
        url = "/".join([self.url, self.endpoints['base'],
                       self.endpoints['update_state'], device, value, token])
        return self.get_request(url)

    def report_state(self, endpoint_id):
        url = "/".join([self.url, self.endpoints['base'],
                       self.endpoints['report_state'], endpoint_id])
        return self.get_request(url)

    def get_request(self, url):
        req = urllib.request.Request(url)
        try:
            logger.info('"Attempting connection to ')
            with urllib.request.urlopen(req) as response:
                the_page = response.read()
            logger.info(f'GET {url} response status code: {response.status}')
            return the_page
        except urllib.error.HTTPError as HTTPError:
            logger.error(f'GET {url} response error')
            raise HTTPError



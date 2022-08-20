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
import logging
import datetime
from datetime import datetime, timezone

# local modules
from lib.request_handler import RequestFactory

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(request, context):

    # Dump the request for logging - check the CloudWatch logs.
    logger.info('lambda_handler request  -----')
    logger.info(json.dumps(request))

    if context is not None:
        logger.info('lambda_handler context  -----')
        logger.info(context)
    else:
        logger.info('lambda_handler context is None')

    response = RequestFactory().create_request_response(request)
    return send_response(response)

# Send the response


def send_response(response):
    print('lambda_handler response -----')
    print(json.dumps(response))
    return response

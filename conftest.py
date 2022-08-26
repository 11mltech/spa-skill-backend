# conftest.py

import pytest
import time
from threading import Thread
from test import bottle_test_server as ms

@pytest.fixture(scope="module")
def bottle_server():
    mock_server = Thread(target=ms.run_server)
    mock_server.daemon = True
    mock_server.start()
    time.sleep(.1)
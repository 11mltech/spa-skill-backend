from bottle import Bottle, run, response

spa_map = {
    "0101": "spa_test_1",
    "0202": "spa_test_2",
    "0303": "spa_test_3",
    "este-es-nuestro.access.token":"spa_test_4"
}

spa_state = {
    "spa_test_1":
    {
        'lights': 'Off'
    },
    "spa_test_2":
    {
        'lights': 'Off'
    },
    "spa_test_3":
    {
        'lights': 'Off'
    },
    "spa_test_4":
    {
        'lights': 'Off'
    }
}

app = Bottle()


def run_server():
    run(app, host='localhost', port=3434)


@app.route('/spa/discovery/<token>')
def discovery(token=None):

    try:
        return {
            "endpoints": [
                {
                    "endpoint_id": spa_map[token]
                }
            ]
        }
    except KeyError:
        response.status = 400
        return 'Token does not match any existing spa'


@app.route('/spa/updatestate/lights/<value>/<token>')
def device_update(value=None, token=None):
    try:
        spa = spa_map[token]
    except KeyError:
        response.status = 400
        return 'Token does not match any existing spa'

    try:
        spa_state[spa] = 'Off' if value == 'TurnOff' else 'On'
        return {
            "status":
                {
                    "endpoint_id": spa,
                    "state": spa_state[spa]
                }
        }
    except KeyError:
        response.status = 400
        return 'Internal spa-token pair map error'


if __name__ == '__main__':
    run_server()

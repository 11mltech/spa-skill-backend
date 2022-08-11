from urllib.error import HTTPError
from bottle import Bottle, run, response
app = Bottle()

def run_server():
    run(app, host='localhost', port=3434)


@app.route('/spa/discovery/<token>')
def discovery(token=None):

    spa_map = {
        "0101": "spa_test_1",
        "0202": "spa_test_2",
        "0303": "spa_test_3"
    }
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
        return 'Object already exists with that name'


run_server()

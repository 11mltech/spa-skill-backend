from bottle import Bottle, run
app = Bottle()


@app.route('/spa/discovery')
def hello():
    return {
        "endpoints": [
            {
                "endpoint_id":"spa_test_1"
            }
        ]
    }

run(app, host='localhost', port=3434)
from bottle import Bottle, run
app = Bottle()


@app.route('/spa/discovery')
def hello():
    return {
        "discovery":"hi!"
    }

run(app, host='localhost', port=3434)

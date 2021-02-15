import random
import time

from flask import Flask, render_template_string, abort
from prometheus_client import generate_latest, REGISTRY, Counter, Gauge, Histogram

app = Flask(__name__)

# A counter to count the total number of HTTP requests
REQUESTS = Counter('http_requests_total', 'Total HTTP Requests (count)', ['method', 'endpoint', 'status_code'])

# A gauge (i.e. goes up and down) to monitor the total number of in progress requests
IN_PROGRESS = Gauge('http_requests_inprogress', 'Number of in progress HTTP requests')


APPPOINTS = Gauge('appoints_total', 'Maximo AppPoints Total', ['metric_type', 'product_id', 'product_name', 'product_metric'])
APPPOINTS_BREAKDOWN = Gauge('appoints_by_capability', 'Maximo AppPoints Breakdown', ['parent', 'category', 'metric_type', 'product_id', 'product_name', 'product_metric', 'value_name'])

appoints_val = 1


# Standard Flask route stuff.
@app.route('/')
# Helper annotation to increment a gauge when entering the method and decrementing when leaving.
@IN_PROGRESS.track_inprogress()
def hello_world():
    REQUESTS.labels(method='GET', endpoint="/", status_code=200).inc()  # Increment the counter
    return 'Hello, World!'

# Note I'm intentionally failing occasionally to simulate a flakey service.
@app.route('/slow')
@IN_PROGRESS.track_inprogress()
def slow_request():
    v = random.expovariate(1.0 / 1.3)
    if v > 3:
        REQUESTS.labels(method='GET', endpoint="/slow", status_code=500).inc()
        abort(500)
    time.sleep(v)
    REQUESTS.labels(method='GET', endpoint="/slow", status_code=200).inc()
    return render_template_string('<h1>Wow, that took {{v}} s!</h1>', v=v)


@app.route('/hello/<name>')
@IN_PROGRESS.track_inprogress()
def index(name):
    REQUESTS.labels(method='GET', endpoint="/hello/<name>", status_code=200).inc()
    return render_template_string('<b>Hello {{name}}</b>!', name=name)


@app.route('/metrics')
@IN_PROGRESS.track_inprogress()
def metrics():
    REQUESTS.labels(method='GET', endpoint="/metrics", status_code=200).inc()
    global appoints_val
    appoints_val += 1
    APPPOINTS.labels(metric_type='adoption', product_id='123', product_name='Maximo', product_metric='AppPoints').set(appoints_val)
    APPPOINTS_BREAKDOWN.labels(metric_type='adoption', product_id='123', product_name='Maximo', product_metric='AppPoints', parent='appoints_total', category='capability', value_name='Capability 1').set(appoints_val-1)
    APPPOINTS_BREAKDOWN.labels(metric_type='adoption', product_id='123', product_name='Maximo', product_metric='AppPoints', parent='appoints_total', category='capability', value_name='Capability 2').set(1)

    return generate_latest(REGISTRY)


if __name__ == "__main__":
    app.run(host='0.0.0.0')

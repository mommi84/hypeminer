#!/usr/bin/env python
from hypeminer.core import Hypeminer
from flask import Flask
import json


app = Flask(__name__)

h = Hypeminer("store", currency="BTCBUSD")


@app.route('/predict')
def hello_world():
    """Prediction endpoint."""
    predictions = h.get_last_json()
    return predictions

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8080)

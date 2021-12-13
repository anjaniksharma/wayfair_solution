# This is the file that implements a flask server to do inferences. 

from __future__ import print_function

import io
import json
import os
import pickle
import signal
import sys
import traceback

import flask
import pandas as pd

from enum import Enum
from typing import Callable, NamedTuple

prefix = "/opt/ml/"
features_path= os.path.join(prefix, "results/features.csv")

class Features(NamedTuple):
    """
    Container for model feature values
    :field: order_hour_of_day: int, A number between 0-23 with the hour of the day of
        the order timestamp
    :field: inventory: int, Sku inventory at the time of the order is placed
    :field: payment_status: str, Categorial feature: Payment status of the order
        returned by payment method provider
    :field: zip_code_available: bool, whether the delivery to the zip_code is possible 
    """
    
    order_hour_of_day: int
    inventory: int
    payment_status: str
    zip_code_available: bool


class Recommendation(Enum): 
    """
    Possible predicted classes
    """
    DELIVER = 'Deliver'
    HOLD_CHECK_AVAILABILITY = 'HoldCheckAvailability' 
    HOLD_CHECK_DELIVERY = 'HoldCheckDelivery' 
    HOLD_CHECK_PAYMENT = 'HoldCheckPayment'
    DECLINE = 'Decline'


def model_v1(features: Features) -> Recommendation: 
    """
    This function is a very simple unrealistic example of what a decision tree could predict based on the example features above. We can assume that it behaves like a real-world ML model
    for the purposes of this exercise.
    """
    if features.inventory <= 0:
        return Recommendation.HOLD_CHECK_AVAILABILITY 
    if not features.zip_code_available:
        return Recommendation.HOLD_CHECK_DELIVERY 
    if features.payment_status != "OK":
        return Recommendation.HOLD_CHECK_PAYMENT 
    if features.order_hour_of_day < 6:
        return Recommendation.DECLINE 
    return Recommendation.DELIVER


class ModelService(object):
    features = None  # Where we keep the model when it's loaded

    @classmethod
    def get_features(cls):
        """Get the model object for this instance, loading it if it's not already loaded."""
        if isinstance(cls.features, type(None)) :
            print("Feature getting loaded")
            cls.features = pd.read_csv(features_path)
            cls.features.set_index(['order_id','customer_id','sku_code','zip_code'],inplace=True)
            
        return cls.features

    @classmethod
    def predict(cls, input):
        """For the input, do the predictions and return them.

        Args:
            input (a pandas dataframe): The data on which to do the predictions. There will be
                one prediction per row in the dataframe"""
        clf = cls.get_features()
        
        df = clf.loc[input][['order_hour_of_day','inventory','payment_status','zip_code_available']]
        pred = model_v1(Features(df.order_hour_of_day,df.inventory,df.payment_status,df.zip_code_available))
        
        return {"order_id": input[1],"recommendation":pred.value}


# The flask app for serving predictions
app = flask.Flask(__name__)


@app.route("/ping", methods=["GET"])
def ping():
    """Determine if the container is working and healthy. In this sample container, we declare
    it healthy if we can load the model successfully."""
    health = ModelService.get_features() is not None  # You can insert a health check here

    status = 200 if health else 404
    return flask.Response(response="\n", status=status, mimetype="application/json")


@app.route("/invocations", methods=["POST"])
def transformation():
    """Do an inference on a single batch of data. In this sample server, we take data as CSV, convert
    it to a pandas data frame for internal use and then convert the predictions back to CSV (which really
    just means one prediction per line, since there's a single column.
    """
    data = None

    # Convert from CSV to pandas
    if flask.request.content_type == "text/json":
        data = flask.request.data.decode("utf-8")
        data=io.StringIO('['+data+']')
        data = pd.read_json(data)

        
    else:
        return flask.Response(
            response="This predictor only supports JSON data", status=415, mimetype="text/plain"
        )

    predictions = ModelService.predict(tuple(data.values[0]))
    return flask.Response(response=json.dumps(predictions), status=200, mimetype="text/plain")


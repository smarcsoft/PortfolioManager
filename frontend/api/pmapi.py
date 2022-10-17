import os
import string
import sys
from xmlrpc.client import boolean
from flask import Flask
from flask_restful import Resource, Api, reqparse
from numpy import number
import pandas as pd
import boto3
from flask_cors import CORS
import logging
import logging.config
import logging.handlers
sys.path.append(os.path.join(os.getcwd(),'..','..','utils'))
from config import get_config


logging.config.fileConfig("config/logging.conf")


app = Flask(__name__)
CORS(app)


UNKNOWN=-1
EXCEPTION=-2
PENDING=0
RUNNING=16
SHUTTING_DOWN=32
TERMINATED=48
STOPPING=64
STOPPED=80

api = Api(app)
k=get_config("akey", configfile="config/pmapi.conf")
s=get_config("asec", configfile="config/pmapi.conf")
boto3.Session(k, s)
client = boto3.client('ec2', 'us-east-1')


@app.route("/")
class Services(Resource):

    def __init__(self):
        self._logger = logging.getLogger('root')
        self._logger.debug("Logging initialized.")

    def get(self):
        '''
        return the status code of the compute instance of -1 if it cannot be known
        '''
        try:
            self._logger.debug("get called. Checking state.")
            toreturn=self.check_server_status()
            return {'status': toreturn}, 200
        except Exception as e:
            self._logger.error(e)
            return {'status': EXCEPTION,'details':e.__repr__()}, 200

    def post(self):
        '''
        return the status code of the compute instance once started
        '''
        try:
            self._logger.debug("post called. Starting servers.")
            toreturn=self.start_server()
            return {'status': toreturn}, 200
        except Exception as e:
            self._logger.error(e)
            return {'status': EXCEPTION,'details':e.__repr__()}, 200

    def delete(self):
        '''
        return the status code of the compute instance once stopped
        '''
        try:
            self._logger.debug("delete called. Stopping servers.")
            instance_id=self.get_compute_instance_id()
            self._logger.debug("Instance ID of stopped server:%s. Now stopping...", instance_id)
            r = client.stop_instances(InstanceIds=[instance_id])
            code:number =-1
            for instance in r["StoppingInstances"]:
                code=instance["CurrentState"]["Code"]
                self._logger.debug("Instance state code of %s:%d", instance_id, code)
                return {'status': code}, 200
        except Exception as e:
            self._logger.error(e)
            return {'status': EXCEPTION,'details':e.__repr__()}, 200
        

    def start_server(self)->number:
        self._logger.debug("Starting servers....")
        if self.check_server_status() == True:
            self._logger.debug("Servers were already started....")
            return RUNNING
        instance_id=self.get_compute_instance_id()
        self._logger.debug("Instance ID of newly started server:%s", instance_id)
        r = client.start_instances(InstanceIds=[instance_id])
        instance_state_code = UNKNOWN
        for instance in r["StartingInstances"]:
            instance_state_code=instance["CurrentState"]["Code"]
        self._logger.debug("Instance state code of %s:%d", instance_id, instance_state_code)
        # If the instance is running, check its status to set its state as running, otherwise, keep the pending state.
        if instance_state_code == RUNNING:
            ist = client.describe_instance_status(InstanceIds=[instance_id])
            for instance in ist["InstanceStatuses"]:
                instance_status_code=instance["InstanceStatus"]["Status"]
                self._logger.debug("Instance status of %s:%s", instance_id, instance_status_code)
                if instance_status_code=='ok':
                    self._logger.debug("Regturning RUNNING")
                    return RUNNING
        self._logger.debug("Regturning PENDING")
        return PENDING




    def check_server_status(self)->number:
        instance_id=self.get_compute_instance_id()
        r = client.describe_instance_status(InstanceIds=[instance_id])
        for instance_status in r["InstanceStatuses"]:
            if (instance_status['InstanceId'] == instance_id) and (instance_status["InstanceState"]["Code"] == 16):
                self._logger.debug("server state returns " + str(RUNNING))
                return RUNNING
        self._logger.debug("server state returns " + str(UNKNOWN))
        return UNKNOWN

    def get_compute_instance_id(self)->string:
        return 'i-0a3774d4c3e971e64'




api.add_resource(Services, '/services')


if __name__ == '__main__':
    logging.getLogger(None).setLevel("DEBUG")
    app.run()  # run our Flask app

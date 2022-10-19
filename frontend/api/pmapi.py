import argparse
import os
import string
import subprocess
import sys
from typing import Literal, TypedDict
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


class Status(TypedDict):
    status_code: int
    message: str
    ip: str


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

CONFIG_FILE="config/pmapi.conf"

api = Api(app)
k=get_config("akey", configfile=CONFIG_FILE)
s=get_config("asec", configfile=CONFIG_FILE)
boto3.Session(k, s)
client = boto3.client('ec2', 'us-east-1')
unix = False
scriptdir=get_config("scriptdir", configfile=CONFIG_FILE)

@app.route("/")
class Services(Resource):

    def __init__(self):
        self._logger = logging.getLogger('root')
        self._logger.debug("Logging initialized.")
        self._IP = None

    def get(self):
        '''
        return the status code of the compute instance of -1 if it cannot be known
        '''
        try:
            self._logger.debug("Get called. Checking state.")
            return self.check_server_status(), 200
        except Exception as e:
            self._logger.error(e)
            return {'status_code': EXCEPTION,'message':e.__repr__()}, 200

    def post(self):
        '''
        return the status code of the compute instance once started
        '''
        try:
            self._logger.debug("Post called. Starting servers.")
            return self.start_server(), 200
        except Exception as e:
            self._logger.error(e)
            return {'status_code': EXCEPTION,'message':e.__repr__()}, 200

    def delete(self):
        '''
        return the status code of the compute instance once stopped
        '''
        try:
            self._logger.debug("Delete called. Stopping servers.")
            return self.stop_server(),200
        except Exception as e:
            self._logger.error(e)
            return {'status': EXCEPTION,'details':e.__repr__()}, 200
        

    def stop_server(self)->Status:
        instance_id=self.get_compute_instance_id()
        self._logger.debug("Instance ID of stopped server:%s. Now stopping...", instance_id)
        r = client.stop_instances(InstanceIds=[instance_id])
        code:number =-1
        for instance in r["StoppingInstances"]:
            code=instance["CurrentState"]["Code"]
            self._logger.debug("Instance state code of %s:%d", instance_id, code)
            return {'status_code': code}

    
    def start_server(self)->Status:
        self._logger.debug("Starting servers....")
        status:Status = self.check_server_status()
        if status["status_code"] == RUNNING:
            self._logger.debug("Servers were already started....")
            return {"status_code":RUNNING, "ip": self.get_server_IP()}
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
                    self._logger.debug("Returning RUNNING")
                    return {"status_code":RUNNING, "ip":self.get_server_IP()}
        self._logger.debug("Returning PENDING")
        return {"status_code":PENDING}



    def check_server_status(self)->Status:
        instance_id=self.get_compute_instance_id()
        IP:string = self.get_server_IP()
        r = client.describe_instance_status(InstanceIds=[instance_id])
        for instance_status in r["InstanceStatuses"]:
            if (instance_status['InstanceId'] == instance_id):
                self._logger.debug("server state returns " + str(instance_status["InstanceState"]["Code"]))
                return {"status_code":instance_status["InstanceState"]["Code"], "ip":IP}
        self._logger.debug("server state returns " + str(UNKNOWN))
        return {"status_code":UNKNOWN}

    def get_server_IP(self)->string:
        if(self._IP == None):
            r = client.describe_instances(InstanceIds=[self.get_compute_instance_id()])
            if (len(r["Reservations"]) ==1) and (len(r["Reservations"][0]["Instances"]) ==1):
                if 'PublicIpAddress' in r["Reservations"][0]["Instances"][0]:
                    self._IP=r["Reservations"][0]["Instances"][0]['PublicIpAddress']
        return self._IP

    def get_compute_instance_id(self)->string:
        return 'i-0a3774d4c3e971e64'


@app.route("/")
class Jupyter(Resource):

    def __init__(self):
        self._logger = logging.getLogger('root')
        self._logger.debug("Logging initialized.")

    def post(self):
        try:
            self._logger.debug("get called on jupyter endpoint.")
            start_script=os.path.join(scriptdir,"run_jupyter.sh")
            self._logger.info("Executing %s", start_script)
            cp:subprocess.CompletedProcess = subprocess.run([start_script, "--background"])
            if cp.returncode == 0:
                self._logger.info("Done with success")
                return {'status': RUNNING}, 200
            self._logger.error(cp.stdout)
            return {'status': EXCEPTION,'details':cp.stdout}, 200
        except Exception as e:
            self._logger.error(e)
            return {'status': EXCEPTION,'details':e.__repr__()}, 200


api.add_resource(Services, '/services')
api.add_resource(Jupyter, '/jupyter')
if __name__ == '__main__':
    logging.getLogger(None).setLevel("DEBUG")
    app.run(host='0.0.0.0')  # run our Flask app

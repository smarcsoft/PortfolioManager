import os
import string
import subprocess
import sys
from typing import TypedDict
from flask import Flask
from flask_restful import Resource, Api, reqparse
from numpy import number
import pandas as pd
import boto3
from flask_cors import CORS
import logging
import logging.config
import logging.handlers
from config import init_config

import requests
sys.path.append(os.path.join(os.getcwd(),'..','..','utils'))
from config import get_config


class Status(TypedDict):
    status_code: int
    message: str
    ip: str


logging.config.fileConfig("config/logging.conf")
logger = logging.getLogger('root')

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
COMPUTE_INSTANCE="i-0a3774d4c3e971e64"

init_config(logger, CONFIG_FILE)

api = Api(app)
k=get_config("akey")
s=get_config("asec")

boto3.Session(k, s)
logger.info("Session initialized with key["+k+"] and password["+s+"].")
client = boto3.client('ec2', 'us-east-1')
unix = False
scriptdir=get_config("scriptdir")

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
        code = UNKNOWN
        r = client.describe_instances(InstanceIds=[instance_id])
        if (len(r["Reservations"]) ==1) and (len(r["Reservations"][0]["Instances"]) ==1):
            if 'State' in r["Reservations"][0]["Instances"][0]:
                code=r["Reservations"][0]["Instances"][0]["State"]["Code"]
                if(code == RUNNING):
                    # Check the detailed instance status code to make sure it is accepting connections
                    self._logger.debug("Instance code is running. Checking status details")
                    status_details = client.describe_instance_status(InstanceIds=[instance_id])
                    if((len(status_details["InstanceStatuses"]) == 1) and 
                       (status_details["InstanceStatuses"][0]["InstanceState"]["Code"] == RUNNING) and 
                        (len(status_details["InstanceStatuses"][0]["InstanceStatus"]["Details"]) ==1) and 
                        (len(status_details["InstanceStatuses"][0]["SystemStatus"]["Details"])==1)):
                        #Check instance status
                        ist:bool = (status_details["InstanceStatuses"][0]["InstanceStatus"]["Details"][0]["Status"] == "passed")
                        if(ist): 
                            self._logger.debug("Instance Status passed") 
                        else:  
                            self._logger.debug("Instance Status NOT passed")
                        #Check system status
                        sst:bool = (status_details["InstanceStatuses"][0]["SystemStatus"]["Details"][0]["Status"] == "passed")
                        if(sst): 
                            self._logger.debug("System Status passed") 
                        else:  
                            self._logger.debug("System Status NOT passed")
                        if(ist and sst):
                            code = RUNNING
                        else:
                            code = PENDING
                    else:
                        code = PENDING
                
        return {"status_code":code, "ip":IP}

    def get_server_IP(self)->string:
        if(self._IP == None):
            self._IP=get_ip(self.get_compute_instance_id())
        return self._IP

    def get_compute_instance_id(self)->string:
        return COMPUTE_INSTANCE


def get_ip(instance_id:string)->string:
    r = client.describe_instances(InstanceIds=[instance_id])
    if (len(r["Reservations"]) ==1) and (len(r["Reservations"][0]["Instances"]) ==1):
        if 'PublicIpAddress' in r["Reservations"][0]["Instances"][0]:
            return r["Reservations"][0]["Instances"][0]['PublicIpAddress']
    return None

@app.route("/")
class Jupyter(Resource):

    def __init__(self):
        self._logger = logging.getLogger('root')
        self._logger.debug("Logging initialized.")

    def get(self):
        '''
        Returns if the jupyter server is up and running or not
        '''
        #Get the IP address of the jupyter server
        try:
            ip = get_ip(COMPUTE_INSTANCE)
            if(ip == None):
                return {'status': UNKNOWN, 'details':"Cannot get copmute server IP address."}
            
            page = requests.get("http://"+ip+":9999/tree")
            if(page.status_code == 200):
                return {'status': RUNNING}
            return {'status': UNKNOWN, 'details':"Could not ping jupyter notebook. Status code returned:{status_code}".format(status_code = page.status_code)}
        except Exception as e:
            return {'status': UNKNOWN, 'details':str(e)}

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

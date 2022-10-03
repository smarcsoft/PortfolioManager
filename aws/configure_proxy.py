import argparse
import logging.config
import re

config_file = "/opt/bitnami/apache/conf/vhosts/pm-vhost.conf"

def process_arguments()->tuple:
    '''
    Return the configuration file to use
    '''

    global config_file

    parser = argparse.ArgumentParser(description="Update the reverse proxy configuration")
    parser.add_argument('--file', nargs='?',action="store",type=str, help="Public IP of the compute server")
    parser.add_argument('--public', nargs='+',action="store",type=str, help="Public IP of the compute server")
    parser.add_argument('--private', nargs='+', action="store",type=str, help="Private IP of the compute server.")
    args=parser.parse_args()
    
    public_ip=args.public[0]
    private_ip = args.private[0]
    if hasattr(args,"file"):
        config_file = args.file
    return public_ip, private_ip

def modify(line, ip):
    return re.sub(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", ip, line)

def configure(public_ip, private_ip):
    #Read the configuration file line by line and update the IP addresses accordingly
    with open(config_file, "rt") as conf:
        lines = conf.readlines()
        for i,line in enumerate(lines):
            if (line.find("ProxyPass")!=-1) or (line.find("ProxyPassReverse")!=-1) or (line.find("RequestHeader set Origin")!=-1):
                lines[i] = modify(line, public_ip)
                continue
            if (line.find("RequestHeader set Host") != -1):
                lines[i] = modify(line, private_ip)

    with open(config_file, "wt") as conf:
        conf.writelines(lines)

configure(*process_arguments())

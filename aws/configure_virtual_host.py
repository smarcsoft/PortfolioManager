import argparse
import logging.config
import re

config_file="/opt/bitnami/apache/conf/httpd.conf"
#config_file="httpd.conf"


def process_arguments():
    '''
    Return the configuration file to use
    '''
    parser = argparse.ArgumentParser(description="Update the virtual host reverse proxy configuration")
    parser.add_argument('--up',action="store_true", help="Enables the virtual host")
    parser.add_argument('--down',action="store_false", help="Disables the virtual host")
    args=parser.parse_args()

    up=True
    if hasattr(args, "up"):
        up=args.up
    if hasattr(args, "down"):
        up=args.down
    return up

def configure(up):
    if up:
        print("Enabling virtual host configuration")
    else:
        print("Disabling virtual host configuration")
    found=False
    #Read the configuration file line by line and update the IP addresses accordingly
    with open(config_file, "rt") as conf:
        lines = conf.readlines()
        for i,line in enumerate(lines):
            if (line.find("pm-vhost.conf")!=-1):
                if up:
                    lines[i] = "Include \"/opt/bitnami/apache/conf/vhosts/pm-vhost.conf\"\n"
                else:
                    lines[i] = "#Include \"/opt/bitnami/apache/conf/vhosts/pm-vhost.conf\"\n"
                found=True
                continue

    if up and (not found):
        lines.append("Include \"/opt/bitnami/apache/conf/vhosts/pm-vhost.conf\"\n")
    with open(config_file, "wt") as conf:
        conf.writelines(lines)

configure(process_arguments())

#! /usr/bin/python

"""
bob

pipe the output of this into hosts file and use it in ansible
"""

__author__ = "Rasmus E"
__author_email__ = "fatman00hot@hotmail.com"
__copyright__ = "Copyright (c) 2018 Rasmus E"
__license__ = "MIT"

from pprint import pprint
from datetime import datetime
from argparse import ArgumentParser
import sys
import time
import requests
import getpass
import json

if __name__ == '__main__':
    parser = ArgumentParser(description='Select options.')
    # Input parameters
    parser.add_argument('--file', type=str, default='hosts.txt',
                        help="file to parse one seed IP on each line")
    parser.add_argument('--apic', type=str,
                        help="IP/hostname of APIC-EM Cluster")
    parser.add_argument('--username', type=str, default="admin",
                        help="username")
    parser.add_argument('--password', type=str,
                        help="password")
    parser.add_argument('--prefix', type=str, default="Auto_",
                        help="Prefix to add to all jobs")
    parser.add_argument('--cdplevel', type=int, default=5,
                        help="cdpLevel: CDP level to which neighbor devices to be discovered,")
    parser.add_argument('--debug', action="store_true",
                        help="Only do a test run without loging in to the devices")
    parser.add_argument('--dryrun', action="store_true",
                        help="Only do a test run without and log details without changeing configuration")
    args = parser.parse_args()

    debug = args.debug
    if args.file == None:
        print("missing filename or device")
        sys.exit(1)

    #Creap code begining right now
    if args.file is not None:
        print("Starting script...")

        # Disable the showing of SSL warning from request library
        requests.packages.urllib3.disable_warnings()

        # Ask for the password if not given using commandline
        if args.password == None:
            password = getpass.getpass("Enter password for "+ args.username+":")
        else:
            password = args.password

        # API url to get the Authentication ticket for further use.
        url_ticket = 'https://'+ args.apic +'/api/v1/ticket'
        json = dict(
            username=args.username,
            password=password
        )
        print("Sending Token Request...")
        ticket_request = requests.post(url_ticket, json=json, verify=False)
        #ticket_request.status_code

        data = ticket_request.json()
        token = data['response']['serviceTicket']
        print("Got the token: "+token+ " for the next "+str(data['response']['sessionTimeout'])+" Secconds")
        headers = {'X-Auth-Token': token}

        if debug:
            print("Requesting network devices...")
            url_network_devices_count = 'https://' + args.apic + '/api/v1/network-device/count'
            headers = {'X-Auth-Token': token}
            #pprint(headers)
            count_request = requests.get(url_network_devices_count, headers=headers, verify=False)
            num_devices = count_request.json()['response']
            print("Listing all network devices("+str(num_devices)+"):")
            url_network_devices = 'https://' + args.apic + '/api/v1/network-device'

            #pprint(headers)
            count_request = requests.get(url_network_devices, headers=headers, verify=False)
            num_devices = count_request.json()
            for devs in num_devices['response']:
                pprint(devs['hostname'])

        if not args.dryrun:
            print("Adding discovery Jobs...")

            # Opening list of devices
            file = open(args.file, 'r', newline=None)
            for line in file:
                print(args.prefix + line.strip() + "... ", end='')

                # API Url for discovery task
                url_network_devices = 'https://' + args.apic + '/api/v1/discovery'
                device_addition = dict(
                    cdpLevel=args.cdplevel,
                    name=args.prefix + line.strip(),
                    discoveryType="auto cdp discovery",
                    ipAddressList=line.strip(),
                    protocolOrder="ssh"
                )

                discovery_request = requests.post(url_network_devices, json=device_addition, headers=headers, verify=False)
                print(discovery_request.status_code)
                if debug:
                    pprint(discovery_request.json())
# Copyright (C) Simplicify, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by William Michael Turner <williammichaelturner@gmail.com>, 2015

import etcd
import uuid
import json
import random
import socket
import operator
import time
import boto
import boto.s3.connection
import dns.resolver
import dns.zone
from dns.exception import DNSException
from dns.rdataclass import *
from dns.rdatatype import *
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from prometheus_client import start_http_server, Summary
class commands:
    def __init__(self, simplicify, provisioner_type):
        self.provisioner_type = provisioner_type
        self.client_etcd = simplicify.client_etcd
        self.client_s3 = simplicify.client_s3
        self.config = simplicify.SimplicifyConfig
        self.hostname = socket.gethostname()

    def ls_SRV(self, service_name):
        """
        Note: This function retrieves all configured S
        Args:
            service_name:  The symbolic name of the desired service, as defined in Assigned
        Numbers [STD 2] or locally.  An underscore (_) is prepended to
        the service identifier to avoid collisions with DNS labels that
        occur in nature.

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully listed all service records with the specified service name ({})".format(service_name)

        try:
            response = dns.resolver.query(service_name, 'SRV')
        except:
                explanation = "An unknown error occurred listing records for the specified service ({})".format(service_name)
                status = 500
                return [ 1, status, explanation, "" ]

        results_list = []
        for rdata in response:
            results_list.append(str(rdata.target).rstrip('.'))

        payload = results_list
        returns = [ prog_status, http_status, explanation, payload ]

        return returns


    def ls_A(self, dns_name):
        """
        Note: This function retrieves all configured S
        Args:
            service_name:  The symbolic name of the desired service, as defined in Assigned
        Numbers [STD 2] or locally.  An underscore (_) is prepended to
        the service identifier to avoid collisions with DNS labels that
        occur in nature.

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully listed all service records with the specified DNS name ({})".format(dns_name)

        try:
            response = dns.resolver.query(dns_name, 'A')
        except:
                explanation = "An unknown error occurred listing records for the specified DNS name ({})".format(dns_name)
                status = 500
                return [ 1, status, explanation, "" ]

        results_list = []
        for rdata in response:
            results_list.append(str(rdata))

        payload = results_list
        returns = [ prog_status, http_status, explanation, payload ]

        return returns

    def create_A(self, record_name, ip_address):
        """
        Note: This function creates an A record on a bind9 DNS server
        Args:
            record_name:  FQDN for record

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully created specified A record ({})".format(record_name)

        domain = "simplicify.com"
        print "Getting zone object for domain", domain
        zone_file = "/etc/bind/zones/db.%s" % domain

        try:
            zone = dns.zone.from_file(zone_file, domain)
            print "Zone origin:", zone.origin
        except DNSException, e:
            print e.__class__, e

        rdataset = zone.find_rdataset(record_name, rdtype=A, create=True)
        rdata = dns.rdtypes.IN.A.A(IN,A, address=ip_address)
        rdataset.add(rdata, ttl=86400)
        new_zone_file = "new.db.%s" % domain

        try:
            zone.to_file(new_zone_file)
        except:
                explanation = "An unknown error occurred adding the specified A record ({})".format(dns_name)
                status = 500
                return [ 1, status, explanation, "" ]

        payload = ""
        returns = [ prog_status, http_status, explanation, payload ]

        return returns

    def create_SRV(self, service_name, service_port, A_record):
        """
        Note: This function creates a SRV record on a bind9 DNS server
        Args:
            service_name:  Name of service
            service_port:  Service Port
            A_record: A reccord defining where service is found

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully created specified SRV record (Service: {} Port: {} A Record: {})".format(service_name, service_port, A_record)

        domain = "simplicify.com"
        zone_file = "/etc/bind/zones/db.%s" % domain
        new_zone_file = "new.db.%s" % domain
        try:
            zone = dns.zone.from_file(zone_file, domain)
        except DNSException, e:
            print e.__class__, e
        n = dns.name.from_text(A_record)
        rdataset = zone.find_rdataset(service_name, rdtype='SRV', create=True)
        rdata = dns.rdtypes.IN.SRV.SRV(IN,SRV,0,0,service_port,target=n)
        rdataset.add(rdata, ttl=86400)
        print str(rdataset)
        print str(rdata)
        try:
            zone.to_file(new_zone_file)
        except:
                explanation = "An unknown error occurred adding the specified SRV record (Service: {} Port: {} A Record: {})".format(service_name, service_port, A_record)
                status = 500
                return [ 1, status, explanation, "" ]

        payload = ""
        returns = [ prog_status, http_status, explanation, payload ]

        return returns

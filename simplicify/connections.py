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
import logging
import logstash
import sys
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from prometheus_client import start_http_server, Summary

class open:
    """
    Note: Class establishes connections that will be used throughout various classes in Simplicify

    Args:
        clusterFQDN: Fully qualified domain that can be used for etcd and s3 connections
        SimplicifyConfig: A configuration dictionary that is stored as a JSON file.  More documentation on individual configuration attirbutes is stored in the config.json file

    Returns:
        returns: All functionality of the Simplicify platform.  This is the parent object of the Simplicify namespace.

    """
    def __init__(self, clusterFQDN, SimplicifyConfig):
        self.clusterFQDN = clusterFQDN
        self.SimplicifyConfig = SimplicifyConfig

    def etcd(self):
        """
        Note: This method establishes an etcd connection using settings in input during class initialization

        Args:
            self.SimplicifyConfig: A configuration dictionary that is stored as a JSON file.  More documentation on individual configuration attirbutes is stored in the config.json file

        Returns:
            returns: On success this method returns an etcd client object

        """

        host_etcd = self.SimplicifyConfig['etcd']['uri']
        port_etcd = self.SimplicifyConfig['etcd']['port']

        try:
            self.client_etcd = etcd.Client(host=host_etcd, port=port_etcd)
        except etcd.EtcdConnectionFailed:
            explanation = "Connecting to the specified etcd host ({}) on the specified port ({}) failed.".format(host_etcd, port_etcd)

            returns = [ prog_status, http_status, explanation, self.client_etcd ]

        return self.client_etcd


    def logstash(self):
        """
        Note: This method establishes a connection to logstash using settings in input during class initialization

        Args:
            self.SimplicifyConfig: A configuration dictionary that is stored as a JSON file.  More documentation on individual configuration attirbutes is stored in the config.json file

        Returns:
            returns: On success this method returns a logstash client object

        """
        host = self.SimplicifyConfig['logstash']['host']
        port = self.SimplicifyConfig['logstash']['port']

        self.logger = logging.getLogger('python-logstash-logger')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logstash.TCPLogstashHandler(host, 5000, version=1))

        fields = {
            'prog_status': '0',
            'http_status': '200',
            'explanation': 'Simplicify component ({}) is starting up, and is successfully logging'.format(self.program_name)
            }

        self.logger.info('simplicify: fields', fields=fields)

        return self.logger


    def s3(self):
        """
        Note: This method establishes an s3 connection using settings in input during class initialization

        Args:
            self.SimplicifyConfig: A configuration dictionary that is stored as a JSON file.  More documentation on individual configuration attirbutes is stored in the config.json file

        Returns:
            returns: On success this method returns an etcd client object

        """

        access_key = self.SimplicifyConfig['s3']['access_key']
        secret_key = self.SimplicifyConfig['s3']['secret_key']
        host_s3 = self.SimplicifyConfig['s3']['host']
        security_setting = (self.SimplicifyConfig['s3']['is_secure'] == "True")

        self.client_s3 = boto.connect_s3(
        aws_access_key_id = access_key,
        aws_secret_access_key = secret_key,
        host = host_s3,
        is_secure=security_setting,
        calling_format = boto.s3.connection.OrdinaryCallingFormat(),
        )

        return self.client_s3


    def omapi(self):
        """
        Note: This method establishes an omapi connection to isc-dhcp-server using settings in input during class initialization

        Args:
            self.SimplicifyConfig: A configuration dictionary that is stored as a JSON file.  More documentation on individual configuration attirbutes is stored in the config.json file

        Returns:
            returns: On success this method returns an omapi client object

        """

        keyname = self.SimplicifyConfig['omapi']['keyname']
        secret  = self.SimplicifyConfig['omapi']['secret']
        server  = self.SimplicifyConfig['omapi']['server']
        port    = self.SimplicifyConfig['omapi']['port']

        try:
            self.client_omapi = pypureomapi.Omapi(server, port, keyname, secret)
        except pypureomapi.OmapiError, err:
            print "OMAPI error: %s" % (err,)
            sys.exit(1)

        return self.client_omapi

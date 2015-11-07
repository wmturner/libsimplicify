# Simplicify Library
import etcd
import uuid
import json
import random
import socket
import operator
import time
import boto
import boto.s3.connection
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from prometheus_client import start_http_server, Summary

NODE_TYPE="baremetal"

class simplicify:
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

    def connect_etcd(self):
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

    def connect_s3(self):
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

class commands:
    def __init__(self, simplicify, provisioner_type):
        self.provisioner_type = provisioner_type
        self.client_etcd = simplicify.client_etcd
        self.client_s3 = simplicify.client_s3
        self.config = simplicify.SimplicifyConfig
        self.hostname = socket.gethostname()

    def queue_build(self, type, ttl, provisioner, settings, appliance_name):
        """
        Note: This method establishes an s3 connection using settings in input during class initialization

        Args:
            type: The type of build (defined in and validated against config.json)
            ttl: Total time build will exist after initialization
            provisioner: Provisioner used for post configuration of the build (defined in and validated against config.json)
            settings: Settings used for provisioner configuration (defined in and validated against config.json)
            appliance_name: Colloquial name used to casually descibe the build (uniqueness is not required or enforce)
        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload (with .name, and .creation_date methods)

        """

        self.type = type
        self.ttl = ttl
        self.provisioner = provisioner
        self.settings = settings
        self.appliance_name = appliance_name

        jobID = uuid.uuid1()

        # Error handling code to be moved to validation library
        if provisioner in self.config["build"]["provisioner"]:

            for key in self.settings:
                print key
                if key in self.config["build"]["settings"][self.provisioner]:
                    print "Success"
                else:
                    print "fail"
        else:
            print "epic fail"

        if type in self.config["build"]["type"]:
            print "Success"
        else:
            print "Epic Fail"

        job = { "provisioner": self.provisioner,
                "settings": self.settings,
                "ttl": self.ttl,
                "appliance_name": self.appliance_name }

        if type == "baremetal":
            self.client_etcd.write('/build/{}/{}'.format(type,jobID), json.dumps(job))


    def rm_build(self, type, buildID):
        """
        Note: This method removes a queued build
        Args:
            type: The type of build (defined in and validated against config.json)
            appliance_name: Colloquial name used to casually descibe the build (uniqueness is not required or enforce)
        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        try:
            self.client_etcd.read("/build/{}/{}".format(type, buildID))
            self.client_etcd.delete("/build/{}/{}".format(type, buildID))
        except etcd.EtcdKeyNotFound:
            print "key not found"
        return

    def get_build(self, type, buildID):
        """
        Note: This method fetches the information associated with a buildID

        Args:
            type: The type of build (defined in and validated against config.json)
            appliance_name: Colloquial name used to casually descibe the build (uniqueness is not required or enforce)
        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully fetched contents of the {} build with buildID {}".format(type, buildID)

        try:
            print self.client_etcd.read("/build/{}/{}".format(type, buildID))
        except etcd.EtcdKeyNotFound:
            explanation = "No key found for the specified build type {} with the specified buildID {}".format(type, buildID)


        returns = [ prog_status, http_status, explanation, pick['key'] ]

        return returns



    def pollBuildQueue(self, type):
        """
        Note: This method polls the build queues for a specified node type, and submits a bid if resources are free

        Args:
            type: The type of build (defined in and validated against config.json)
            appliance_name: Colloquial name used to casually descibe the build (uniqueness is not required or enforce)
        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully won a bid for a {} build".format(type)

        # Execute a recursive query to etcd and only show a single new value after the request to the cluster was made:
        self.queue = self.client_etcd.read('/build/{}'.format(self.type), recursive = True)._children

        pick = random.choice(self.queue)
        print pick['key']
        if pick:
            # Recapture the jobID by assigning the end of the complete URI for the key (UUID that uniquely desecribes the job prescribed from the controller):
            buildID = pick['key'].rsplit('/',1)[1]

            winner = self._bid(buildID)
            # If the current worker process believes itis the winner, then begin performing the provisioning task:
            if winner==self.hostname:
                try:
                    # Double check to make sure another node has not claimed winner for the jobID
                    out_of_syncWinner = self.client_etcd.read('/winner/{}/{}/{}'.format(self.type, buildID, self.hostname))
                    print "WINNER ALREADY SELECTED, YOU ARE OUT OF SYNC"

                # During good cluster behavior, the below condition should be triggered
                except etcd.EtcdKeyNotFound:

                    # If node truly is the winner, then write it to the winner queue for record
                    # Inform the cluster that the provisioning job is in progress
                    self.client_etcd.write('/winner/{}/{}/{}'.format(type, buildID, self.hostname), pick['value'])
                    self.client_etcd.write('/inprogress/{}/{}'.format(type, buildID), "True")

                    # Delete the job from the build queue
                    self.client_etcd.delete(pick['key'])
                    print "Win"
                #os.chroot("/simplicify/chroot")
                #call(["chef-solo", "-o", "nginx"])
                exit

        returns = [ prog_status, http_status, explanation, pick['key'] ]

        return returns

    def _bid(self,jobID):
        # Create a bid
        # A bid is an integer value between 1 and 1000, and the cluster member with the highest number wins:
        bid = random.randrange(100, 1000, 3)
        # Write the worker's bid to the appropriate etcd folder:
        self.client_etcd.write('/bid/{}/{}/{}'.format(NODE_TYPE, jobID, self.hostname), bid)

        # Wait a minute until all workers have had an opportunity to bid:
        time.sleep(1)
        bid_queue = self.client_etcd.read('/bid/{}/{}'.format(NODE_TYPE, jobID), recursive = True)

        # Create a quorum dictionary used to store all bids from the various members and determine which worker is the winner
        quorum_dict = {}
        for bid in bid_queue._children:
            quorum_dict.update({ bid['key'].rsplit('/',1)[1]: bid['value'] })

        winner = max(quorum_dict.iteritems(), key=operator.itemgetter(1))[0]
        return winner

    def put_chroot(self, bkt, name, file_path):
        """
        Note: This method adds a chroot environment (tar, zip, 7zip, tar.gz, .gzip) to s3, and creates a correspoding entry in etcd

        Args:

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload (with .name, and .creation_date methods)

        """
        new_obj = s3_put_file(bkt, name, file_path)

        # Check and make sure object is successfully created.  Object will not be overwritten if it already exists
        # If the chroot was sucessfully added to s3, use etcd to keep track of the metadata
        if not new_obj == 1:
            chroot_meta_data = { "bucket": bkt,
                                 "name": name
                               }
            self.client_etcd.write('/artifacts/chroots/{}/{}'.format(bkt, name), choot_meta_data)


    def s3_ls_bkts(self):
        """
        Note: This function lists all s3 buckets within the configured s3 endpoint

        Args:

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload (with .name, and .creation_date methods)

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully listed all buckets in the connected endpoint ({}).".format(self.config['s3']['host'])

        try:
            bucket_list = self.client_s3.get_all_buckets()
        except:
            explanation = "An unknown error occurred while trying to list the buckets at the connected s3 endpoint ({}).".format(self.config['s3']['host'])
            return [ 1, 500, explanation, "" ]

        returns = [ prog_status, http_status, explanation, bucket_list ]

        return returns


    def s3_ls_bkt(self, bkt):
        """
        Note: This function lists the content(s) of an s3 bucket.

        Args:
            bkt: The source s3 bucket.

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully listed the contents specified bucket ({}).".format(bkt)

        try:
            bucket = self.client_s3.get_bucket(bkt)
        except boto.exception.S3ResponseError, [status, response, body]:
            if status == 404:
                explanation = "The bucket you requested ({}) to list the contents of could not be found.".format(bkt)
            else:
                status = 500
                explanation = "An unknown error occurred while trying to list the contents of the specified bucket ({}).".format(bkt)
            return [ 1, status, explanation, "" ]

        ls_bkt = bucket.list()

        returns = [ prog_status, http_status, explanation, ls_bkt ]

        return returns


    def s3_rm_key(self, bkt, key):
        """
        Note: This function a moves a file object stored in s3 to a predefined delete bucket.  This method allows the apperance of a delete operation, while maintaining the option to restore

        Args:
            bkt: The source s3 bucket.
            key: The source key representing the file object.

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully removed the specifiied file ({}) from specified bucket ({})".format(key, bkt)

        try:
            src = self.client_s3.get_bucket(bkt)
        except boto.exception.S3ResponseError, [status, response, body]:
            explanation = "The bucket you requested ({}) to delete the file ({}) from could not be found.".format(bkt, key)
            return [ 1, status, explanation, "" ]

        try:
            rm_bkt = self.client_s3.get_bucket('{}'.format(self.config['s3']['rm_bkt']))
        except boto.exception.S3ResponseError, [status, response, body]:
            explanation = "The connection to s3 is established, but the delete bucket cannot be found"
            return [ 1, status, explanation, "" ]

        try:
            rm_bkt.copy_key(key, bkt, key)
        except boto.exception.S3CopyError, [status, response, body]:
            if status == 404:
                explanation = "An unknown error occured while copying the file you requested ({}) to delete from bucket ({}).".format(key, bkt)
            else:
                explanation = "An unknown error occured while moving the specified file ({}) from the source bucket ({})".format(bkt, key)
            return [ 1, status, explanation, "" ]

        except boto.exception.S3ResponseError, [status, response, body]:
            explanation = "The file you requested ({}) to delete from bucket ({}) could not be found.".format(key, bkt)

            return [ 1, status, explanation, "" ]

        try:
            src.delete_key(key)
        except boto.exception.S3ResponseError, [status, response, body]:
            explanation = "An unknown error occured while deleting the specified file ({}) from the bucket ({})".format(bkt, key)

            return [ 1, status, explanation, "" ]

        returns = [ prog_status, http_status, explanation, "" ]

        return returns


    def s3_put_file(self, bkt, key, file_path, overwrite=False):
        """
        Note: This function stores a file in s3 if it does not exist, but will overwrite if specifed

        Args:
            bkt: The target s3 bucket.
            key: The target key representing the file object.
            file_path: The path of the file to put at the target bucket/key s3
            overwrite: Defaults to False, but allows for over-write behavior

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully uploaded the specified file ({}) to specified bucket ({})".format(key, bkt)

        # Instantiate the bucket that the file is desired to be stored in
        try:
            bucket = self.client_s3.get_bucket(bkt)
        except boto.exception.S3ResponseError, [status, response, body]:
            explanation = "The connection to s3 is established, but the bucket ({}) cannot be found".format(bkt)
            return [ 1, status, explanation ]

        existance_test = bucket.get_key(key)
        if existance_test == None:
            pass
        elif overwrite == True:
            pass
        else:
            status = 204
            explanation = "File already exists at the specified key ({}) in the specified bucket ({})".format(key, bkt)
            return [ 1, status, explanation ]

        # Create a the key used to store the file
        try:
            new_key = bucket.new_key(key)
        except boto.exception.S3CreateError, [status, response, body]:
            explanation = "An error occurred creating the key in the requested bucket ({}) to store the specified file ({}).".format(bkt, key)
            return [ status, explanation ]

        # Upload file contents to key just created
        try:
            new_key.set_contents_from_filename(file_path)
        except boto.exception.S3DataError, [status, args]:
            explanation = "An error occurred creating the key in the requested bucket ({}) to store the specified file ({}).".format(bkt, key)
            return [ status, explanation ]

        # Set private ACL on file
        try:
            new_key.set_canned_acl('private')
        except:
            explanation = "An unknown error occurred setting the ACL on file {}".format(key)
            status = 500
            return [ status, explanation ]

        returns = [ prog_status, http_status, explanation ]

        return returns

    def s3_get_file_url(self, bkt, key):
        """
        Note: This function generates a url to to download a file from an s3 bucket

        Args:
            bkt: The target s3 bucket.
            key: The target key representing the file object.

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully generate url for specified file ({}) in specified bucket ({})".format(key, bkt)

        try:
            bucket = self.client_s3.get_bucket(bkt)
        except boto.exception.S3ResponseError, [status, response, body]:
            explanation = "The connection to s3 is established, but the bucket ({}) cannot be found".format(bkt)
            return [ 1, status, explanation, "" ]

        req_key = bucket.get_key(key)
        if req_key == None:
            status = 404
            explanation = "A file cannot be found at the specified key ({}) in the specified bucket ({})".format(key, bkt)
            return [ 1, status, explanation, "" ]
        else:
            try:
                obj_url = req_key.generate_url(3600, query_auth=True, force_http=True)
            except:
                explanation = "An unknown error occurred setting the ACL on file {}".format(key)
                status = 500
                return [ 1, status, explanation, "" ]

        payload = obj_url
        returns = [ prog_status, http_status, explanation, payload ]

        return returns

############### DNS METHODS #################
    def ls_srv(self, service_name):
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

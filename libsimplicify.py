 #Simplicify Library

import etcd
import uuid
import json
import random
import socket
import operator
import time
import boto
import boto.s3.connection

NODE_TYPE="baremetal"

class simplicify:
    def __init__(self, clusterFQDN, SimplicifyConfig):
        self.clusterFQDN = clusterFQDN
        self.SimplicifyConfig = SimplicifyConfig

    def connect_etcd(self):
        
        host_etcd = self.SimplicifyConfig['etcd']['uri']
        port_etcd = self.SimplicifyConfig['etcd']['port']

        self.client_etcd = etcd.Client(host=host_etcd, port=port_etcd)

        return self.client_etcd

    def connect_s3(self):

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


    def rm_build(self, type, jobID):
        
        try: 
            self.client_etcd.read("/build/{}/{}".format(type, jobID))
            self.client_etcd.delete("/build/{}/{}".format(type, jobID))
        except etcd.EtcdKeyNotFound:
            print "key not found"
        return

    def echo_build(self, type, jobID, value):
        try:
            self.client_etcd.read("/build/{}/{}".format(type, jobID))
        except etcd.EtcdKeyNotFound:
            print "Key not found"
            self.client_etcd.write('/build/{}/{}'.format(type,jobID), value)
        
        

    def pollBuildQueue(self):
       # print "Beginning Polling loop"

        # Execute a recursive query to etcd and only show a single new value after the request to the cluster was made:
        self.queue = self.client_etcd.read('/build/{}'.format(NODE_TYPE), recursive = True)._children
        
        pick = random.choice(self.queue)        
        print pick['key']
        if pick:
            # Recapture the jobID by assigning the end of the complete URI for the key (UUID that uniquely desecribes the job prescribed from the controller):
            jobID = pick['key'].rsplit('/',1)[1]

            winner = self._vote(jobID)
            # If the current worker process believes itis the winner, then begin performing the provisioning task:
            if winner==self.hostname:
                try:
                    # Double check to make sure another node has not claimed winner for the jobID
                    out_of_syncWinner = self.client_etcd.read('/winner/{}/{}/{}'.format(NODE_TYPE, jobID, self.hostname))
                    print "WINNER ALREADY SELECTED, YOU ARE OUT OF SYNC"

                # During good cluster behavior, the below condition should be triggered
                except etcd.EtcdKeyNotFound:

                    # If node truly is the winner, then write it to the winner queue for record
                    # Inform the cluster that the provisioning job is in progress
                    self.client_etcd.write('/winner/{}/{}/{}'.format(NODE_TYPE, jobID, self.hostname), pick['value'])
                    self.client_etcd.write('/inprogress/{}/{}'.format(NODE_TYPE, jobID), "True")

                    # Delete the job from the build queue
                    self.client_etcd.delete(pick['key'])
        #        self.processJob()
                    print "Win"
                #os.chroot("/simplicify/chroot")
                #call(["chef-solo", "-o", "nginx"])
                exit

        return 0

    def _vote(self,jobID):
        # Create a vote
        # A vote is an integer value between 1 and 1000, and the cluster member with the highest number wins:
        vote = random.randrange(100, 1000, 3)
        # Write the worker's vote to the appropriate etcd folder:
        self.client_etcd.write('/vote/{}/{}/{}'.format(NODE_TYPE, jobID, self.hostname), vote)

        # Wait a minute until all workers have had an opportunity to vote:
        time.sleep(1)
        vote_queue = self.client_etcd.read('/vote/{}/{}'.format(NODE_TYPE, jobID), recursive = True)

        # Create a quorum dictionary used to store all votes from the various members and determine which worker is the winner
        quorum_dict = {}
        for vote in vote_queue._children:
            quorum_dict.update({ vote['key'].rsplit('/',1)[1]: vote['value'] })

        winner = max(quorum_dict.iteritems(), key=operator.itemgetter(1))[0]
        return winner
    
 #   def put_chroot(self):
 #       chroot_id
 #       self.client_etcd.write('/artifacts/chroots/{}/'.format(, jobID, self.hostname), vote) 
    
    def provisioners(self):
        
        def chef_chroot(self):
            os.chroot("/simplicify/chroot")
            call(["chef-solo", "-o", "nginx"])
            
            return
        return
    
    def ls_bkts(self):
        for bucket in self.client_s3.get_all_buckets():
            print "{name}\t{created}".format(
                    name = bucket.name,
                    created = bucket.creation_date,
            )
        return

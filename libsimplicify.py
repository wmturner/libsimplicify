 #Simplicify Library

import etcd
import uuid
import json
import random
import socket
import operator
import time
NODE_TYPE="baremetal"

class simplicify:
    def __init__(self, clusterFQDN, SimplicifyConfig):
        self.clusterFQDN = clusterFQDN
        self.SimplicifyConfig = SimplicifyConfig

    def connect(self):
        self.client = etcd.Client(host='controller1.simplicify.com', port=2379)
        return self.client


class commands:
    def __init__(self, simplicify, provisioner_type):
        self.provisioner_type = provisioner_type
        self.client = simplicify.client
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
            self.client.write('/build/{}/{}'.format(type,jobID), json.dumps(job))


    def rm_build(self, type, jobID):
        
        try: 
            self.client.read("/build/{}/{}".format(type, jobID))
            self.client.delete("/build/{}/{}".format(type, jobID))
        except etcd.EtcdKeyNotFound:
            print "key not found"
        return

    def echo_build(self, type, jobID, value):
        try:
            self.client.read("/build/{}/{}".format(type, jobID))
        except etcd.EtcdKeyNotFound:
            self.client.write('/build/{}/{}'.format(type,jobID), value)
        
        

    def pollBuildQueue(self):
       # print "Beginning Polling loop"

        # Execute a recursive query to etcd and only show a single new value after the request to the cluster was made:
        self.queue = self.client.read('/build/{}'.format(NODE_TYPE), recursive = True)._children
        
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
                    out_of_syncWinner = self.client.read('/winner/{}/{}/{}'.format(NODE_TYPE, jobID, self.hostname))
                    print "WINNER ALREADY SELECTED, YOU ARE OUT OF SYNC"

                # During good cluster behavior, the below condition should be triggered
                except etcd.EtcdKeyNotFound:

                    # If node truly is the winner, then write it to the winner queue for record
                    # Inform the cluster that the provisioning job is in progress
                    self.client.write('/winner/{}/{}/{}'.format(NODE_TYPE, jobID, self.hostname), pick['value'])
                    self.client.write('/inprogress/{}/{}'.format(NODE_TYPE, jobID), "True")

                    # Delete the job from the build queue
                    self.client.delete(pick['key'])
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
        self.client.write('/vote/{}/{}/{}'.format(NODE_TYPE, jobID, self.hostname), vote)

        # Wait a minute until all workers have had an opportunity to vote:
        time.sleep(1)
        vote_queue = self.client.read('/vote/{}/{}'.format(NODE_TYPE, jobID), recursive = True)

        # Create a quorum dictionary used to store all votes from the various members and determine which worker is the winner
        quorum_dict = {}
        for vote in vote_queue._children:
            quorum_dict.update({ vote['key'].rsplit('/',1)[1]: vote['value'] })

        winner = max(quorum_dict.iteritems(), key=operator.itemgetter(1))[0]
        return winner
    
    
    def provisioners(self):
        
        def chef_chroot(self):
            os.chroot("/simplicify/chroot")
            call(["chef-solo", "-o", "nginx"])
            
            return
        return

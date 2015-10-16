# Simplicify Library

import etcd
import uuid
import json

client = etcd.Client(host='controller1.simplicify.com', port=2379)

#with open('config.json') as data_file:
#    config = json.load(data_file)



class simplicify:
    def __init__(self, clusterFQDN, SimplicifyConfig):
        self.clusterFQDN = clusterFQDN
        self.SimplicifyConfig = SimplicifyConfig

    def connect(self):
        self.client = etcd.Client(host='controller1.simplicify.com', port=2379)
        return self.client


class provisioner:
    def __init__(self, simplicify, provisioner_type):
        self.provisioner_type = provisioner_type
        self.client = simplicify

    def queue_build(self, type, ttl, provisioner, settings, appliance_name):
        self.type = type
        self.ttl = ttl
        self.provisioner = provisioner
        self.settings = settings
        self.appliance_name = appliance_name


        jobID = uuid.uuid1()


        # Error handling code to be moved to validation library
        if provisioner in self.client.SimplicifyConfig["build"]["provisioner"]:

            for key in self.settings:
                print key
                if key in self.client.SimplicifyConfig["build"]["settings"][self.provisioner]:
                    print "Success"
                else:
                    print "fail"
        else:
            print "epic fail"

        if type in self.client.SimplicifyConfig["build"]["type"]:
            print "Success"
        else:
            print "Epic Fail"




        job = { "provisioner": self.provisioner,
                "settings": self.settings,
                "ttl": self.ttl,
                "appliance_name": self.appliance_name }

        if type == "baremetal":
            client.write('/build/{}/{}'.format(type,jobID), json.dumps(job))


    def pollBuildQueue(self):
        print "Beginning Polling loop"

        # Create a vote
        # A vote is an integer value between 1 and 1000, and the cluster member with the highest number wins:
        vote = random.randrange(100, 1000, 3)

        # Execute a recursive query to etcd and only show a single new value after the request to the cluster was made:
        self.queue = client.read('/build/{}'.format(NODE_TYPE), recursive = True, wait = True)

        # Recapture the jobID by assigning the end of the complete URI for the key (UUID that uniquely desecribes the job prescribed from the controller):
        jobID = self.queue.key.rsplit('/',1)[1]

        # Write the worker's vote to the appropriate etcd folder:
        client.write('/vote/{}/{}/{}'.format(NODE_TYPE, jobID, host), vote)

        # Wait a minute until all workers have had an opportunity to vote:
#        time.sleep(60)
        vote_queue = client.read('/vote/{}/{}'.format(NODE_TYPE, jobID), recursive = True)

        # Create a quorum dictionary used to store all votes from the various members and determine which worker is the winner
        quorum_dict = {}
        for vote in vote_queue._children:
            quorum_dict.update({ vote['key'].rsplit('/',1)[1]: vote['value'] })

        winner = max(quorum_dict.iteritems(), key=operator.itemgetter(1))[0]

        # If the current worker process believes itis the winner, then begin performing the provisioning task:
        if winner==host:
            try:
                # Double check to make sure another node has not claimed winner for the jobID
                out_of_syncWinner = client.read('/winner/{}/{}/{}'.format(NODE_TYPE, jobID, host))
                print "WINNER ALREADY SELECTED, YOU ARE OUT OF SYNC"

            # During good cluster behavior, the below condition should be triggered
            except etcd.EtcdKeyNotFound:

                # If node truly is the winner, then write it to the winner queue for record
                # Inform the cluster that the provisioning job is in progress
                client.write('/winner/{}/{}/{}'.format(NODE_TYPE, jobID, host), self.queue.value)
                client.write('/inprogress/{}/{}'.format(NODE_TYPE, jobID), "True")

                # Delete the job from the build queue
                client.delete(self.queue.key)
                self.processJob()
                #os.chroot("/simplicify/chroot")
                #call(["chef-solo", "-o", "nginx"])


        return 0
    
    def provisioners(self):
        
        def chef_chroot(self):
            os.chroot("/simplicify/chroot")
            call(["chef-solo", "-o", "nginx"])
            
            return
        return

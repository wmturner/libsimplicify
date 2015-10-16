import etcd
import uuid
import json
import random
import operator
import time
import os
import urllib
from subprocess import call

NODE_TYPE="baremetal"
host = "node1.simplicify.com"
client = etcd.Client(host='node1.simplicify.com', port=2379)


class worker:
    def __init__(self, clusterFQDN, clusterPort):
        self.clusterFQDN = clusterFQDN
        self.clusterPort = clusterPort

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
    
    def processJob(self):
# {u'appliance_name': u'testing123', u'provisioner': u'chef', u'settings': {u'chroot_url': u'test', u'cookbooks': [u'nginx'], u'cheffile': u'http://controller1.simplicify.com/cheffiles/simplicify_test/Cheffile'}, u'ttl': u'5'}
        job = json.loads(self.queue.value)
        print job
        print job['settings']['chroot_url']
        urllib.urlretrieve ("http://controller1.simplicify.com/cheffiles/simplicify_test/Cheffile", "Cheffile")



if __name__ == '__main__':
    while True:
        Worker = worker("node1.simplicify.com", "2379")
        Worker.pollBuildQueue()

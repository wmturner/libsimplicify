import etcd
import uuid
import json
import random
import operator
import threading


NODE_TYPE="baremetal"
host = "controller1.simplicify.com"
client = etcd.Client(host='controller1.simplicify.com', port=2379)


class worker:
    def __init__(self, clusterFQDN, clusterPort):
        self.clusterFQDN = clusterFQDN
        self.clusterPort = clusterPort

    def pollBuildQueue(self):
        vote = random.randrange(100, 1000, 3)
        queue = client.read('/build/{}'.format(NODE_TYPE), recursive = True, wait = True)
        
        jobID = queue.key.rsplit('/',1)[1]
        
        client.write('/vote/{}/{}/{}'.format(NODE_TYPE, jobID, host), vote)
        vote_queue = client.read('/vote/{}/{}'.format(NODE_TYPE, jobID), recursive = True)

        quorum_dict = {}
        
        for vote in vote_queue._children:
            quorum_dict.update({ vote['key'].rsplit('/',1)[1]: vote['value'] })
        
        winner = max(quorum_dict.iteritems(), key=operator.itemgetter(1))[0]
         
        if winner==host:
            print "I win!" 

Worker = worker("controller1.simplicify.com", "2379")

Worker.pollBuildQueue()

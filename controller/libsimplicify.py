# Simplicify Library

import etcd
import uuid
import json

client = etcd.Client(host='controller1.simplicify.com', port=2379)

#with open('config.json') as data_file:
#    config = json.load(data_file)

class provisioner:
    def __init__(self, clusterFQDN, SimplicifyConfig, provisioner_type):
        self.clusterFQDN = clusterFQDN
        self.SimplicifyConfig = SimplicifyConfig
        self.provisioner_type = provisioner_type

    def queue_build(self, type, ttl, provisioner, settings, appliance_name):
        self.type = type
        self.ttl = ttl
        self.provisioner = provisioner
        self.settings = settings
        self.appliance_name = appliance_name


        jobID = uuid.uuid1()


        # Error handling code to be moved to validation library
        if provisioner in self.SimplicifyConfig["build"]["provisioner"]:

            for key in self.settings:
                print key
                if key in self.SimplicifyConfig["build"]["settings"][self.provisioner]:
                    print "Success"
                else:
                    print "fail"
        else:
            print "epic fail"

        if type in self.SimplicifyConfig["build"]["type"]:
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
        print "hello"
        vote = random.randrange(0, 1000, 3)
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
        return 0

import etcd
import uuid
import json

client = etcd.Client(host='controller1.simplicify.com', port=2379)

with open('config.json') as data_file:    
    config = json.load(data_file)

class Provision:
    def __init__(self, clusterFQDN, clusterPort):
        self.clusterFQDN = clusterFQDN
        self.clusterPort = clusterPort

    def build(self, type, ttl, provisioner, settings, appliance_name):
        self.type = type
        self.ttl = ttl
        self.provisioner = provisioner
        self.settings = settings
        self.appliance_name = appliance_name
        

        jobID = uuid.uuid1()
        if provisioner in config["build"]["provisioner"]:
            print "Success"
           
            for key in self.settings:
                print key
                if key in config["build"]["settings"][self.provisioner]:
                    print "Success"
                else:
                    print "fail"
        else:
            print "epic fail"

        if type in config["build"]["type"]:
            print "Success"
        else: 
            print "Epic Fail"
        job = { "provisioner": self.provisioner,
                "settings": self.settings,
                "ttl": self.ttl,
                "appliance_name": self.appliance_name }

        if type == "baremetal":
            client.write('/build/{}/{}'.format(type,jobID), json.dumps(job))




test_settings = { "cheffile": "http://controller1.simplicify.com/cheffiles/simplicify_test/Cheffile",
                  "cookbooks": ["nginx"] }
provision_test = Provision('test', '22')

provision_test.build('baremetal', '5', 'chef', test_settings, 'testing123')

import etcd
import uuid
import json
import random
import operator
import time
import os
import urllib
import socket
from subprocess import call
from libsimplicify import simplicify
from libsimplicify import commands
with open('../controller/config.json') as data_file:
    config = json.load(data_file)

NODE_TYPE="baremetal"
host = socket.gethostname()

simplicify_instance = simplicify('controller1.simplicify.com', config)
print dir(simplicify_instance)
simplicify_instance.connect()
print dir(simplicify)
#client = etcd.Client(host='controller1.simplicify.com', port=2379)
cmdObj = commands(simplicify_instance, config)


# {u'appliance_name': u'testing123', u'provisioner': u'chef', u'settings': {u'chroot_url': u'test', u'cookbooks': [u'nginx'], u'cheffile': u'http://controller1.simplicify.com/cheffiles/simplicify_test/Cheffile'}, u'ttl': u'5'}
#        job = json.loads(self.queue.value)
#        print job
#        print job['settings']['chroot_url']
#        urllib.urlretrieve ("http://controller1.simplicify.com/cheffiles/simplicify_test/Cheffile", "Cheffile")



if __name__ == '__main__':
    while True:
        cmdObj.pollBuildQueue()
        time.sleep(5)

import etcd
import uuid
import json
from libsimplicify import provisioner

with open('config.json') as data_file:
    config = json.load(data_file)

simplicify = provisioner('controller1.simplicify.com', config, "Tets")
client = etcd.Client(host='controller1.simplicify.com', port=2379)


test_settings = { "cheffile": "http://controller1.simplicify.com/cheffiles/simplicify_test/Cheffile", "cookbooks": ["nginx"], "chroot_url":"test" }

simplicify.queue_build('baremetal', '5', 'chef', test_settings, 'testing123')

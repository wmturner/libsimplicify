import etcd
import uuid
import json
from libsimplicify import provisioner
from libsimplicify import simplicify

with open('config.json') as data_file:
    config = json.load(data_file)

simplicify_instance = simplicify('controller1.simplicify.com', config)
simplicify_instance.connect()
#client = etcd.Client(host='controller1.simplicify.com', port=2379)
Provisioner = provisioner(simplicify_instance, config)


test_settings = { "cheffile": "http://controller1.simplicify.com/cheffiles/simplicify_test/Cheffile", "cookbooks": ["nginx"], "chroot_url":"test" }

Provisioner.queue_build('baremetal', '5', 'chef', test_settings, 'testing123')

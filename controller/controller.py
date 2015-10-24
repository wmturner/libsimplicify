import etcd
import uuid
import json
from libsimplicify import simplicify
from libsimplicify import commands

with open('config.json') as data_file:
    config = json.load(data_file)

simplicify_instance = simplicify('controller1.simplicify.com', config)
simplicify_instance.connect_etcd()
simplicify_instance.connect_s3()
#client = etcd.Client(host='controller1.simplicify.com', port=2379)
cmdObj = commands(simplicify_instance, config)


test_settings = { "cheffile": "http://controller1.simplicify.com/cheffiles/simplicify_test/Cheffile", "cookbooks": ["nginx"], "chroot_url":"test" }

#cmdObj.queue_build('baremetal', '5', 'chef', test_settings, 'testing123')
#cmdObj.echo_build('baremetal', '4', '<3u evan')
#cmdObj.rm_build('baremetal', '4')
cmdObj.ls_bkts()


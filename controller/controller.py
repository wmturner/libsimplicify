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
#print cmdObj.view_build('baremetal', '4', '<3u evan')
#cmdObj.rm_build('baremetal', '4')
#print cmdObj.s3_ls_bkts()
#print cmdObj.s3_ls_bkt('chroots')
#print cmdObj.s3_rm_key('chroots','config')
#print cmdObj.s3_put_file('chroots', 'config', '/root/simplicify/controller/config.json')
#print cmdObj.s3_get_file_url('chroots', 'config')

#print cmdObj.ls_srv("_etcd-server._tcp.simplicify.com")
#print cmdObj.ls_A("storage1")
#print cmdObj.create_A("record", "192.168.2.5")
print cmdObj.create_SRV("_etcd-server._tcp", 900, "controller1.simplicify.com")

# Copyright (C) Simplicify, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by William Michael Turner <williammichaelturner@gmail.com>, 2015

class commands:
    def __init__(self, simplicify, provisioner_type):
        self.provisioner_type = provisioner_type
        self.client_etcd = simplicify.client_etcd
        self.client_s3 = simplicify.client_s3
        self.config = simplicify.SimplicifyConfig
        self.hostname = socket.gethostname()

    def queue_build(self, type, ttl, provisioner, settings, appliance_name):
        """
        Note: This method establishes an s3 connection using settings in input during class initialization

        Args:
            type: The type of build (defined in and validated against config.json)
            ttl: Total time build will exist after initialization
            provisioner: Provisioner used for post configuration of the build (defined in and validated against config.json)
            settings: Settings used for provisioner configuration (defined in and validated against config.json)
            appliance_name: Colloquial name used to casually descibe the build (uniqueness is not required or enforce)
        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload (with .name, and .creation_date methods)

        """

        self.type = type
        self.ttl = ttl
        self.provisioner = provisioner
        self.settings = settings
        self.appliance_name = appliance_name

        jobID = uuid.uuid1()

        # Error handling code to be moved to validation library
        if provisioner in self.config["build"]["provisioner"]:

            for key in self.settings:
                print key
                if key in self.config["build"]["settings"][self.provisioner]:
                    print "Success"
                else:
                    print "fail"
        else:
            print "epic fail"

        if type in self.config["build"]["type"]:
            print "Success"
        else:
            print "Epic Fail"

        job = { "provisioner": self.provisioner,
                "settings": self.settings,
                "ttl": self.ttl,
                "appliance_name": self.appliance_name }

        if type == "baremetal":
            self.client_etcd.write('/build/{}/{}'.format(type,jobID), json.dumps(job))


    def rm_build(self, type, buildID):
        """
        Note: This method removes a queued build
        Args:
            type: The type of build (defined in and validated against config.json)
            appliance_name: Colloquial name used to casually descibe the build (uniqueness is not required or enforce)
        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        try:
            self.client_etcd.read("/build/{}/{}".format(type, buildID))
            self.client_etcd.delete("/build/{}/{}".format(type, buildID))
        except etcd.EtcdKeyNotFound:
            print "key not found"
        return

    def get_build(self, type, buildID):
        """
        Note: This method fetches the information associated with a buildID

        Args:
            type: The type of build (defined in and validated against config.json)
            appliance_name: Colloquial name used to casually descibe the build (uniqueness is not required or enforce)
        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully fetched contents of the {} build with buildID {}".format(type, buildID)

        try:
            print self.client_etcd.read("/build/{}/{}".format(type, buildID))
        except etcd.EtcdKeyNotFound:
            explanation = "No key found for the specified build type {} with the specified buildID {}".format(type, buildID)


        returns = [ prog_status, http_status, explanation, pick['key'] ]

        return returns



    def pollBuildQueue(self, type):
        """
        Note: This method polls the build queues for a specified node type, and submits a bid if resources are free

        Args:
            type: The type of build (defined in and validated against config.json)
            appliance_name: Colloquial name used to casually descibe the build (uniqueness is not required or enforce)
        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully won a bid for a {} build".format(type)

        # Execute a recursive query to etcd and only show a single new value after the request to the cluster was made:
        self.queue = self.client_etcd.read('/build/{}'.format(self.type), recursive = True)._children

        pick = random.choice(self.queue)
        print pick['key']
        if pick:
            # Recapture the jobID by assigning the end of the complete URI for the key (UUID that uniquely desecribes the job prescribed from the controller):
            buildID = pick['key'].rsplit('/',1)[1]

            winner = self._bid(buildID)
            # If the current worker process believes itis the winner, then begin performing the provisioning task:
            if winner==self.hostname:
                try:
                    # Double check to make sure another node has not claimed winner for the jobID
                    out_of_syncWinner = self.client_etcd.read('/winner/{}/{}/{}'.format(self.type, buildID, self.hostname))
                    print "WINNER ALREADY SELECTED, YOU ARE OUT OF SYNC"

                # During good cluster behavior, the below condition should be triggered
                except etcd.EtcdKeyNotFound:

                    # If node truly is the winner, then write it to the winner queue for record
                    # Inform the cluster that the provisioning job is in progress
                    self.client_etcd.write('/winner/{}/{}/{}'.format(type, buildID, self.hostname), pick['value'])
                    self.client_etcd.write('/inprogress/{}/{}'.format(type, buildID), "True")

                    # Delete the job from the build queue
                    self.client_etcd.delete(pick['key'])
                    print "Win"
                #os.chroot("/simplicify/chroot")
                #call(["chef-solo", "-o", "nginx"])
                exit

        returns = [ prog_status, http_status, explanation, pick['key'] ]

        return returns

    def _bid(self,jobID):
        # Create a bid
        # A bid is an integer value between 1 and 1000, and the cluster member with the highest number wins:
        bid = random.randrange(100, 1000, 3)
        # Write the worker's bid to the appropriate etcd folder:
        self.client_etcd.write('/bid/{}/{}/{}'.format(NODE_TYPE, jobID, self.hostname), bid)

        # Wait a minute until all workers have had an opportunity to bid:
        time.sleep(1)
        bid_queue = self.client_etcd.read('/bid/{}/{}'.format(NODE_TYPE, jobID), recursive = True)

        # Create a quorum dictionary used to store all bids from the various members and determine which worker is the winner
        quorum_dict = {}
        for bid in bid_queue._children:
            quorum_dict.update({ bid['key'].rsplit('/',1)[1]: bid['value'] })

        winner = max(quorum_dict.iteritems(), key=operator.itemgetter(1))[0]
        return winner

    def put_chroot(self, bkt, name, file_path):
        """
        Note: This method adds a chroot environment (tar, zip, 7zip, tar.gz, .gzip) to s3, and creates a correspoding entry in etcd

        Args:

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload (with .name, and .creation_date methods)

        """
        new_obj = s3_put_file(bkt, name, file_path)

        # Check and make sure object is successfully created.  Object will not be overwritten if it already exists
        # If the chroot was sucessfully added to s3, use etcd to keep track of the metadata
        if not new_obj == 1:
            chroot_meta_data = { "bucket": bkt,
                                 "name": name
                               }
            self.client_etcd.write('/artifacts/chroots/{}/{}'.format(bkt, name), choot_meta_data)


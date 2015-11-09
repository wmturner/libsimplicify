class create:
    """
    Note: Class establishes connections that will be used throughout various classes in Simplicify

    Args:
        clusterFQDN: Fully qualified domain that can be used for etcd and s3 connections
        SimplicifyConfig: A configuration dictionary that is stored as a JSON file.  More documentation on individual configuration attirbutes is stored in the config.json file

    Returns:
        returns: All functionality of the Simplicify platform.  This is the parent object of the Simplicify namespace.

    """
    def __init__(self, clusterFQDN, SimplicifyConfig):
        self.clusterFQDN = clusterFQDN
        self.SimplicifyConfig = SimplicifyConfig

    def connect_etcd(self):
        """
        Note: This method establishes an etcd connection using settings in input during class initialization

        Args:
            self.SimplicifyConfig: A configuration dictionary that is stored as a JSON file.  More documentation on individual configuration attirbutes is stored in the config.json file

        Returns:
            returns: On success this method returns an etcd client object

        """

        host_etcd = self.SimplicifyConfig['etcd']['uri']
        port_etcd = self.SimplicifyConfig['etcd']['port']

        try:
            self.client_etcd = etcd.Client(host=host_etcd, port=port_etcd)
        except etcd.EtcdConnectionFailed:
            explanation = "Connecting to the specified etcd host ({}) on the specified port ({}) failed.".format(host_etcd, port_etcd)

            returns = [ prog_status, http_status, explanation, self.client_etcd ]

        return self.client_etcd

    def connect_s3(self):
        """
        Note: This method establishes an s3 connection using settings in input during class initialization

        Args:
            self.SimplicifyConfig: A configuration dictionary that is stored as a JSON file.  More documentation on individual configuration attirbutes is stored in the config.json file

        Returns:
            returns: On success this method returns an etcd client object

        """

        access_key = self.SimplicifyConfig['s3']['access_key']
        secret_key = self.SimplicifyConfig['s3']['secret_key']
        host_s3 = self.SimplicifyConfig['s3']['host']
        security_setting = (self.SimplicifyConfig['s3']['is_secure'] == "True")

        self.client_s3 = boto.connect_s3(
        aws_access_key_id = access_key,
        aws_secret_access_key = secret_key,
        host = host_s3,
        is_secure=security_setting,
        calling_format = boto.s3.connection.OrdinaryCallingFormat(),
        )

        return self.client_s3

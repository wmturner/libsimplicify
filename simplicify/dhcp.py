class commands:
    def __init__(self, simplicify):
        self.client_omapi = simplicify.client_omapi
        self.config = simplicify.SimplicifyConfig

    def add_lease(self, ip_address, mac_address):
        """
        Note: This method adds a chroot environment (tar, zip, 7zip, tar.gz, .gzip) to s3, and creates a correspoding entry in etcd

        Args:

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload (with .name, and .creation_date methods)

        """

        # Define the response of a successful execution of the function
        http_status = 201
        prog_status = 0
        explanation = "Successfully added DHCP lease for specified MAC address ({}) on specified IP address ({}) on specified server ({}) .".format(mac_address, ip_address, self.config['omapi']['server'])
        payload = {}

        try:
            payload['added_lease'] = self.client_omapi.add_host(ip_address, mac_address)
        except:
            explanation = "An unknown error occurred while trying to add a DHCP lease for specified MAC address ({}) on specified IP address ({}) with specified on specified server ({}) .".format(mac_address, ip_address, self.config['omapi']['server'])
            return { "prog_status": 1, "http_status": 500, "explanation": explanation, "payload": "" }

        returns = { "prog_status": prog_status, "http_status": http_status, "explanation": explanation, "payload": payload }

        return returns


    def del_lease(self, mac_address):
        """
        Note: This method adds a chroot environment (tar, zip, 7zip, tar.gz, .gzip) to s3, and creates a correspoding entry in etcd

        Args:

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload (with .name, and .creation_date methods)

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully deleted DHCP lease for specified MAC address ({}) on specified server ({}) .".format(mac_address, self.config['omapi']['server'])
        payload = {}

        try:
            payload['deleted_lease'] = self.client_omapi.del_host(mac_address)
        except:
            explanation = "An unknown error occurred while trying to add a DHCP lease for specified MAC address ({}) on specified IP address ({}) with specified name ({}) on specified server ({}) .".format(mac_address, ip_address, name,self.config['omapi']['server'])
            return { "prog_status": 1, "http_status": 500, "explanation": explanation, "payload": "" }

        returns = { "prog_status": prog_status, "http_status": http_status, "explanation": explanation, "payload": payload }

        return returns

    def lookup_lease(self, mac_address):
        """
        Note: This method queries a DHCP server and returns a lease corresponding to the provided MAC Address

        Args:

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload (with .name, and .creation_date methods)

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully listed DHCP lease for specified MAC address ({}) on specified server ({}) .".format(mac_address, self.config['omapi']['server'])
        payload = {}

        try:
            payload["lease_IP"] = self.client_omapi.lookup_ip_host(mac_address)
        except:
            explanation = "An unknown error occurred while trying to add a DHCP lease for specified MAC address ({}) on specified IP address ({}) with specified name on specified server.".format(mac_address, self.config['omapi']['server'])
            return { "prog_status": 1, "http_status": 500, "explanation": explanation, "payload": "" }

        returns = { "prog_status": prog_status, "http_status": http_status, "explanation": explanation, "payload": payload }

        return returns

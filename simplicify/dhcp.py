class commands:
    def __init__(self, simplicify):
        self.client_omapi = simplicify.client_omapi
        self.config = simplicify.SimplicifyConfig

    def add_lease(self, ip_address, mac_address, name):
        """
        Note: This method adds a chroot environment (tar, zip, 7zip, tar.gz, .gzip) to s3, and creates a correspoding entry in etcd

        Args:

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload (with .name, and .creation_date methods)

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully added DHCP lease for specified MAC address ({}) on specified IP address ({}) with specified name ({}) on specified server ({}) .".format(mac_address, ip_address, name, self.config['omapi']['server'])

        try:
            added_lease = self.client_omapi.add_host(ip_address, mac_address, name)
        except:
            explanation = "An unknown error occurred while trying to add a DHCP lease for specified MAC address ({}) on specified IP address ({}) with specified name ({}) on specified server ({}) .".format(mac_address, ip_address, name, self.config['omapi']['server'])
            return [ 1, 500, explanation, "" ]

        returns = [ prog_status, http_status, explanation, added_lease ]

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

        try:
            deleted_lease = self.client_omapi.del_host(mac_address)
        except:
            explanation = "An unknown error occurred while trying to delete a DHCP lease for specified MAC address ({}) on specified server ({}) .".format(mac_address, self.config['omapi']['server'])
            return [ 1, 500, explanation, "" ]

        returns = [ prog_status, http_status, explanation, deleted_lease ]

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
        explanation = "Successfully added DHCP lease for specified MAC address ({}) on specified IP address ({}) with specified name ({}) on specified server ({}) .".format(mac_address, ip_address, name, self.config['omapi']['server'])

        try:
            lease = self.client_omapi.lookup_mac(mac_address)
        except:
            explanation = "An unknown error occurred while trying to add a DHCP lease for specified MAC address ({}) on specified IP address ({}) with specified name ({}) on specified server ({}) .".format(mac_address, ip_address, name, self.config['omapi']['server'])
            return [ 1, 500, explanation, "" ]

        returns = [ prog_status, http_status, explanation, lease ]

        return returns

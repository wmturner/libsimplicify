class commands:
    def __init__(self, simplicify):
        self.client_redis = simplicify.client_redis
        self.config = simplicify.SimplicifyConfig
        self.hostname = socket.gethostname()

    def get_rand_request(self):
        """
        Note: This function gets a random request from the redis server specified in the client config

        Args:

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload (with .name, and .creation_date methods)

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully got random request from configured redis server ({}).".format(self.config['redis']['host'])

        try:
            request_key = self.client_redis.randomkey()
            request = self.client_redis.hgetall(request_key)
        except:
            explanation = "An unknown error occurred while trying get a random request from the configured redis server ({}).".format(self.config['redis']['host'])
            return [ 1, 500, explanation, "" ]

        returns = [ prog_status, http_status, explanation, request ]

        return returns

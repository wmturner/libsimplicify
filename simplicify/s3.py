# Copyright (C) Simplicify, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by William Michael Turner <williammichaelturner@gmail.com>, 2015

import uuid
import json
import boto
import boto.s3.connection
class commands:
    def __init__(self, simplicify, provisioner_type):
        self.provisioner_type = provisioner_type
        self.client_etcd = simplicify.client_etcd
        self.client_s3 = simplicify.client_s3
        self.config = simplicify.SimplicifyConfig
        self.hostname = socket.gethostname()

    def s3_ls_bkts(self):
        """
        Note: This function lists all s3 buckets within the configured s3 endpoint

        Args:

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload (with .name, and .creation_date methods)

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully listed all buckets in the connected endpoint ({}).".format(self.config['s3']['host'])

        try:
            bucket_list = self.client_s3.get_all_buckets()
        except:
            explanation = "An unknown error occurred while trying to list the buckets at the connected s3 endpoint ({}).".format(self.config['s3']['host'])
            return [ 1, 500, explanation, "" ]

        returns = [ prog_status, http_status, explanation, bucket_list ]

        return returns


    def s3_ls_bkt(self, bkt):
        """
        Note: This function lists the content(s) of an s3 bucket.

        Args:
            bkt: The source s3 bucket.

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully listed the contents specified bucket ({}).".format(bkt)

        try:
            bucket = self.client_s3.get_bucket(bkt)
        except boto.exception.S3ResponseError, [status, response, body]:
            if status == 404:
                explanation = "The bucket you requested ({}) to list the contents of could not be found.".format(bkt)
            else:
                status = 500
                explanation = "An unknown error occurred while trying to list the contents of the specified bucket ({}).".format(bkt)
            return [ 1, status, explanation, "" ]

        ls_bkt = bucket.list()

        returns = [ prog_status, http_status, explanation, ls_bkt ]

        return returns


    def s3_rm_key(self, bkt, key):
        """
        Note: This function a moves a file object stored in s3 to a predefined delete bucket.  This method allows the apperance of a delete operation, while maintaining the option to restore

        Args:
            bkt: The source s3 bucket.
            key: The source key representing the file object.

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully removed the specifiied file ({}) from specified bucket ({})".format(key, bkt)

        try:
            src = self.client_s3.get_bucket(bkt)
        except boto.exception.S3ResponseError, [status, response, body]:
            explanation = "The bucket you requested ({}) to delete the file ({}) from could not be found.".format(bkt, key)
            return [ 1, status, explanation, "" ]

        try:
            rm_bkt = self.client_s3.get_bucket('{}'.format(self.config['s3']['rm_bkt']))
        except boto.exception.S3ResponseError, [status, response, body]:
            explanation = "The connection to s3 is established, but the delete bucket cannot be found"
            return [ 1, status, explanation, "" ]

        try:
            rm_bkt.copy_key(key, bkt, key)
        except boto.exception.S3CopyError, [status, response, body]:
            if status == 404:
                explanation = "An unknown error occured while copying the file you requested ({}) to delete from bucket ({}).".format(key, bkt)
            else:
                explanation = "An unknown error occured while moving the specified file ({}) from the source bucket ({})".format(bkt, key)
            return [ 1, status, explanation, "" ]

        except boto.exception.S3ResponseError, [status, response, body]:
            explanation = "The file you requested ({}) to delete from bucket ({}) could not be found.".format(key, bkt)

            return [ 1, status, explanation, "" ]

        try:
            src.delete_key(key)
        except boto.exception.S3ResponseError, [status, response, body]:
            explanation = "An unknown error occured while deleting the specified file ({}) from the bucket ({})".format(bkt, key)

            return [ 1, status, explanation, "" ]

        returns = [ prog_status, http_status, explanation, "" ]

        return returns


    def s3_put_file(self, bkt, key, file_path, overwrite=False):
        """
        Note: This function stores a file in s3 if it does not exist, but will overwrite if specifed

        Args:
            bkt: The target s3 bucket.
            key: The target key representing the file object.
            file_path: The path of the file to put at the target bucket/key s3
            overwrite: Defaults to False, but allows for over-write behavior

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully uploaded the specified file ({}) to specified bucket ({})".format(key, bkt)

        # Instantiate the bucket that the file is desired to be stored in
        try:
            bucket = self.client_s3.get_bucket(bkt)
        except boto.exception.S3ResponseError, [status, response, body]:
            explanation = "The connection to s3 is established, but the bucket ({}) cannot be found".format(bkt)
            return [ 1, status, explanation ]

        existance_test = bucket.get_key(key)
        if existance_test == None:
            pass
        elif overwrite == True:
            pass
        else:
            status = 204
            explanation = "File already exists at the specified key ({}) in the specified bucket ({})".format(key, bkt)
            return [ 1, status, explanation ]

        # Create a the key used to store the file
        try:
            new_key = bucket.new_key(key)
        except boto.exception.S3CreateError, [status, response, body]:
            explanation = "An error occurred creating the key in the requested bucket ({}) to store the specified file ({}).".format(bkt, key)
            return [ status, explanation ]

        # Upload file contents to key just created
        try:
            new_key.set_contents_from_filename(file_path)
        except boto.exception.S3DataError, [status, args]:
            explanation = "An error occurred creating the key in the requested bucket ({}) to store the specified file ({}).".format(bkt, key)
            return [ status, explanation ]

        # Set private ACL on file
        try:
            new_key.set_canned_acl('private')
        except:
            explanation = "An unknown error occurred setting the ACL on file {}".format(key)
            status = 500
            return [ status, explanation ]

        returns = [ prog_status, http_status, explanation ]

        return returns

    def s3_get_file_url(self, bkt, key):
        """
        Note: This function generates a url to to download a file from an s3 bucket

        Args:
            bkt: The target s3 bucket.
            key: The target key representing the file object.

        Returns:
            returns: Array containing the program status code, http status code, humanly readable explanation, and payload

        """

        # Define the response of a successful execution of the function
        http_status = 200
        prog_status = 0
        explanation = "Successfully generate url for specified file ({}) in specified bucket ({})".format(key, bkt)

        try:
            bucket = self.client_s3.get_bucket(bkt)
        except boto.exception.S3ResponseError, [status, response, body]:
            explanation = "The connection to s3 is established, but the bucket ({}) cannot be found".format(bkt)
            return [ 1, status, explanation, "" ]

        req_key = bucket.get_key(key)
        if req_key == None:
            status = 404
            explanation = "A file cannot be found at the specified key ({}) in the specified bucket ({})".format(key, bkt)
            return [ 1, status, explanation, "" ]
        else:
            try:
                obj_url = req_key.generate_url(3600, query_auth=True, force_http=True)
            except:
                explanation = "An unknown error occurred setting the ACL on file {}".format(key)
                status = 500
                return [ 1, status, explanation, "" ]

        payload = obj_url
        returns = [ prog_status, http_status, explanation, payload ]

        return returns

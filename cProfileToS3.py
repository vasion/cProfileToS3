import tempfile
import datetime

import boto
import os


__author__ = 'momchilrogelov'

import cProfile
# decorator save profile to temp file

class profile_and_save(object):
    def __init__(self, aws_key=None, aws_secret=None, bucket_name=None, file_name="profile"):
        self.aws_key = aws_key
        self.aws_secret = aws_secret
        self.bucket_name = bucket_name
        self.file_name = file_name

        self.conn = boto.connect_s3(self.aws_key, self.aws_secret)
        self.bucket = self.conn.get_bucket(self.bucket_name)

    def __call__(self, f):
        def wrapped_f(*args, **kwargs):
            #start profiler
            p = cProfile.Profile()
            p.enable()

            #function call
            result = f(*args, **kwargs)

            #stop profiler
            p.disable()

            #dump to temp file
            file = tempfile.NamedTemporaryFile()
            p.dump_stats(file.name)

            #upload file to s3
            key_name = '{}{}.profile'.format(self.file_name, datetime.datetime.now())
            k = self.bucket.new_key(key_name)
            k.set_contents_from_filename(file.name)
            file.close()

            return result

        return wrapped_f

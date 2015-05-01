import tempfile
import datetime
import cProfile

import boto
import line_profiler


# decorator save profile to temp file

class profile_and_save(object):
    def __init__(self, aws_key=None, aws_secret=None, bucket_name=None, file_name="profile"):
        self.aws_key = aws_key
        self.aws_secret = aws_secret
        self.bucket_name = bucket_name
        self.file_name = file_name

        self.conn = boto.connect_s3(self.aws_key, self.aws_secret)
        self.bucket = self.conn.get_bucket(self.bucket_name)

    def _upload_to_s3(self, tfile, duration, extension="cprofile"):
        key_name = '{}.{}.{}.{}'.format(self.file_name, duration, datetime.datetime.now().strftime("%b.%d.%Y.%H:%M:%S"),
                                        extension)
        k = self.bucket.new_key(key_name)
        k.set_contents_from_filename(tfile.name)

    def __call__(self, f):
        def wrapped_f(*args, **kwargs):
            # start profiler
            start = datetime.datetime.now()
            p = cProfile.Profile()
            p.enable()

            # function call
            result = f(*args, **kwargs)

            #stop profiler
            p.disable()
            end = datetime.datetime.now()
            time_elapsed = end - start

            #dump to temp file
            with tempfile.NamedTemporaryFile() as tfile:
                p.dump_stats(tfile.name)

                #upload file to s3
                self._upload_to_s3(tfile, round(time_elapsed.total_seconds(), 3))

            return result

        return wrapped_f


class line_profile_and_save(profile_and_save):
    def __call__(self, f):
        def wrapped_f(*args, **kwargs):
            # start profiler
            p = line_profiler.LineProfiler(f)
            p.enable_by_count()
            start = datetime.datetime.now()

            # function call
            result = f(*args, **kwargs)

            #stop profiler
            p.disable_by_count()
            end = datetime.datetime.now()
            time_elapsed = end - start

            #dump to temp file
            with tempfile.NamedTemporaryFile() as tfile:
                p.print_stats(tfile)
                tfile.seek(0)

                #upload file to s3
                self._upload_to_s3(tfile, round(time_elapsed.total_seconds(), 3), "line_profile.txt")

            return result

        return wrapped_f

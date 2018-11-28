# -*- Coding: utf-8 -*-

"""Classes for S3 buckets."""

from botocore.exceptions import ClientError   # for Exceptions
from pathlib import Path
import mimetypes
import util


class BucketManager:
    """Manage an S3 bucket."""

    def __init__(self, session):
        """Create a BucketManager object."""
        self.session = session
        self.s3 = self.session.resource('s3')

    def get_region_name(self, bucket):
        """Get the bucket's region name."""
        bucket_location = self.s3.meta.client.get_bucket_location(Bucket=bucket.name)
        return bucket_location["LocationConstraint"] or 'us-east-1'

    def get_bucket_url(self, bucket):
        """Get the website URL for this bucket."""
        return "http://{}.{}".format(bucket.name,
               util.get_endpoint(self.get_region_name(bucket)).host)

    def all_buckets(self):
        """Get an iterator for all buckets."""
        return self.s3.buckets.all()

    def all_objects(self, bucket_name):  # bucket_name is a string
        """Get an iterator for all objects in a bucket."""
        return self.s3.Bucket(bucket_name).objects.all()

    def init_bucket(self, bucket_name):  # bucket_name is a string...
        """Create a new bucket, or returns existing one by name."""
        s3_bucket = None
        try:
            s3_bucket = self.s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': self.session.region_name
                }
            )
        except ClientError as error:
            ec = error.response['Error']['Code']
            if ec == 'BucketAlreadyOwnedByYou':
                s3_bucket = self.s3.Bucket(bucket_name)
            elif ec == 'InvalidLocationConstraint':
                s3_bucket = self.s3.create_bucket(
                                Bucket=bucket_name
                            )
            else:
                print('ERROR IS =', error.response['Error']['Code'])
                raise error

        return s3_bucket

    def set_policy(self, bucket):  # 'bucket' is an object here.
        """Set bucket policy to be readable by everyone."""
        policy = """
        {
          "Version":"2012-10-17",
          "Statement": [{
              "Sid":"AddPerm",
              "Effect":"Allow",
              "Principal": "*",
              "Action":["s3:GetObject"],
              "Resource":["arn:aws:s3:::%s/*"]
          }]
        }
        """ % bucket.name
        policy = policy.strip()

        pol = bucket.Policy()
        pol.put(Policy=policy)

    def configure_website(self, bucket):
        """Configure website content."""
        ws = bucket.Website()
        ws.put(WebsiteConfiguration={
            'ErrorDocument': {
                'Key': 'error.html'
            },
            'IndexDocument': {
                'Suffix': 'index.html'
            }
        })

    @staticmethod
    def upload_file(bucket, path, key):
        """Upload the file (key) in the directory (path) to the S3 bucket."""
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'
        # Try this in ipython
        # import mimetypes
        # mimetypes?

        return bucket.upload_file(
            path,
            key,
            ExtraArgs={
                'ContentType': content_type
            }
        )

    def sync(self, pathname, bucket_name):
        """Synchrozie the website with local folder."""
        bucket = self.s3.Bucket(bucket_name)
        root = Path(pathname).expanduser().resolve()

        def handle_directory(target):
            for p in target.iterdir():
                if p.is_dir():
                    handle_directory(p)
                if p.is_file():
                    # s3's upload file function needs strings...
                    self.upload_file(bucket,
                                     str(p),
                                     str(p.relative_to(root)))
                    print("Path: {}\n Key: {}".format(p, p.relative_to(root)))

        handle_directory(root)

import boto3
import click

session = boto3.Session(profile_name='devdj')
s3 = session.resource('s3')

@click.group()
def cli():
    "Webotron deploys websites to AWS"
    pass

@cli.command('list-buckets')
def list_buckets():
    "List all s3 buckets"
    for bucket in s3.buckets.all():
        print(bucket)

@cli.command('list-bucket-objects')
def list_bucket_objects():
    "List objects (files) in an s3 bucket"
    for obj in s3.Bucket('automatingaws-dinesh-boto3').objects.all():
        print(obj)


if __name__ == '__main__':
    cli()

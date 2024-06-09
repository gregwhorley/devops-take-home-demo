import argparse
import boto3
import sys


def main(profile, name):
    session = boto3.Session(region_name='us-west-2', profile_name=profile)
    s3 = session.client('s3')
    dynamodb = session.client('dynamodb')
    try:
        response = s3.create_bucket(Bucket=name,
                                    ACL='private',
                                    CreateBucketConfiguration={
                                        'LocationConstraint': 'us-west-2',
                                    }, )
        print(response)
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print('Bucket already exists and you own it...moving on')
    except s3.exceptions.BucketAlreadyExists:
        print('Bucket already exists and you do not own it. Please try again with another unique bucket name.')
        sys.exit(1)

    s3.put_bucket_versioning(Bucket=name,
                             VersioningConfiguration={
                                 'Status': 'Enabled',
                                 'MFADelete': 'Disabled',
                             },
                             )
    try:
        response = dynamodb.create_table(
            TableName=name,
            AttributeDefinitions=[{
                'AttributeName': 'LockID',
                'AttributeType': 'S'
            }],
            KeySchema=[{
                'AttributeName': 'LockID',
                'KeyType': 'HASH',
            }],
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            }
        )
    except dynamodb.exceptions.TableAlreadyExists:
        print('Table already exists...moving on')
    except dynamodb.exceptions.InternalServerError as e:
        print(f'Unhandled exception while creating table {name}', e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Manage S3 bucket that stores Terraform remote state')
    parser.add_argument('-p', '--profile', help='AWS profile', required=True)
    parser.add_argument('-n', '--name',
                        help='S3 bucket and DynamoDB table name',
                        required=True,)
    args = parser.parse_args()
    main(args.profile, args.name)

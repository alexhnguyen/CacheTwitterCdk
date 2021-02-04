import boto3
import tempfile
import json

BUCKET_NAME = "alngyn-twitter-archive"
# this ID comes from twitter
BARACK_OBAMA_ID = '813286'

def get_all_files_in_path(s3_client, bucket_name, file_prefix):
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=file_prefix)
    return [obj['Key'] for page in pages for obj in page['Contents']]


def handler(event, context):
    try:
        s3_client = boto3.client('s3')
        all_files = get_all_files_in_path(s3_client, BUCKET_NAME, f'{BARACK_OBAMA_ID}/')
        all_files.sort()
        # for simplicity, get the 5 newest tweets
        latest = all_files[-5:]

        json_outputs = []
        for s3_filepath in latest:
            with tempfile.NamedTemporaryFile('w') as tempfile_input:
                # flush to make sure the file actually exists
                tempfile_input.flush()
                s3_client.download_file(BUCKET_NAME, s3_filepath, tempfile_input.name)
                # flush to update the file
                tempfile_input.flush()
                with open(tempfile_input.name) as json_file:
                    abc = json.load(json_file)
                json_outputs.append(abc)
        response = {
            "statusCode": 200,
            "headers": {
                "Content-Type" : "application/json",
                "Access-Control-Allow-Headers" : "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods" : "OPTIONS,POST",
                "Access-Control-Allow-Credentials" : True,
                "Access-Control-Allow-Origin" : "http://localhost:3000",
                "X-Requested-With" : "*"
            },
            "body": str(json_outputs)
        }
        return response
    except:
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type" : "application/json",
                "Access-Control-Allow-Headers" : "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods" : "OPTIONS,POST",
                "Access-Control-Allow-Credentials" : True,
                "Access-Control-Allow-Origin" : "*",
                "X-Requested-With" : "*"
            },
        }

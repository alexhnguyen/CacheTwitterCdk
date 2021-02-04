import os
import boto3
import tempfile
import json
from botocore.exceptions import ClientError
import tweepy

PREVIOUS_ID_FILENAME = "previous_id"
SCREEN_NAME = "BarackObama"
BUCKET_NAME = "alngyn-twitter-archive"

def handler(event, context):

    print("Authorizing with twitter")
    api = tweepy.API(authorization())

    print("Getting tweets")
    tweets = get_tweets(api)
    print(f"Got {len(tweets)} tweets")
    if len(tweets) == 0:
        return {
            "statusCode": 200,
            "body": "No new tweets found."
        }

    print("Uploading tweets")
    latest_uploaded_tweet_id = upload_tweets(tweets)

    if latest_uploaded_tweet_id is not None:
        print("Updating latest uploaded tweet")
        update_latest_uploaded_tweet_id(latest_uploaded_tweet_id)
    else:
        print("Unable to upload new tweets")
        return {
                "statusCode": 500,
                "body": "Failed to upload new tweets."
            }

    return {
            "statusCode": 200,
            "body": f"Added {len(tweets)} new tweets."
        }


def authorization():
    # set these manually in AWS console.
    # you could put it in secrets manager,
    # but then you'd have to pay more
    consumer_key = os.environ.get('CONSUMER_KEY')
    consumer_secret = os.environ.get('CONSUMER_SECRET')

    access_token = os.environ.get('ACCESS_TOKEN')
    access_token_secret = os.environ.get('ACCESS_TOKEN_SECRET')

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    return auth

def get_tweets(api):
    tweets = []
    try:
        with tempfile.NamedTemporaryFile('w') as tempfile_prev_id:
            s3_client = boto3.client('s3')
            s3_client.download_file(BUCKET_NAME, PREVIOUS_ID_FILENAME, tempfile_prev_id.name)
            tempfile_prev_id.flush()
            with open(tempfile_prev_id.name, "r") as since_id_io:
                since_id = since_id_io.read().strip()
        tweets = api.user_timeline(screen_name=SCREEN_NAME, since_id=since_id)
    except ClientError:
        # if we get a ClientError, that means we could not get the previous_id
        # in that case, get the previous 10 tweets
        tweets = api.user_timeline(screen_name=SCREEN_NAME, count=10)
    return tweets


def upload_tweets(tweets):
    latest_uploaded_tweet_id = None
    try:
        # reverse to start with the oldest
        # that way if we fail it is easier to
        # pick up where we left off
        tweets.reverse()
        for tweet in tweets:
            save_json = {
                "author_id": tweet.author.id,
                "screen_name": tweet.author.screen_name,
                "created_at": tweet.created_at.isoformat(),
                "text": tweet.text,
                "favorite_count": tweet.favorite_count,
                "retweet_count": tweet.retweet_count,
            }
            with tempfile.NamedTemporaryFile('w') as tempfile_json:
                json.dump(save_json, tempfile_json)
                tempfile_json.flush()
                upload_file(
                    BUCKET_NAME, tempfile_json.name,
                    f'{tweet.author.id}/{tweet.created_at.year}/{tweet.created_at.month}/{tweet.created_at.isoformat()}.json'
                )
            latest_uploaded_tweet_id = tweet.id
    except Exception as e:
        print(e)
    return latest_uploaded_tweet_id

def update_latest_uploaded_tweet_id(latest_uploaded_tweet_id):
    with tempfile.NamedTemporaryFile('w') as tempfile_new_prev_id:
        tempfile_new_prev_id.write(str(latest_uploaded_tweet_id))
        tempfile_new_prev_id.flush()
        upload_file(BUCKET_NAME, tempfile_new_prev_id.name, PREVIOUS_ID_FILENAME)

def upload_file(bucket, file_name, object_name=None):
    if object_name is None:
        object_name = file_name

    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        print(e)
        return False
    return True


handler('', '')
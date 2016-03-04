import logging
import boto3
import json
import requests
import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# change this to whatever your table name is
table = dynamodb.Table('elasticsearch-backups')
now = datetime.datetime.now()

# I don't fully understand the reason for this. Following example
# http://docs.aws.amazon.com/amazondynamodb/latest/gettingstartedguide/GettingStarted.Python.04.html
pe = "#dmn, #pth, #bkt"
ean = {"#dmn": "domain", "#pth": "path", "#bkt": "bucket"}


# This is the method that will be registered
# with Lambda and run on a schedule
def handler(event={}, context={}):
    logger.info("started")

    logger.info("scanning table")
    nodes = table.scan(
        ProjectionExpression=pe,
        ExpressionAttributeNames=ean
        )

    logger.info("nodes are " + str(nodes))

    for i in nodes['Items']:
        bucket = str(i['bucket'])
        path = str(i['path'])

        logger.info("bucket is " + str(i['bucket']))
        logger.info("base_path is " + str(i['path']))

        logger.info("setting repository json")
        repository = {
            "type": "s3",
            "settings": {
                "bucket": bucket,
                "base_path": path
            }
        }
        logger.info("repository json is " + json.dumps(repository))

        logger.info("setting url path")
        url = i['domain'] + "/_snapshot/lambda_s3_repository"
        logger.info("url path is " + url)

        # create repository
        logger.info("creating repository")
        response = requests.put(
            url,
            data=json.dumps(repository)
            )
        logger.info(response.content)

        # start snapshot
        logger.info("starting snapshot")
        url = url + "/" + str(now.strftime("%Y-%m-%dt%H:%M"))
        response = requests.put(
            url
            )
        logger.info(response.content)
        logger.info("new snapshot started at " + url)


# If being called locally, just call handler
if __name__ == '__main__':
    import os
    import json
    import sys

    logging.basicConfig()
    event = {}

    # TODO if argv[1], read contents, parse into json
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        with open(input_file, 'r') as f:
            data = f.read()
        event = json.loads(data)

    result = handler(event)
    output = json.dumps(
        result,
        sort_keys=True,
        indent=4,
        separators=(',', ':')
    )
    logger.info(output)
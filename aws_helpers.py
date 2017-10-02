import boto3


def sns_send(message, topic_arn='arn:aws:sns:us-west-2:632826021673:fwaligorski-watchdog-topic'):
    client = boto3.client('sns')
    client.publish(
        TopicArn=topic_arn,
        Message=message
    )


def get_dynamodb_settings(id, table_name='fwaligorski-watchdog-table'):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    # TODO check if id is correct
    response = table.get_item(
        Key={'id': str(id)}
    )
    items = response['Item']
    return items
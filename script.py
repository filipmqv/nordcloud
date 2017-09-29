import boto3
import os
import subprocess
import asyncio
import datetime
import sys


async def manage_service(name, num_of_sec_check, num_of_sec_wait, num_of_attempts):
    while True:
        print('check ' + name)
        if not is_service_running(name):
            print('starting ' + name)
            start_service(name)
        print('sleeping ' + name)
        await asyncio.sleep(5)


def get_dynamodb_settings(table_name='fwaligorski-watchdog-table'):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    response = table.get_item(
        Key={'id': '1'}
        )
    items = response['Item']
    print(items['ListOfServices'])
    return items


def start_service(name):
    with open(os.devnull, 'wb') as hide_output:
        exit_code = subprocess.Popen(['service', name, 'start'], stdout=hide_output, stderr=hide_output).wait()
        return exit_code == 0


def is_service_running(name):
    with open(os.devnull, 'wb') as hide_output:
        exit_code = subprocess.Popen(['service', name, 'status'], stdout=hide_output, stderr=hide_output).wait()
        return exit_code == 0


try:
    settings = get_dynamodb_settings()
    # TODO error check!!!

    futures = [manage_service(service, 1, 1, 1) for service in settings['ListOfServices']]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(futures))
    loop.close()
except KeyboardInterrupt:
    # ctrl-c was pushed; cancel all tasks
    for task in asyncio.Task.all_tasks():
        task.cancel()
    sys.exit()




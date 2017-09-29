import boto3
import os
import subprocess
import asyncio
import datetime
import sys
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Watchdog')
    parser.add_argument('id', type=int, help='an integer for the id')
    return parser.parse_args()


async def manage_service(name, num_of_sec_check, num_of_sec_wait, num_of_attempts):
    running = True
    while running:
        print(name+ ' check ')
        if not is_service_running(name):
            for i in range(num_of_attempts):
                print(name + ' starting attempt ' + str(i))
                start_service(name)
                if is_service_running(name):
                    print(name + ' breaking ')
                    break;
                if i == num_of_attempts - 1:
                    running = False
                    print(name + ' quitting')
                if running: 
                    print(name + ' did not start, waiting; times:' + str(i))
                    await asyncio.sleep(num_of_sec_wait)
        if running: 
            print(name + ' sleeping')
            await asyncio.sleep(num_of_sec_check)
    print(name + " quited")


def get_dynamodb_settings(id, table_name='fwaligorski-watchdog-table'):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    # TODO check if id is correct
    response = table.get_item(
        Key={'id': str(id)}
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
    args = parse_args()
    settings = get_dynamodb_settings(args.id)
    # TODO error check!!!
    # TODO check if settings changed every 15*60 sec

    futures = [manage_service(service, 
        int(settings['NumOfSecCheck']), int(settings['NumOfSecWait']), int(settings['NumOfAttempts'])) 
        for service in settings['ListOfServices']]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(futures))
    loop.close()
except KeyboardInterrupt:
    # ctrl-c was pushed; cancel all tasks
    for task in asyncio.Task.all_tasks():
        task.cancel()
    sys.exit()




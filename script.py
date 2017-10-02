import os
import subprocess
import asyncio
from concurrent.futures import FIRST_COMPLETED
import datetime
import sys
import argparse
import logging
from aws_helpers import sns_send, get_dynamodb_settings


def parse_args():
    parser = argparse.ArgumentParser(description='Watchdog')
    parser.add_argument('id', type=int, help='an integer for the id')
    return parser.parse_args()


def log(text):
    sns_send(text)
    logging.error(text)


async def manage_config_changes(settings, db_id, time_to_wait=900):
    while True:
        await asyncio.sleep(time_to_wait)
        print('checking new settings')
        new_settings = get_dynamodb_settings(db_id)
        if (settings != new_settings):
            return new_settings
    

async def pending():
    while True:
        # waiting because task should not to finish (only manage_config_changes task can return value to main process)
        await asyncio.sleep(99999)


async def restart_service(name, num_of_sec_wait, num_of_attempts):
    for i in range(num_of_attempts):
        print(name + ' starting attempt ' + str(i))
        start_service(name)
        if is_service_running(name):
            print(name + ' started succesfully ')
            log('Service {0} has been started after {1} attempts.'.format(name, i+1))
            return True;
        if i < num_of_attempts:
            print(name + ' did not start, waiting; times:' + str(i))
            await asyncio.sleep(num_of_sec_wait)
    print(name + ' quitting')
    log("Service {0} can't be started after {1} attempts.".format(name, num_of_attempts))
    return False


async def manage_service(name, num_of_sec_check, num_of_sec_wait, num_of_attempts):
    running = True
    while running:
        print(name + ' check ')
        if not is_service_running(name):
            log('Service {} is down'.format(name))
            running = await restart_service(name, num_of_sec_wait, num_of_attempts)
        if running: 
            print(name + ' sleeping')
            await asyncio.sleep(num_of_sec_check)
    print(name + " quited")
    await pending()


def start_service(name):
    with open(os.devnull, 'wb') as hide_output:
        exit_code = subprocess.Popen(['service', name, 'start'], stdout=hide_output, stderr=hide_output).wait()
        return exit_code == 0


def is_service_running(name):
    with open(os.devnull, 'wb') as hide_output:
        exit_code = subprocess.Popen(['service', name, 'status'], stdout=hide_output, stderr=hide_output).wait()
        return exit_code == 0


def cancel_all_tasks():
    for task in asyncio.Task.all_tasks():
        task.cancel()


def main():
    logging.basicConfig(filename='nordcloud.log', level=logging.WARNING, format='%(asctime)s %(message)s')
    args = parse_args()
    settings = get_dynamodb_settings(args.id)
    try:
        loop = asyncio.get_event_loop()
        while True:
            futures = [manage_service(service, 
                int(settings['NumOfSecCheck']), int(settings['NumOfSecWait']), int(settings['NumOfAttempts'])) 
                for service in settings['ListOfServices']]
            futures.append(manage_config_changes(settings, args.id))

            # first and only completed task can be 'manage_config_changes' task which ends when config changed
            done, _ = loop.run_until_complete(asyncio.wait(futures, return_when=FIRST_COMPLETED))
            settings = done.pop().result()
            cancel_all_tasks()
    except KeyboardInterrupt:
        # ctrl-c was pushed; cancel all tasks
        cancel_all_tasks()
        sys.exit()
    finally:
        loop.stop()
        loop.close()


if __name__ == '__main__':
    main()

# todo

# check if id of dynamodb is correct

# This should be a daemonized script​ which is able to run in the background even when a
# user is not logged on (running as a Service).

# 2. Upon execution - the script should check for configuration and perform error handling
# (demonstrate creativeness).
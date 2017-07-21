#!/usr/bin/env python
#     Copyright 2017 Netflix, Inc.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
"""
USAGE:
    grizzly_util.py test <command_file> <region>
    grizzly_util.py sendmsg <arn> <subject> <message>...
"""

import boto3
import logging

log = logging.getLogger("mock_grizzly")
logging.basicConfig()
log.setLevel(logging.DEBUG)


def get_node_number(region):

    region = "all"

    d = boto3.session.Session().client("dynamodb", region_name="us-west-2")
    v = d.update_item(TableName="repulsive_grizzly", Key={ "key": {"S": "counter"}, "region": {"S": region}}, UpdateExpression="SET node_number = node_number + :c", ExpressionAttributeValues={":c": {"N": "1"}}, ReturnValues="ALL_OLD")

    return int(v["Attributes"]["node_number"]["N"])


def killswitch():
    d = boto3.session.Session().client("dynamodb", region_name="us-west-2")
    v = d.get_item(TableName="repulsive_grizzly", Key={"key": {"S": "kill_switch"}, "region": {"S": "all"}})

    item = v.get("Item")
    if not item:
        log.critical("Can't find kill switch")
        return True

    switch = bool(item["shutdown"]["BOOL"])

    return switch


def get_uuid():
    import uuid
    return uuid.uuid4()


def send_message(arn, subject, message):

    region = arn.split(":")[3]
    log.debug("sending to '{}' subject '{}' message '{}'".format(arn, subject, message))

    sns = boto3.session.Session().client("sns", region_name=region)
    sns.publish(TopicArn=arn, Subject=subject, Message=message)


def main(args):

    if args.get("test"):
        command_file = args["<command_file>"]
        region = args["<region>"]

        log.debug("command file is {}".format(command_file))
        log.debug("node number is {}".format(get_node_number(region)))
        log.debug("kill switch is {}".format(killswitch()))
        log.debug("uuid is {}".format(get_uuid()))

    elif args.get("sendmsg"):
        arn = args["<arn>"]
        subject = args["<subject>"]
        message = " ".join(args["<message>"])
        send_message(arn, subject, message)

if __name__ == "__main__":
    from docopt import docopt
    main(docopt(__doc__))

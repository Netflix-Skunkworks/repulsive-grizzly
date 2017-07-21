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
import boto.sns
import grizzly_util

import eventlet
from eventlet.timeout import Timeout
from eventlet.green.urllib import request
from eventlet.green.urllib import error
import eventlet.green.ssl as ssl

import json
import _thread
import time
import string
import urllib.parse
from datetime import datetime
from collections import Counter
import random


class GrizzlyConfiguration():
    '''
    This class is called to configure and conduct an application layer
    DoS test.

    More information on how to configure the tool can be found on:
    https://github.com/netflix-skunkworks/repulsive-grizzly
    '''
    def __init__(self):
        # Read in config file
        self.conf = ""
        with open("commands.json") as config:
            self.conf = json.loads(config.read())

        self.status_code = []

        # If setup to use Kraken, we should ensure sns_region and sns_topic
        try:
            if self.conf["use_with_kraken"]:
                self.use_kraken = True
                self.sns = boto.sns.connect_to_region(self.conf["sns_region"])
                self.topic = self.conf["sns_topic"]
            else:
                self.use_kraken = False
        except:
            print("Could not set sns_region or sns_topic, did you specify them?")
            exit(1)

        # Check if we should perform a sanity check
        try:
            if self.conf["perform_sanity_check"]:
                self.perform_sanity_check = True
            else:
                self.perform_sanity_check = False
        except:
            print("Could not determine if we should do sanity check")
            exit(1)

        # If setup to use Kraken, we should ensure sns_region and sns_topic
        try:
            if self.conf["use_with_kraken"]:
                self.instance_id = grizzly_util.get_node_number("all")
            else:
                self.instance_id = 1
        except:
            print("Could not set instance, do you have AWS credentials "
                  "on the host you are running Repulsive Grizzly?")
            exit(1)

        self.cookie_list = []
        self.headers_list = []

    def payload_generator(self, size=50, chars=string.ascii_uppercase + string.digits):
        '''
        Payload generator can be used by supplying a placehodler $$1$$
        and overwritten for your specific use case

        NOTE: This is not currently used or implemented
        '''

        return ''.join(random.choice(chars) for _ in range(size))

    def load_commands(self, command_file):
        '''
        Loads all commands into self object
        '''

        # Make sure there is a hostname defined, otherwise we can't set header
        try:
            self.verb = self.conf["verb"]
        except:
            print("Could not resolve HTTP Verb for attack, exiting")
            exit(1)

        # Configure proxy if enabled
        try:
            if self.conf["proxy"]:
                self.proxy = True
                self.proxy_config = self.conf["proxy_config"]
            else:
                self.proxy = False
        except:
            print("Proxy should be set to True/False in the commands.json")
            exit(1)

        # Grab the sanity check url
        try:
            self.sanity_check_url = self.conf["sanity_check_url"]
        except:
            print("No sanity check url provided, how do we know we are healthy?")
            exit(1)

        # Make sure there is a hostname defined, otherwise we can't set header
        try:
            self.host = self.conf["hostname"]
        except:
            print("Could not resolve hostname for attack, exiting")
            exit(1)

        # Load post data if provided and verb is either post, put or patch
        try:
            if self.verb.lower() in ["post", "put", "patch"] and self.conf["post_data"]:
                if self.conf["post_data"]:
                    with open("post_data/{}".format(str(self.conf["post_data"]))) as post_data:
                        self.post_data = post_data.read().replace('\n', '')
            else:
                self.post_data = ""
        except:
            print("Could not resolve post data, did you specify the correct filename?")
            raise

        # If configured to use cookies, load the cookies from json into string?
        try:
            if self.conf["use_auth"]:
                self.auth_store_name = self.conf["auth_store_name"]
                with open("./authentication/{}".format(self.auth_store_name)) as auth_objects:
                    self.auth_objects = json.loads(auth_objects.read())
            else:
                self.auth_objects = []
        except Exception as e:
            print("Could not resolve cookie store for attack, exiting")
            print(e)
            exit(1)

        # You can set one_url_per_agent to true to have each agent
        # hit all URLs or moduls to fix one URL per attack agent.
        # Otherwise this defaults to all urls per each agent
        try:
            if self.conf["urls"] and self.conf["one_url_per_agent"]:
                self.urls = [self.conf["urls"][int(self.instance_id) % len(self.conf["urls"])]]
            elif self.conf["urls"]:
                self.urls = self.conf["urls"]
        except Exception as e:
            print("Could not assign one url per agent, exiting!")
            print(e)
            exit(1)

        # Load headers into a dict object
        if self.conf["headers"]:
            self.header_store_name = self.conf["headers"]
            with open("./headers/{}".format(self.header_store_name)) as config:
                self.headers = json.loads(config.read())
        else:
            print("no headers specified, using default headers.")
            with open("./headers/{}".format("default")) as config:
                self.headers = json.loads(config.read())

        # If we need to replace auth objects, let's load them and build a map
        if len(self.auth_objects) > 0:
            # This method generates a random sample with a deterministic seed
            # to ensure each instances uses the same cookies
            try:
                random_sample = random
                random_sample.seed(self.conf["auth_store_count"])
                if len(self.auth_objects) != 0:
                    self.auth_objects = random_sample.sample(self.auth_objects, (self.conf["auth_store_count"]))
                else:
                    self.auth_objects = []
            except:
                print("Did you specify the number of objects (auth_store_count) "
                      "for your authentication store?")
                exit(1)

            # The following code blocks compute all possible requests depending
            # on how many auth objects were provided.
            self.computed_requests = {}
            self.computed_requests["urls"] = []
            self.computed_requests["headers"] = []
            self.computed_requests["post_data"] = []
            temp_hash = {}

            # Compute a list of URLs with associated auth objects if identified
            for url in self.urls:
                if "$$AUTH$$" in url:
                    for auth_object in self.auth_objects:
                        self.computed_requests["urls"].append(url.replace("$$AUTH$$", auth_object))
                else:
                    self.computed_requests["urls"].append(url)

            # Compute a list of headers with associated auth objects if identified
            auth_headers = False
            for header in self.headers.values():
                if "$$AUTH$$" in header:
                    auth_headers = True

            if auth_headers:
                for i in range(len(self.auth_objects)):
                    print(i)
                    temp_hash = {}
                    for key, value in self.headers.items():
                        if "$$AUTH$$" in value:
                            temp_hash.update({key: value.replace("$$AUTH$$", self.auth_objects[i])})
                        else:
                            temp_hash.update({key: value})

                    self.computed_requests["headers"].append(temp_hash)
            else:
                self.computed_requests["headers"] = [self.headers]

            # Compute a list of post_data samples with associated auth objects if identified
            if self.post_data:
                if "$$AUTH$$" in self.post_data:
                    auth_headers = True
                if auth_headers:
                    for i in range(len(self.auth_objects)):
                        self.computed_requests["post_data"].append(self.post_data.replace("$$AUTH$$", self.auth_objects[i]))
                else:
                    self.computed_requests["post_data"] = [self.post_data]
        else:
            self.computed_requests = {}
            self.computed_requests["urls"] = []
            self.computed_requests["headers"] = []
            self.computed_requests["post_data"] = []
            temp_hash = {}
            self.computed_requests["urls"] = self.urls
            self.computed_requests["headers"] = [self.headers]
            self.computed_requests["post_data"] = [self.post_data]

    def generate_request(self, verb, url, headers, post_data=None):
        try:
            # import pdb; pdb.set_trace()
            req = request.Request(url,
                                  data=post_data.encode("utf-8") if post_data is not None else None,
                                  headers=headers,
                                  method=verb)
            if self.proxy:
                req.set_proxy(self.proxy_config, urllib.parse.urlparse(url).scheme)
                response = request.urlopen(req, timeout=60, context=self.create_ctx())
            else:
                response = request.urlopen(req, timeout=60, context=self.create_ctx())
            self.status_code.append(int(response.code))
        except error.HTTPError as e:
            self.status_code.append(int(e.code))
        except error.URLError as e:
            self.sns_logger(status_codes={}, exception=str(e.reason), subject="Grizzly Error")
        except Exception:
            import traceback
            self.sns_logger(status_codes={}, exception=str(traceback.format_exc()), subject="Grizzly Error")
            print(('generic exception: ' + traceback.format_exc()))

    def countdown(self, start_time):
        '''
        This method sleeps until the start_time is triggered.
        This is used to keep attack agents in sync so they start
        their tests at the same time.
        '''
        print(("Executing Test on "
               "{} with {} threads "
               "via {} url(s) for "
               "{} seconds".format(self.conf["hostname"],
                                   str(self.conf["threads"]),
                                   self.urls,
                                   str(self.conf["ttl"]))))

        now = datetime.now()
        timestamp = start_time.split(':')
        start_attack = now.replace(hour=int(timestamp[0]), minute=int(
            timestamp[1]), second=int(timestamp[2]))
        t = int((start_attack - now).total_seconds())
        print(("Attack starts at: {} in {} seconds".format(start_time, t)))

        while start_attack > now:
            now = datetime.now()
            timestamp = start_time.split(':')
            start_attack = now.replace(hour=int(timestamp[0]), minute=int(
                timestamp[1]), second=int(timestamp[2]))
            mins, secs = divmod(t, 60)
            timeformat = '{:02d}:{:02d}'.format(mins, secs)
            print(timeformat)
            time.sleep(1)
            t -= 1
        print('Attack Executing!\n\n')

    def sns_logger(self, status_codes={}, exception=None, subject="Grizzly Log", url=""):
        '''
        This method  logs messages to an SNS queue and/or prints them to console.
        '''
        timestamp = '%s' % datetime.now()
        agent = self.instance_id
        if url == "":
            url = self.urls

        if status_codes:
            message = json.dumps({"agent": agent,
                                  "timestamp": timestamp,
                                  "status_codes": status_codes,
                                  "elb": url})
            if self.use_kraken:
                self.sns.publish(message=message, subject=subject, topic=self.topic)
            print(message)
        # I am not handling exceptions yet, but this is for future
        if exception:
            message = json.dumps({"agent": agent,
                                  "timestamp": timestamp,
                                  "url": url,
                                  "exception": exception})
            if self.use_kraken:
                self.sns.publish(message=message, subject=subject, topic=self.topic)
            print(message)

    def status_counter(self, thread_name):
        '''
        This provides status updates to the SNS queue every 5 seconds
        '''
        while True:
            time.sleep(5)
            status_codes = Counter(self.status_code)
            self.sns_logger(status_codes)
            self.status_code = []

    def create_ctx(self):
        '''
        This method sets the right ssl context to disable hostname checking
        and certificate validation.
        '''
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def sanity_check(self, client, computed_requests):
        '''
        This method checks that the sanity_check_url provides a 200 status code.
        If the sanity check fails, the application exists.
        '''
        req = request.Request(client, headers=self.computed_requests["headers"][0])

        response = request.urlopen(req, timeout=60, context=self.create_ctx())
        if response.code != 200:
            self.sns_logger(status_codes={},
                            exception=str(response.code),
                            subject="Grizzly Sanity Check Failed",
                            url=client)
            raise
        else:
            self.sns_logger(status_codes={},
                            exception=str(response.code),
                            subject="Grizzly Sanity Check Passed",
                            url=client)
            print('Sanity check passed: 200 OK')
            return True


if __name__ == "__main__":
    # Initalize class and load command file
    grizzly_config = GrizzlyConfiguration()
    grizzly_config.load_commands("commands.json")

    # Set threadpool
    pool = eventlet.GreenPool(int(grizzly_config.conf["threads"]))

    # Start time is when to start in seconds from time
    try:
        # First publish a message telling the system the test is beginning
        print('Test is starting')
        _thread.start_new_thread(grizzly_config.status_counter, ("thread_1",))
    except:
        # If we can't publish a message or start our thread, exit
        raise

    # Block execution of attack until start_time is triggered
    try:
        start_time = grizzly_config.conf["start_time"]
        grizzly_config.countdown(start_time)
    except:
        raise

    # Perform a sanity check
    if grizzly_config.sanity_check:
        grizzly_config.sanity_check(grizzly_config.sanity_check_url, grizzly_config.computed_requests)

    # Set time interval for attack
    timeout = Timeout(int(grizzly_config.conf["ttl"]), False)

    # Conduct attack until timeout is triggered, then exit gracefully
    try:
        while True:
            for url in grizzly_config.computed_requests["urls"]:  # and not kill switch
                if grizzly_config.verb != "GET":
                    for headers in grizzly_config.computed_requests["headers"]:  # and not kill switch
                        for post_data in grizzly_config.computed_requests["post_data"]:
                            pool.spawn(grizzly_config.generate_request,
                                       grizzly_config.conf["verb"].upper(),
                                       url,
                                       headers,
                                       post_data)
                else:
                    for headers in grizzly_config.computed_requests["headers"]:  # and not kill switch
                        pool.spawn(grizzly_config.generate_request, grizzly_config.conf["verb"].upper(),
                                   url,
                                   headers)
    finally:
        timeout.cancel()

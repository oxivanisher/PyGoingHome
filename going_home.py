#!/usr/bin/env python3

import json
import logging
import requests
import time
import os
import yaml
import sys
import click
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

logging.basicConfig(level=logging.WARNING)


def get_long_duration(age):
    intervals = (
        ('y', 31536000),  # 60 * 60 * 24 * 365
        ('w', 604800),  # 60 * 60 * 24 * 7
        ('d', 86400),  # 60 * 60 * 24
        ('h', 3600),  # 60 * 60
        ('m', 60),
        ('s', 1),
    )

    result = []

    for name, count in intervals:
        value = age // count
        if value:
            age -= value * count
            result.append("%s%s" % (int(value), name))
    return ' '.join(result)


def render_header(location, in_seconds, delay=0):
    if not delay:
        return "Start from %s in %s." % (location, get_long_duration(in_seconds))
    else:
        return "Start from %s in %s (Delay: %s min)" % (location, get_long_duration(in_seconds), delay)


def render_arduino_header(in_seconds, delay=0):
    if not delay:
        return "Start in %s" % (get_long_duration(in_seconds))
    else:
        return "Start in %s +%s min" % (get_long_duration(in_seconds), delay)


def render_delay_line(delay_list):
    ret = []
    for location, delay in delay_list:
        ret.append("%s: %s" % (location, delay))
    return ";".join(ret)


def render_time_line(in_seconds, src, dst):
    return ("In %s from %s to %s" % (get_long_duration(in_seconds),
                                     src,
                                     dst))


def get_fetcher():
    locations_file = os.path.join("config", "locations.yml")
    with open(locations_file) as file:
        logging.debug("Server loading locations from %s" % locations_file)
        locations = yaml.load(file, Loader=yaml.FullLoader)
    fetcher = PublicTransportFetcher()
    fetcher.locations = locations
    return fetcher

class StaticServer(BaseHTTPRequestHandler):

    def execute_arduino_request(self):
        logging.info("Handling arduino request from %s" % self.address_string())
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        fetcher = get_fetcher()
        data = fetcher.run()
        self.wfile.write(json.dumps({'arduino': data['arduino']}).encode("ascii"))

    def execute_json_request(self):
        logging.info("Handling arduino request from %s" % self.address_string())
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        fetcher = get_fetcher()
        self.wfile.write(json.dumps(fetcher.run()).encode("ascii"))

    def execute_html_request(self):
        logging.info("Handling arduino request from %s" % self.address_string())
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        fetcher = get_fetcher()
        data = fetcher.run()
        self.wfile.write("<html><head><title>Going Home</title><h2>%s</h2>%s<br><pre>%s</pre></html>" % (data['header'],
                                                                                                         data['delay'],
                                                                                                         data['all']))

    def do_POST(self):
        if self.path == '/arduino.json':
            self.execute_arduino_request()
        elif self.path == '/all.json':
            self.execute_json_request()
        else:
            self.execute_html_request()

    def do_GET(self):
        if self.path == '/arduino.json':
            self.execute_arduino_request()
        elif self.path == '/all.json':
            self.execute_json_request()
        else:
            self.execute_html_request()


class PublicTransportFetcher:

    def __init__(self):
        self.refreshRate = 299
        self.locations = {}
        self.cacheFile = os.path.join("cache", "PublicTransportFetcherCache.json")
        self.cache = {}

    def load_cache(self):
        logging.debug("Loading cache")
        if os.path.isfile(self.cacheFile):
            logging.debug("Existing cache file found")
            with open(self.cacheFile) as data_file:
                self.cache = json.load(data_file)
        else:
            self.cache = {"last_fetch": 0.0,
                          "channels": {}
                          }
            logging.debug("No existing cache file found")

    def store_cache(self):
        logging.debug("Storing cache")
        with open(self.cacheFile, 'w') as data_file:
            json.dump(self.cache, data_file)

    def fetch_from_opendatach(self):
        logging.debug("Starting to fetch data from http://transport.opendata.ch")

        url = "http://transport.opendata.ch/v1/connections"

        if datetime.now().hour < 12:
            start = self.locations["home"]
            target = self.locations["work"]
            start_location = "home"
        else:
            start = self.locations["work"]
            target = self.locations["home"]
            start_location = "work"

        payload = {"from": start,
                   "to": target}
        r = requests.get(url, params=payload)
        self.cache['data'] = r.json()
        self.cache['last_fetch'] = time.time()
        self.cache['start_location'] = start_location
        self.store_cache()

    def get_data(self):
        self.load_cache()
        if self.cache['last_fetch'] + self.refreshRate < time.time():
            logging.info("Last check to old, need to fetch data")
            self.fetch_from_opendatach()
        else:
            logging.info("Using cached data")

    def generate_output(self):
        ret = {'header': None, 'delay': None, 'details': [], 'error': None, 'arduino': None, 'all': None}
        if "connections" not in self.cache['data'].keys():
            ret['error'] = "No connections found"
            return ret

        header_done = False
        loop_counter = 0
        loop_counter_usable = 0
        for conn in self.cache['data']['connections']:
            loop_counter += 1
            in_seconds = int(conn['from']['departureTimestamp'] - time.time())
            if in_seconds < 1:
                continue
            if not header_done:
                ret['header'] = render_header(self.cache['start_location'], in_seconds, conn['from']['delay'])
                ret['arduino'] = render_arduino_header(in_seconds, conn['from']['delay'])
                ret['all'] = self.cache['data']
                header_done = True

                delay_list = []
                for section in conn['sections']:
                    if section['arrival']['delay']:
                        delay_list.append((section['location']['name'], section['arrival']['delay']))
                if delay_list:
                    ret['details'] = render_delay_line(delay_list)

                ret['details'].append(render_time_line(in_seconds, conn['from']['station']['name'],
                                                       conn['to']['station']['name']))
                loop_counter_usable += 1
        logging.debug("Data sets found: %s; Usable sets: %s" % (loop_counter, loop_counter_usable))

        return ret

    def run(self):
        logging.debug("Run called")
        self.get_data()
        return self.generate_output()


@click.command()
@click.option('--cli', 'mode', flag_value='cli', default=True)
@click.option('--argos', 'mode', flag_value='argos')
@click.option('--server', 'mode', flag_value='server')
def run(mode):
    if mode == "cli" or mode == "argos":
        locations_file = os.path.join("config", "locations.yml")
        with open(locations_file) as file:
            logging.debug("Loading locations from %s" % locations_file)
            locations = yaml.load(file, Loader=yaml.FullLoader)
        fetcher = PublicTransportFetcher()
        fetcher.locations = locations
        output = fetcher.run()

    if mode == "cli":
        logging.debug("Running in cli mode")
        if output['error']:
            print(output['error'])
            sys.exit(1)
        else:
            cli_ret = [output['header']]
            if output['delay']:
                cli_ret.append(output['delay'])
            if output['details']:
                cli_ret.extend(output['details'])
            print("\n".join(cli_ret))
    elif mode == "argos":
        # argos might require one string with \n in it after the header and --- on seperate lines
        logging.debug("Running in argos mode")
        if output['error']:
            print("%s\n---" % output['error'])
            sys.exit(1)
        else:
            argos_ret = [output['header'], "---"]
            if output['delay']:
                argos_ret.append(output['delay'])
            if output['details']:
                argos_ret.append("\\n".join(output['details']))
            print("\n".join(argos_ret) + "| font = monospace")

    elif mode == "server":
        server_class = HTTPServer
        handler_class = StaticServer
        port = 8000
        server_address = ('', port)
        httpd = server_class(server_address, handler_class)
        logging.debug("Running in server mode on port %s" % port)
        httpd.serve_forever()

    else:
        logging.error("Unknown mode: %s" % mode)


if __name__ == '__main__':
    run()

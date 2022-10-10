#!/usr/bin/python3
import json
import socket
import requests
import subprocess
from bottle import run, post, error, route, install, request, response, HTTPResponse, default_app

config = json.loads(open('/scripts/config.json').read())

modes = config['modes']
pins = config['pins']

#modes = [ 'off', 'on']
#pins = { "heat" : 14,
#         "water" : 17
#       }

def pin_state(pin):
    out = subprocess.Popen(['cat', "/sys/class/gpio/gpio%s/value" % (pin)],
           stdout=subprocess.PIPE,
           stderr=subprocess.STDOUT)
    stdout,stderr = out.communicate()
    return int(float(stdout.decode('utf-8')))


def get_pin(pin):
    if pin not in pins:
        return "2"
    pin = pins[pin]
    if isinstance(pin, list):
        result = 0
        for p in pin:
            result += pin_state(p)
        if result < 2:
            return "0"
        return "1"
    return str(pin_state(pin))


def set_pin(pin, mode, timer=False):
    mode = mode.lower()
    if mode not in modes or pin not in pins:
        return "2"
    cmd = ["/scripts/%s" % (pin), mode]
    if timer:
        cmd.append(timer)
    out = subprocess.Popen(cmd,
           stdout=subprocess.PIPE,
           stderr=subprocess.STDOUT)
    stdout,stderr = out.communicate()
    return get_pin(pin)


def get_house_temp(place):
    if place.lower() not in ['up', 'down']:
        return 0
    if place.lower() == 'up':
        return requests.get('http://192.168.0.101:5000/getupstairstemp/').text
    if place.lower() == 'down':
        return requests.get('http://192.168.0.102:5000/gettemp/livingroom').text
    return 0


def get_all_pins():
    output = {
        'human' : {},
        'system' : {}
    }
    for pin in pins:
        if isinstance(pins[pin], list):
            result = 0
            for p in pins[pin]:
                result += pin_state(p)
            if result < 2:
                output['human'][pin] = 'on'
                output['system'][pin] = 0
                continue
            output['human'][pin] = 'off'
            output['system'][pin] = 1
            continue
        state = pin_state(pins[pin])
        output['human'][pin] = modes[state]
        output['system'][pin] = state
    return output


@route('/')
def FUNCTION():
    return None


@route('/getallstates')
def FUNCTION():
    return json.dumps(get_all_pins())


@route('/on/<pin>')
def FUNCTION(pin):
    if pin not in pins:
        print("%s not in %s" % (pin, ', '.join(pins)))
        return "2"
    return set_pin(pin, 'on')


@route('/off/<pin>')
def FUNCTION(pin):
    if pin not in pins:
        print("%s not in %s" % (pin, ', '.join(pins)))
        return "2"
    return set_pin(pin, 'off')


@route('/state/<pin>')
def FUNCTION(pin):
    if pin not in pins:
        print("%s not in %s" % (pin, ', '.join(pins)))
        return "2"
    return get_pin(pin)


@route('/timer/<pin>/<timer>')
def FUNCTION(pin, timer):
    if pin not in pins:
        print("%s not in %s" % (pin, ', '.join(pins)))
        return "2"
    set_pin(pin, 'on', timer)
    return get_pin(pin)


@route('/gettemp/<place>')
def FUNCTION(place):
    return get_house_temp(place)


@route('/devquery')
def FUNCTION():
    return socket.gethostname().title()


@route('/getconfig')
def FUNCTION():
    return json.dumps(config)


@route('/humanstate/<pin>')
def FUNCTION(pin):
    if pin not in pins:
        print("%s not in %s" % (pin, ', '.join(pins)))
        return "2"
    binary_state = int(get_pin(pin))
    return modes[binary_state]


@route('/homeassistant/<pin>')
def FUNCTION(pin):
    if pin not in pins:
        print("%s not in %s" % (pin, ', '.join(pins)))
        return "2"
    state = int(
        not bool(
            int(
                get_pin(pin)
            )
        )
    )
    return str(state)


#run(server='paste', host='192.168.0.100', port=5000, reloader=True, quiet=True)
application = default_app()

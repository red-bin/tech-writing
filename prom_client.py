#!/usr/bin/env python3

import json
import sys
import subprocess

from prometheus_client import start_http_server, Counter, CollectorRegistry
from time import sleep

if __name__ == '__main__':
    FMTSTR='{"server_ip":"%fd.sip","client_ip":"%fd.cip","server_port":"%fd.sport","proc_name":"%proc.name"}'

    cmd = ['/usr/bin/sysdig', '-p', FMTSTR, 'evt.type=connect']

    start_http_server(9100)
    print("server started")

    c = Counter('sysdig_conns', 'Connections from sysdig', labelnames=['server_ip', 'client_ip', 'server_port','proc_name'])

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    for raw_line in iter(proc.stdout.readline,''):
        line = json.loads(raw_line.decode('utf-8'))
        print(line)
    
        c.labels(line['server_ip'], line['client_ip'], line['server_port'], line['proc_name']).inc()

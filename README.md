##Prometheus/sysdig/grafana demo
This is a short intro of prometheus and its potential use. I'm using sysdig as a data source, as I've found it to be extremely good for probing information that would otherwise require significant amount of code. It's also some of the best-polished software I've ever used.

For this demo, I'd like to show that it's possible to map out an infrastructure's application flow using sysdig and a minimal amount of code.

###Quick sysdig rundown
Sysdig uses a kernel module, `sysdig-dkms`, to probe the linux audit subsystem for use within userspace. It's extremely powerful and while it has a small performance impact, the visibility it provides is worth its weight in gold.

Consider visibility into HTTP requests; application code changes would be required in many cases for response status metrics. Sysdig gets around the need for this using 'chisels', which parses through system calls for easy reading/parsing:
```bash
sudo sysdig -j -c httplog

#2017-08-04 13:27:04.319499846 < method=GET url=localhost:9090/metrics response_code=200 latency=2ms size=2842B
#2017-08-04 13:27:04.319512704 > method=GET url=localhost:9090/metrics response_code=200 latency=2ms size=2842B
```

###Socket data for demo
For this demo, I'm just going to pull socket data from any 'connect' system call and format it as json:
```bash
FMTSTR='{"server_ip":"%fd.sip","client_ip":"%fd.cip","server_port":"%fd.sport","proc_name":"%proc.name"}'
sudo /usr/bin/sysdig -p "$FMTSTR" evt.type=connect

#{"server_ip":"127.0.0.1","client_ip":"127.0.0.1","server_port":"9090","proc_name":"prometheus"}
#{"server_ip":"127.0.0.1","client_ip":"127.0.0.1","server_port":"9187","proc_name":"prometheus"}
#{"server_ip":"127.0.1.1","client_ip":"127.0.0.1","server_port":"53","proc_name":"Chrome_IOThread"}
#{"server_ip":"216.58.192.164","client_ip":"10.0.0.138","server_port":"443","proc_name":"Chrome_IOThread"}
#{"server_ip":"127.0.1.1","client_ip":"127.0.0.1","server_port":"53","proc_name":"Chrome_IOThread"}
#{"server_ip":"104.20.43.44","client_ip":"10.0.0.138","server_port":"443","proc_name":"Chrome_IOThread"}
```

###Sysdig data to prometheus client metric endpoint
I'm using the prometheus python client to create a metrics endpoint that increases counters based on the socket information:

```bash
sudo ./prom_client.py 
server started
#{'server_ip': '127.0.0.1', 'proc_name': 'prometheus', 'server_port': '9090', 'client_ip': '127.0.0.1'}
#{'server_ip': '127.0.1.1', 'proc_name': 'Chrome_IOThread', 'server_port': '53', 'client_ip': '127.0.0.1'}
#{'server_ip': '54.83.156.61', 'proc_name': 'Chrome_IOThread', 'server_port': '80', 'client_ip': '10.0.0.138'}
```

This creates an http endpoint with counters that contains:
```bash
wget -O - localhost:9100
#[...]
# HELP sysdig_conns Connections from sysdig
# TYPE sysdig_conns counter
sysdig_conns{client_ip="127.0.0.1",proc_name="prometheus",server_ip="127.0.0.1",server_port="9100"} 2.0
sysdig_conns{client_ip="127.0.0.1",proc_name="prometheus",server_ip="127.0.0.1",server_port="9090"} 3.0
sysdig_conns{client_ip="127.0.0.1",proc_name="prometheus",server_ip="127.0.0.1",server_port="9187"} 1.0
```

###Pulling data into prometheus
Adding this new endpoint is fairly trivial and just requires a few lines of config in `/etc/prometheus/prometheus.yml`:

```
  - job_name: node
    target_groups:
      - targets: ['localhost:9100']
```

The data is then polled at 5 second intervals from the `scrape_interval` parameter:
```
    scrape_interval: 5s
```


###Charting new data
With prometheus pulling this new metrics data, we can now create a chart using prometheus's query language. Particularly, let's chart processes and their connections:
```
sum(rate({__name__="sysdig_conns"}[5m])) by (proc_name, server_ip)
```
http://imgur.com/a/lHPFH

neat.

###88mf mph
I'm not really satisfied with this as the end-all-be-all of prometheus/grafana and want to do something cool with it using Grafana's Diagram plugin and Prometheus's API. So, let's query prometheus for the metric data we just created and convert it to Mermaid syntax:

```bash
PROMHOST="localhost"
ENDPOINT="http://$PROMHOST:9090/api/v1/query_range"
QUERY="sysdig_conns&start=2017-07-25T00:00:00.000Z&end=2017-08-04T20:11:00.000Z&step=100s"

curl 'http://localhost:9090/api/v1/query_range?query=sysdig_conns&start=2017-07-25T00:00:00.000Z&end=2017-08-04T20:11:00.000Z&step=100s' \
  | jq -r '.data.result[].metric | [.client_ip, .server_ip, .server_port] | @csv' \
  | tr -d '"' \
  | awk -F',' '{print $1,"-->",$2":"$3}' \Friday, 04. August 2017 02:09PM 
im
  | egrep -v "127.0.0|:0$" | sort | uniq
  
#10.0.0.138 --> 91.189.88.162:80
#10.0.0.138 --> 91.189.91.23:80
#10.0.0.138 --> 91.189.91.26:80
#10.0.0.138 --> 91.189.92.150:80
#10.0.0.138 --> 91.189.92.191:80
#10.0.0.138 --> 94.31.29.54:443
```

And then throw that into a new graph:
```bash
graph LR
10.0.0.138 --> 91.189.88.162:80
10.0.0.138 --> 91.189.91.23:80
10.0.0.138 --> 91.189.91.26:80
10.0.0.138 --> 91.189.92.150:80
10.0.0.138 --> 91.189.92.191:80
10.0.0.138 --> 94.31.29.54:443
```

Which ends up looking like: ![](http://imgur.com/a/9g7Pc)

###What's next?

This demo was only for a single host, but can be used to graph out entire application infrastructures with relatively minimal effort and performance impact. With a bit of data massaging, appdb querying and such, this can be used to run audits, do application monitoring and much, much more. Have fun!


PROMHOST="localhost"
ENDPOINT="http://$PROMHOST:9090/api/v1/query_range"
QUERY="sysdig_conns&start=2017-07-25T00:00:00.000Z&end=2017-08-04T20:11:00.000Z&step=100s"

curl 'http://localhost:9090/api/v1/query_range?query=sysdig_conns&start=2017-07-25T00:00:00.000Z&end=2017-08-04T20:11:00.000Z&step=100s' \
  | jq -r '.data.result[].metric | [.client_ip, .server_ip, .server_port] | @csv' \
  | tr -d '"' \
  | awk -F',' '{print $1,"-->",$2":"$3}' \
  | egrep -v "127.0.0|:0$" | sort | uniq

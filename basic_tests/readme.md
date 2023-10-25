# Basic MongoDB query language test 

THe `experiments.py` file expresses a simple experiment in formating a query so tha tthe resuls can be analysed. 

To use this you need to 

1. install MongoDB locally with `sudo apt install mongodb`
2. run `./test_data/populate.py`

## Example outputs 

<!-- ```
./experiment.py json 'using messages query1 client_id is 3 and tokens.machine is "DESKTOP-TJR7EI0" and tokens.action like "ileagal.*"' | jq
[
  {
    "rule": "b489a151-6e84-43ce-86d2-40e21791b26b",
    "pattern": "19187f7a-e575-4729-a307-f7e050205bc6",
    "tokens": {
      "date": "Aug  8 11:26:11",
      "machine": "DESKTOP-TJR7EI0",
      "component": "kernel driver",
      "action": "ileagal access request",
      "file": "/opt/dev/device"
    },
    "client_id": 3
  }
]
``` -->

```
./basic_tests/simple_query.py json 'using messages query1 {"client_id": 3} aggregate' | jq
{
  "query1": {
    "metadata": {
      ".rule.b489a151-6e84-43ce-86d2-40e21791b26b": 3,
      ".pattern.19187f7a-e575-4729-a307-f7e050205bc6": 3,
      ".tokens.date.Aug  8 11:26:11": 1,
      ".tokens.machine.DESKTOP-TJR7EI0": 3,
      ".tokens.component.kernel driver": 1,
      ".tokens.action.ileagal access request": 1,
      ".tokens.file./opt/dev/device": 1,
      ".client_id.3": 3,
      ".tokens.date.Aug  8 12:31:25": 1,
      ".tokens.notification.ilegal loggin attempt": 1,
      ".tokens.port.223": 1,
      ".tokens.src_ip_addr.172.16.0.12": 1,
      ".tokens.target_ip_addr.192.168.20.31": 1,
      ".tokens.user.vn_21": 1,
      ".tokens.status.login attempt failed": 1,
      ".tokens.date.Aug  8 12:25:11": 1,
      ".tokens.component.user management": 1,
      ".tokens.access.access granted": 1,
      ".tokens.src_ip_addr.172.17.0.12": 1
    },
    ".rule": "b489a151-6e84-43ce-86d2-40e21791b26b",
    ".pattern": "19187f7a-e575-4729-a307-f7e050205bc6",
    ".tokens.date": [
      "Aug  8 11:26:11",
      "Aug  8 12:31:25",
      "Aug  8 12:25:11"
    ],
    ".tokens.machine": "DESKTOP-TJR7EI0",
    ".tokens.component": [
      "kernel driver",
      "user management"
    ],
    ".tokens.action": "ileagal access request",
    ".tokens.file": "/opt/dev/device",
    ".client_id": 3,
    ".tokens.notification": "ilegal loggin attempt",
    ".tokens.port": 223,
    ".tokens.src_ip_addr": [
      "172.16.0.12",
      "172.17.0.12"
    ],
    ".tokens.target_ip_addr": "192.168.20.31",
    ".tokens.user": "vn_21",
    ".tokens.status": "login attempt failed",
    ".tokens.access": "access granted"
  }
}
```

```
./basic_tests/simple_query.py json 'using messages query_1 sum tokens.machine ;' | jq
{
  "query_1": {
    "tokens.machine": [
      "DESKTOP-TJR7EI0",
      "system-server"
    ]
  }
}
```

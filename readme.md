# Daily updated list of proxy servers

The script collects addresses of proxy servers from 
publicly available resources. Then it tries to connect
(asynchronously) through each proxy server to the 
following websites: `google.com`, `yahoo.com`, `ya.ru`. 
It collects HTTP response statuses, total time of 
web-page downloading (throug proxy) and error messages 
(if error is raised). All this information is stored 
in `proxy.json` file.


# Structure of proxy.json file


```
    {
     'proxies': [<item1>, <item2>, ..., <itemN>]
     'date': <date of creation, utc>
    }
```

Each `item<n>` has the following structure (example):


```
    {
    "ip": xxx.xxx.xxx.xxx,
    "port": xxxx,
    "google_error" : "no",
    "yahoo_error"  : "no",
    "yandex_error" : "unknown error",
    "google_total_time" : 2900,
    "yahoo_total_time" : 1900,
    "yandex_total_time" : None,
    "google_status" : 200,
    "yahoo_status"  : 200,
    "yandex_status" : 503,
    }
```

 * `*_total_time` values are given in milliseconds; each value representes total time (including connection) 
   required to download html-content (through proxy) from either 'google.com', 'yahoo.com' or 'ya.ru'.
 * `*_error` are attributes which represent the error messages raised during 
   connecting to the website through proxy;
 * `*_status` are HTTP status codes;
 * `ip` proxy server's IP address;
 * `port` proxy server's port;


# How to use it


The list of proxy servers is available as json-file through the link:

https://raw.githubusercontent.com/scidam/proxy-list/master/proxy.json

```python

import json
from urllib.request import urlopen

json_url = "https://raw.githubusercontent.com/scidam/proxy-list/master/proxy.json"

with urlopen("json_url") as url:
    json_proxies = json.loads(url.read().decode('utf-8'))

# use json_proxies
print("The total number of proxies: ", len(json_proxies['proxies']))
```

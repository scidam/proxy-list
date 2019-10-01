from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
from collections import Counter
from operator import itemgetter
from datetime import datetime
import json
import aiohttp
import re
import asyncio
import time
import mechanize
import ipaddress
from bs4 import BeautifulSoup
from conf import (TIMEOUT, CHECK_URLS)
import os


def verify_ip_port(ip, port):
    try:
        ipaddress.ip_address(ip)
    except:
        return False
    try:
        if not (1 <= int(port) <= 65535):
            return False
    except ValueError:
        return False
    return True


class Source:
    url = ''

    # simple ip-pattern (check if line starts with something like an ip-address)
    ip_pat = re.compile(r"\s?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}.*")

    def read_url(self):
        data = None
        if self.url:
            with urlopen(self.url) as handler:
                data = handler.read().decode('utf-8')
        return data

    def get_data(self):
        raise NotImplementedError


class SpysList(Source):
    """Get proxies from spys.me"""

    url = 'http://spys.me/proxy.txt'

    def get_data(self):
        data = self.read_url()
        result = list()
        if data:
            for line in data.split('\n'):
                if self.ip_pat.match(line):
                    try:
                        ip, port = line.split()[0].split(':')
                        result.append((ip, port))
                    except:
                        pass
        return result


class FreeProxyList(Source):
    """Get proxies from free-proxy-list.net"""

    url = 'https://free-proxy-list.net'

    def read_url(self):
        br = mechanize.Browser()
        br.set_handle_robots(False)
        # TODO: Probably need user-agent rotation;
        # NOTE: These requests are performed rarely
        br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
        data = None
        resp = br.open(self.url)
        data = resp.read()
        br.close()
        return data

    def get_data(self):
        data = self.read_url()
        soup = BeautifulSoup(data, 'lxml')
        table = soup.find(id="proxylisttable")
        result = list()
        for tr in table.find_all('tr'):
            try:
                td_ip = tr.find_all('td')[0].text.strip()
                td_port = tr.find_all('td')[1].text.strip()
                if self.ip_pat.match(td_ip):
                    result.append((td_ip, td_port))
            except IndexError:
                pass
        return result


class ProxyDailyList(Source):
    """Get proxies from proxy-daily.com"""

    url = 'https://proxy-daily.com/'

    def read_url(self):
        br = mechanize.Browser()
        br.set_handle_robots(False)
        br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
        data = None
        resp = br.open(self.url)
        data = resp.read()
        br.close()
        return data

    def get_data(self):
        data = self.read_url()
        soup = BeautifulSoup(data, 'lxml')
        alist = soup.find("div", class_="centeredProxyList freeProxyStyle")
        result = list()
        for item in alist.text.strip().split():
            splitted = item.split(':')
            result.append(splitted)
        return result


async def check_proxy(proxy):
    """Try to load content of several commonly known websites through proxy"""

    timeout = aiohttp.ClientTimeout(total=TIMEOUT)
    result = dict()
    ip, port = proxy
    result['ip'] = ip
    result['port'] = port

    for website_name, url in CHECK_URLS:
        try:
            async with aiohttp.ClientSession(timeout=timeout, connector=aiohttp.TCPConnector(ssl=False)) as session:
                start = time.time()
                status_code = 404
                total_time = None
                error_msg = 'no'
                async with session.get(url, proxy='http://{}:{}'.format(ip, port)) as resp:
                    status_code = resp.status
                    await resp.text()
                    end = time.time()
                    total_time = int(round(end - start, 2) * 1000)
        except asyncio.TimeoutError:
            status_code = 408
            error_msg = 'timeout error'
        except aiohttp.client_exceptions.ClientProxyConnectionError:
            error_msg = 'connection error'
            status_code = 503
        except Exception as e:
            status_code = 503
            error_msg = 'unknown error: {}.'.format(e)
        finally:
            result[website_name + '_status'] = status_code
            result[website_name + '_error'] = error_msg
            result[website_name + '_total_time'] = total_time
    return result

async def runner(complete_list):
    tasks = [check_proxy(item) for item in complete_list]
    return await asyncio.gather(*tasks)


def main():
    result = []
    complete_list = FreeProxyList().get_data() + SpysList().get_data() + ProxyDailyList().get_data()
    filtered_list = filter(lambda x: verify_ip_port(*x), complete_list)

    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(runner(filtered_list))
    finally:
        loop.close()
    return result


if __name__ == "__main__":
    data = main()

    # proxy-list filtering: removing duplicates
    ip_cntr = Counter(map(itemgetter('ip'), data))
    filtered_data = list(filter(lambda x: ip_cntr[x['ip']] == 1, data))

    # sorting by the number of successfull queries
    try:
        # calculate the number of errorless queries for each proxy
        errorless_measures = [sum(item[resource + '_error'] == 'no' for resource in map(itemgetter(0), CHECK_URLS)) for item in filtered_data]
        argsorted = sorted(range(len(errorless_measures)), key=errorless_measures.__getitem__, reverse=True)
        sorted_data = [filtered_data[ind] for ind in argsorted]
    except KeyError:
        pass

    to_json = {
               'date': str(datetime.utcnow()),
               'proxies': sorted_data
               }

    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, 'proxy.json'), 'w') as f:
        f.write(json.dumps(to_json, sort_keys=True, indent=4))

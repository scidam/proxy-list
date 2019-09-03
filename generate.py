
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
import aiohttp
import re
import asyncio
import time

TIMEOUT = 10

class Source:
    url = ''
    ip_line_pat = re.compile(r"\s?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}.*")

    def read_url(self):
        data = None
        if self.url:
            with urlopen(self.url) as handler:
                data = handler.read().decode('utf-8')
        return data

    def get_data():
        raise NotImplemented


class SpysList(Source):
    url = 'http://spys.me/proxy.txt'

    def get_data(self):
        data = self.read_url()
        result = list()
        if data:
            for line in data.split('\n'):
                if self.ip_line_pat.match(line):
                    try:
                        ip, port = line.split()[0].split(':')
                        result.append((ip, port))
                    except:
                        pass
        return result



class FreeProxyList(Source):
    url = 'https://free-proxy-list.net'

    def read_url(self):
        try:
            import mechanize
        except ImportError:
            print("You should install mechanize first")
            return None

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
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return []

        data = self.read_url()
        soup = BeautifulSoup(data)
        table = soup.find(id="proxylisttable")
        result = list()
        for tr in table.find_all('tr'):
            try:
                td_ip =  tr.find_all('td')[0].text
                td_port = tr.find_all('td')[1].text
                if self.ip_line_pat.match(td_ip):
                    result.append((td_ip, td_port))
            except IndexError:
                pass
        return result


async def check_proxy(proxy):
    timeout = aiohttp.ClientTimeout(total=TIMEOUT)
    urls_to_check =(
                    ('google', 'http://google.com/'),
                    ('yandex', 'http://ya.ru/'),
                    ('yahoo', 'http://yahoo.com/'),
                    ('botsad', 'http://botsad.ru/')
                    )
    result = dict()
    ip = proxy[0]
    port = proxy[1]
    result['ip'] = ip
    result['port'] = port
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            for website_name, url in urls_to_check:
                start = time.time()
                async with session.get(url, proxy='http://{}:{}'.format(ip, port)) as resp:
                    result[website_name] = resp.status
                    await resp.text()
                    end = time.time()
                    result[website_name + '_total_time'] = end - start
                    result[website_name + '_error'] = 'no'
        except asyncio.TimeoutError:
            result[website_name] = 404
            result[website_name + '_total_time'] = ''
            result[website_name + '_error'] = 'timeout'
        except aiohttp.client_exceptions.ClientProxyConnectionError:
            result[website_name] = 404
            result[website_name + '_total_time'] = ''
            result[website_name + '_error'] = 'connection error'
        except Exception as e:
            result[website_name] = 404
            result[website_name + '_total_time'] = ''
            result[website_name + '_error'] = 'unknown error'
    return result

async def runner(complete_list):
    tasks = [check_proxy(item) for item in complete_list]
    return await asyncio.gather(*tasks) 


def main():
    result = dict()
    complete_list = FreeProxyList().get_data() + SpysList().get_data()
    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(runner(complete_list))
    finally:
        loop.close()
    return result


if __name__ == "__main__":
    for item in main():
        if item['google_error'] == 'no':
            print(item)









import base64
import asyncio
import time
import sys
import json
import re
from aiohttp import ClientSession
from aiohttp.helpers import BasicAuth
from aiohttp_socks import ProxyConnector
import ssl
import urllib3
import urllib
urllib3.disable_warnings()
ssl._create_default_https_context = ssl._create_unverified_context

result = {}

async def run(cmd, ret = False):
    print(cmd)
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    if ret:
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            return stdout
        else:
            return False

def decode_base64(data, altchars=b'+/'):
    """Decode base64, padding being optional.

    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    data = re.sub(rb'[^a-zA-Z0-9%s]+' % altchars, b'', data.encode('utf-8'))  # normalize
    missing_padding = len(data) % 4
    if missing_padding:
        data += b'='* (4 - missing_padding)
    return base64.b64decode(data, altchars)

async def get(proxy):
    proxy = 'socks5://{}'.format(proxy)
    connector = ProxyConnector.from_url(proxy)
    try:
        async with ClientSession(connector=connector) as session:
            start = time.perf_counter()
            async with session.get('http://www.google.com/generate_204') as request:
                p = time.perf_counter() - start
                if request.status != 204:
                    p = None
        return p
    except:
        return None


async def send(send, proxy):
    try:
        sys.argv[2]
    except IndexError:
        return
    proxy = 'socks5://{}'.format(proxy)
    connector = ProxyConnector.from_url(proxy, rdns=True)
    async with ClientSession(connector=connector) as session:
        async with session.post('https://api.telegram.org/bot{}/sendMessage'.format(sys.argv[2]), data={"chat_id": "@Proxy0110", "text": send, "parse_mode": "markdown", "disable_web_page_preview": True}, ssl=False):
            pass  # :)


async def ping(ip, port, enc, password, tag, n):
    await run('ss-local -s {} -p {} -l {} -k {} -m {}'.format(ip, port, n, password, enc))
    p = await get("127.0.0.1:{}".format(n))
    return p


async def github(api, method, data={}):
    try:
        sys.argv[1]
    except IndexError:
        return
    async with ClientSession() as session:
        async with session.request(method, "https://api.github.com/{}".format(api), data=json.dumps(data) if len(data) > 0 else None, headers={'Content-Type': 'application/json', 'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'SafaSafari'}, auth=BasicAuth('SafaSafari', sys.argv[1])) as res:
            return (await res.read()).decode('utf-8')


async def upload_github(file):
    with open(file, 'r') as f:
        await github('repos/SafaSafari/SAFA_SS/contents/{}'.format(file), 'PUT', {'message': 'UPDATE', 'content': base64.b64encode(f.read().encode('utf-8')).decode('utf-8'), 'sha': json.loads(await github('repos/SafaSafari/SAFA_SS/contents/{}'.format(file), 'GET'))['sha']})

async def parse_ss(ss):
    if ss[0:5] != "ss://":
        return
    part1 = ss[5:].split("#")
    tag = part1[1] if len(part1) > 1 else ''
    part1 = part1[0]
    if not part1.__contains__("@"):
        part2 = decode_base64(part1).decode('utf-8')
    else:
        p = part1.split("@")
        part2 = decode_base64(p[0]).decode('utf-8') + "@" + p[1]
    part3 = part2.split("@")
    ip, port = part3[1].split(':')
    p2 = part3[0].split(':')
    enc = p2[0]
    password = p2[1]
    return [ip, port, enc, password, urllib.parse.quote(urllib.parse.unquote(tag))]

async def main(n, ss):
    global result
    ss = ss.strip()
    parse = await parse_ss(ss)
    if parse:
        p = await ping(*parse, n)
        if p != None:
            p = (p * 100).__round__()
            result[ss + ("#" if '#' not in ss else '') + urllib.parse.quote("@Proxy0110")] = p


async def gather():
    global result
    with open('source_ss.txt') as f:
        source = f.read()
    source = source.split("\n")
    n = 30
    chunk = [source[i:i + n] for i in range(0, len(source), n)]
    for proxies in chunk:
        await asyncio.gather(*[main(n+3333, proxies[n]) for n in range(0, len(proxies) - 1)])
        await run('killall ss-local')
        print(str(source.index(proxies[0])) + '/' + str(len(source)), end="\r")
        await asyncio.sleep(3)
    sort = {k: v for k, v in sorted(
        result.items(), key=lambda item: item[1])}
    leaf = []
    for proxy in sort:
        leaf.append("SS=ss,{},{},encrypt-method={},password={}#{}".format(*(await parse_ss(proxy))))
    text = "Shadowsocks Proxy\n\n"
    text = text.__add__("\n".join("`{}`\nPing:{}\n".format(
        server, str(ping)) for server, ping in list(sort.items())[:10]))
    sslocal = []
    for proxy in sort:
        sslocal.append("ss-local -s {} -p {} -l 3993 -m {} -k {} # {}".format(*(await parse_ss(proxy))))
    ip, port, enc, password, tag = await parse_ss(list(sort.items())[0][0])
    await run('ss-local -s {} -p {} -l {} -k {} -m {}'.format(ip, port, 9999, password, enc))
    with open('ss.txt', 'w+') as f:
        f.write("\n".join(sort))

    with open('leaf.txt', 'w+') as f:
        f.write("\n".join(leaf))

    with open('ss-local.txt', 'w+') as f:
        f.write("\n".join(sslocal))

    with open("SUBSCRIBE", "w+") as f:
        f.write(base64.b64encode(b"\n".join(server.encode('utf-8')
                for server, ping in list(sort.items())[:10])).decode('utf-8'))
    await upload_github('SUBSCRIBE')
    await upload_github('ss.txt')
    await upload_github('leaf.txt')
    await upload_github('ss-local.txt')
    await send(text, '127.0.0.1:9999')

loop = asyncio.get_event_loop()
loop.run_until_complete(gather())

import re
import sys
import flag
import json
import time
import base64
import pproxy
import urllib
import asyncio
from aiohttp import ClientSession
from aiohttp.helpers import BasicAuth
from aiohttp_socks import ProxyConnector

result = []


def decode_base64(data, altchars=b'+/'):
    """Decode base64, padding being optional.

    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    data = re.sub(rb'[^a-zA-Z0-9%s]+' % altchars, b'',
                  data.encode('utf-8'))  # normalize
    missing_padding = len(data) % 4
    if missing_padding:
        data += b'=' * (4 - missing_padding)
    return base64.b64decode(data, altchars)


async def send(send):
    try:
        sys.argv[2]
    except IndexError:
        return
#     proxy = 'socks5://127.0.0.1:3993'
#     connector = ProxyConnector.from_url(proxy, rdns=True)
    async with ClientSession() as session: # connector=connector
        async with session.post('https://api.telegram.org/bot{}/sendMessage'.format(sys.argv[2]), data={"chat_id": "@Proxy0110", "text": send, "parse_mode": "markdown", "disable_web_page_preview": True}, ssl=False):
            pass  # :)


async def ping(ss):
    try:
        ip, port, enc, password, tag = await parse_ss(ss)
        if not ip:
            return [None]*6
        start = time.perf_counter()
        conn = pproxy.Connection(
            'ss://{}:{}@{}:{}'.format(enc, password, ip, port))
        reader, writer = await conn.tcp_connect('google.com', 80)
        writer.write(b'GET /generate_204 HTTP/1.1\r\n\r\n')
        data = await reader.read(1024*16)
        if not 'HTTP/1.1 204 No Content' in data.decode('utf-8'):
            return [None]*6
        p = time.perf_counter() - start
    except:
        return [None]*6
    try:
        reader, writer = await conn.tcp_connect('ipinfo.io', 80)
        writer.write(b'GET / HTTP/1.1\r\nHost: ipinfo.io\r\n\r\n')
        data = await reader.read(1024*32)
        result = json.loads(data.decode('utf-8').split('\r\n\r\n')[1])
        location = '{} {} - {} - {} - {}'.format(flag.flag(
            result['country']), result['country'], result['region'], result['city'], result['org'])
    except:
        location = 'UNKNOWN'
    return [p, ip, port, enc, password, urllib.parse.quote(location)]


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
        return [None]*5
    part1 = ss[5:].split("#")
    tag = part1[1] if len(part1) > 1 else ''
    part1 = part1[0]
    if not part1.__contains__("@"):
        s = decode_base64(part1).decode('utf-8')
    else:
        p = part1.split("@")
        s = decode_base64(p[0]).decode('utf-8') + "@" + p[1]
    regex = re.match(r"(?i)^(.+?):(.*)@(.+?):(\d+)", s)
    enc, password, ip, port = regex.groups()
    return [ip, port, enc, password, urllib.parse.quote(urllib.parse.unquote(tag))]


async def main(ss):
    global result
    ss = ss.strip()
    p, ip, port, enc, password, location = await ping(ss)
    if p != None:
        p = (p * 100).__round__()
        result.append([ip, port, enc, password, location, p])


async def gather():
    global result
    with open('source_ss.txt') as f:
        source = f.read()
    source = source.split("\n")
    n = 30
    chunk = [source[i:i + n] for i in range(0, len(source), n)]
    for proxies in chunk:
        await asyncio.gather(*[main(proxies[n]) for n in range(0, len(proxies) - 1)])

    sort = sorted(result, key=lambda x: x[5])
    sort = sorted(sort, key=lambda x: not (
        len(str(x[1])) < 4 or x[1] in [8080]))

    leaf = []
    sslocal = []
    for index, proxy in enumerate(sort):
        leaf.append(
            "SS{}=ss,{},{},encrypt-method={},password={}#{}".format(index, *proxy[:-1]))
        sslocal.append(
            "ss-local -s {} -p {} -l 3993 -m {} -k {} # {}".format(*proxy[:-1]))

    text = "\n".join("`ss://{}#{}`\nPing:{}\n".format(base64.b64encode('{}:{}@{}:{}'.format(enc, password, ip, port).encode('utf-8')).decode('utf-8'), location, str(ping))
                     for ip, port, enc, password, location, ping in sort[:10])
    text += '\n\n@Proxy0110'
    with open('ss.txt', 'w+') as f:
        f.write("\n".join("ss://{}#{}".format(base64.b64encode('{}:{}@{}:{}'.format(enc, password, ip, port).encode('utf-8')).decode('utf-8'), location)
                          for ip, port, enc, password, location, ping in sort))

    with open('leaf.txt', 'w+') as f:
        f.write("\n".join(leaf))

    with open('ss-local.txt', 'w+') as f:
        f.write("\n".join(sslocal))

    with open("SUBSCRIBE", "wb+") as f:
        f.write(base64.b64encode("\n".join(["ss://{}#{}".format(base64.b64encode('{}:{}@{}:{}'.format(enc, password, ip, port).encode(
            'utf-8')).decode('utf-8'), location) for ip, port, enc, password, location, ping in sort[:10]]).encode('utf-8')))

    await upload_github('SUBSCRIBE')
    await upload_github('ss.txt')
    await upload_github('leaf.txt')
    await upload_github('ss-local.txt')
    await send(text)

loop = asyncio.get_event_loop()
loop.run_until_complete(gather())

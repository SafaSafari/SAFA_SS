import base64
import asyncio
import time
import sys
import json
from aiohttp import ClientSession
from aiohttp.helpers import BasicAuth
from aiohttp_socks import ProxyConnector

result = {}


async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)


async def get(proxy, send=False):
    proxy = 'socks5://{}'.format(proxy)
    connector = ProxyConnector.from_url(proxy)
    try:
        async with ClientSession(connector=connector) as session:
            start = time.perf_counter()
            async with session.get('http://clients1.google.com/generate_204') as request:
                p = time.perf_counter() - start
                if request.status != 204:
                    p = None
        return p
    except:
        return None


async def send(send):
    if not sys.argv[1]:
        return
    async with ClientSession() as session:
        async with session.post('https://api.telegram.org/bot{}/sendMessage'.format(sys.argv[1]), data={"chat_id": "@SafaProxy", "text": send, "parse_mode": "markdown", "disable_web_page_preview": True}):
            pass  # :)


async def ping(ip, port, enc, password, n):
    await run('ss-local -s {} -p {} -l {} -k {} -m {}'.format(ip, port, n, password, enc))
    p = await get("127.0.0.1:{}".format(n))
    return p


async def github(api, method, data={}):
    if not sys.argv[2]:
        return
    async with ClientSession() as session:
        async with session.request(method, "https://api.github.com/{}".format(api), data=json.dumps(data) if len(data) > 0 else None, headers={'Content-Type': 'application/json', 'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'SafaSafari'}, auth=BasicAuth('SafaSafari', sys.argv[2])) as res:
            return (await res.read()).decode('utf-8')


async def upload_github(file):
    with open(file, 'w+') as f:
        await github('repos/SafaSafari/SAFA_SS/contents/{}'.format(file), 'PUT', {'message': 'UPDATE', 'content': base64.b64encode(f.read().encode('utf-8')).decode('utf-8'), 'sha': json.loads(await github('repos/SafaSafari/SAFA_SS/contents/SUBSCRIBE', 'GET'))['sha']})


async def main(n, ss):
    global result
    if ss[0:5] != "ss://":
        return
    part1 = ss[5:].split("#")
    country = part1[1]
    part1 = part1[0]
    if not part1.__contains__("@"):
        part2 = base64.b64decode(part1).decode('utf-8')
    else:
        p = part1.split("@")
        part2 = base64.b64decode(p[0]).decode('utf-8') + "@" + p[1]
    part3 = part2.split("@")
    ip, port = part3[1].split(':')
    enc, password = part3[0].split(':')
    p = await ping(ip, port, enc, password, n)
    if p != None:
        p = (p * 100).__round__()
        result["ss://{}#{}@SafaProxy".format(part1, country)] = p


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
    sort = {k: v for k, v in sorted(
        result.items(), key=lambda item: item[1])}
    text = "Shadowsocks Proxy\n[Source](https://github.com/SafaSafari/SAFA_SS)\n\n"
    text = text.__add__("\n".join("`{}`\nPing:{}\n".format(
        server, str(ping)) for server, ping in sort.items()))
    await send(text)
    with open('ss.txt', 'w+') as f:
        f.write("\n".join(sort))
    with open("SUBSCRIBE", "w+") as f:
        f.write(base64.b64encode(b"\n".join(server.encode('utf-8')
                for server, ping in list(sort.items())[:10])).decode('utf-8'))
    await upload_github('SUBSCRIBE')
    await upload_github('ss.txt')

loop = asyncio.get_event_loop()
loop.run_until_complete(gather())

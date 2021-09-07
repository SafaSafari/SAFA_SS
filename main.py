import base64
import asyncio
import time
import sys
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector

result = {}

async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

async def get(proxy, send = False):
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
    if not sys.argv[1]: return
    async with ClientSession() as session:
        async with session.post('https://api.telegram.org/bot{}/sendMessage'.format(sys.argv[1]), data={"chat_id": "43390784", "text": send}): pass # :)
async def ping(ip, port, enc, password, n):
    await run('ss-local -s {} -p {} -l {} -k {} -m {}'.format(ip, port, n, password, enc))
    p = await get("127.0.0.1:{}".format(n))
    return p

async def main(n, ss):
    global result
    if ss[0:5] != "ss://":
        return
    part1 = ss[5:].split("#")[0]
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
        result['ss://' + part1 + "#@SafaProxy"] = p
    
async def gather():
    global result
    with open('source_ss.txt') as f:
        source = f.read()
    list = source.split("\n")
    n = 30
    chunk = [list[i:i + n] for i in range(0, len(list), n)]
    for proxies in chunk:
        await asyncio.gather(*[main(n+3333, proxies[n]) for n in range(0, len(proxies) - 1)])
        await run('killall ss-local')
        print(str(list.index(proxies[0])) + '/' + str(len(list)), end="\r")
    sort = {k: v for k, v in sorted(
        result.items(), key=lambda item: item[1])}
    text = "\n".join("{}\nPing:{}\n".format(server, str(ping)) for server, ping in sort.items())
    send(text)
    with open('ss.txt', 'w+') as f:
        f.write("\n".join(sort))
    
loop = asyncio.get_event_loop()
loop.run_until_complete(gather())

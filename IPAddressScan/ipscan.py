import socket
import struct
import asyncio
import logging

logging.basicConfig(filename='scan_log.txt', level=logging.INFO, format='%(message)s')


async def scan_ip(ip_address):
    try:
        await asyncio.wait_for(asyncio.open_connection(ip_address, 1883), timeout=2)
        logging.info(ip_address)
    except asyncio.TimeoutError:
        pass
    except ConnectionRefusedError:
        pass
    except Exception as e:
        pass


async def scan_ip_range(start_ip, end_ip):
    tasks = []
    for ip in range(start_ip, end_ip + 1):
        ip_address = socket.inet_ntoa(struct.pack('!I', ip))
        print(ip_address)
        tasks.append(scan_ip(ip_address))
        if len(tasks) == 100 * 100:
            await asyncio.gather(*tasks)
            tasks = []
    if tasks:
        await asyncio.gather(*tasks)


ranges = [
    ("9.30.0.0", "9.255.255.255"),
    # ("11.0.0.0", "100.63.255.255"),
    # ("100.128.0.0", "126.255.255.255"),
    # ("128.0.0.0", "169.253.255.255"),
    # ("169.255.0.0", "172.15.255.255"),
    # ("173.32.0.0", "191.255.255.255"),
    # ("192.0.1.0", "192.88.98.255"),
    # ("192.88.100.0", "192.167.255.255"),
    # ("192.169.0.0", "198.17.255.255"),
    # ("198.20.0.0", "233.255.255.255")
]


async def main():
    total_ips_scanned = 0
    for start, end in ranges:
        start_ip = struct.unpack('!I', socket.inet_aton(start))[0]
        end_ip = struct.unpack('!I', socket.inet_aton(end))[0]
        await scan_ip_range(start_ip, end_ip)
        total_ips_scanned += (end_ip - start_ip + 1)


asyncio.run(main())

import socket
import struct
import asyncio
import logging
from datetime import datetime

# Configure logging to only record successful connections
logging.basicConfig(
    filename='successful_connections.txt',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class IPScanner:
    def __init__(self, concurrent_tasks=1000):
        self.concurrent_tasks = concurrent_tasks
        self.queue = asyncio.Queue()
        self.active_tasks = set()
        self.successful_ips = set()
        
    async def scan_single_ip(self, ip_address):
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip_address, 1883),
                timeout=2
            )
            # Only log successful connections
            logging.info(f"{ip_address}")
            self.successful_ips.add(ip_address)
            writer.close()
            await writer.wait_closed()
        except:
            # Silently ignore all failed connections
            pass

    async def worker(self):
        while True:
            try:
                ip_address = await self.queue.get()
                task = asyncio.create_task(self.scan_single_ip(ip_address))
                self.active_tasks.add(task)
                task.add_done_callback(self.active_tasks.discard)
                self.queue.task_done()
            except asyncio.CancelledError:
                break

    def ip_range_generator(self, start_ip, end_ip):
        start = struct.unpack('!I', socket.inet_aton(start_ip))[0]
        end = struct.unpack('!I', socket.inet_aton(end_ip))[0]
        
        for ip in range(start, end + 1):
            yield socket.inet_ntoa(struct.pack('!I', ip))

    async def scan_range(self, ranges):
        workers = [asyncio.create_task(self.worker()) 
                  for _ in range(self.concurrent_tasks)]

        total_ips = 0
        start_time = datetime.now()
        
        for start_ip, end_ip in ranges:
            for ip in self.ip_range_generator(start_ip, end_ip):
                await self.queue.put(ip)
                total_ips += 1

        await self.queue.join()
        
        for worker in workers:
            worker.cancel()
        
        await asyncio.gather(*workers, return_exceptions=True)
        
        # Log final statistics
        print(f"Scan completed. Found {len(self.successful_ips)} responsive IPs.")
        print(f"Results have been logged to successful_connections.txt")
        
        return self.successful_ips

async def main():
    ranges = [
        ("1.0.0.0", "9.255.255.255"),
        ("11.0.0.0", "100.63.255.255"),
        # Add more ranges as needed
    ]
    
    scanner = IPScanner(concurrent_tasks=1000)
    await scanner.scan_range(ranges)

if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import time
import subprocess
import matplotlib.pyplot as plt
from collections import defaultdict
import os
import json

# Configuration
BROKER_PORT = 1883
PACKET_BYTES_TO_SEND = 10
MAX_WAIT_TIME = 60  # Maximum time to wait for remote FIN (seconds)
BATCH_SIZE = 100  # Process 100 IPs at a time
SAVE_INTERVAL = 100  # Save results after every 100 batches
MQTT_CONNECT_PACKET = bytes([
    0x10, 0x1E, 0x00, 0x04, ord('M'), ord('Q'), ord('T'), ord('T'), 0x04,
    0x02, 0x00, 0x1E, 0x00, 0x06, ord('s'), ord('l'), ord('o'), ord('w'), ord('i'), ord('d')
])

closure_times = []
tcpdump_process = None

async def send_connect_packet(broker_ip):
    """Send CONNECT packet without closing connection."""
    start_time = time.time()
    writer = None

    try:
        # Establish connection with timeout
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(broker_ip, BROKER_PORT),
            timeout=5
        )
        
        # Send partial CONNECT packet
        writer.write(MQTT_CONNECT_PACKET[:PACKET_BYTES_TO_SEND])
        await writer.drain()

        # Wait for remote FIN or timeout
        try:
            await asyncio.wait_for(reader.read(), timeout=MAX_WAIT_TIME)
        except asyncio.TimeoutError:
            pass  # Max wait time reached

    except Exception:
        pass  # Silence errors but track closure time
    finally:
        closure_duration = time.time() - start_time
        closure_times.append((broker_ip, closure_duration))
        
        # Do not send FIN; abort connection instead
        if writer is not None:
            writer.transport.abort()

def start_packet_capture(batch_num):
    """Start tcpdump packet capture for a specific batch."""
    global tcpdump_process
    
    # Create pcap filename with batch number
    pcap_filename = f"mqtt_responses_batch_{batch_num}.pcap"
    
    tcpdump_process = subprocess.Popen([
        'sudo', 'tcpdump',
        '-i', 'any',
        '-w', pcap_filename,
        f'tcp port {BROKER_PORT}'
    ])
    print(f"Packet capture started for batch {batch_num}.")
    return pcap_filename

def stop_packet_capture():
    """Stop tcpdump packet capture."""
    if tcpdump_process:
        tcpdump_process.terminate()
        # Give tcpdump time to properly save the file
        time.sleep(1)
        print("Packet capture stopped.")

def plot_closure_timeline(batch_times, batch_num, is_cumulative=False):
    """Plot time vs number of closed connections."""
    time_counts = defaultdict(int)
    for _, t in batch_times:
        time_counts[int(t)] += 1

    times = sorted(time_counts.keys())
    if not times:
        print("No connection data collected for this batch.")
        return

    cumulative = 0
    x, y = [], []

    for t in range(0, max(times) + 1):
        cumulative += time_counts.get(t, 0)
        x.append(t)
        y.append(cumulative)

    plt.figure(figsize=(12, 6))
    plt.step(x, y, where='post', color='b')
    
    title_prefix = "Cumulative" if is_cumulative else "Batch"
    plt.title(f'{title_prefix} Connection Closure Timeline - Batch {batch_num}')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Cumulative Closed Connections')
    plt.grid(True)
    
    # Save with appropriate filename
    filename = f"results/closure_timeline_{'cumulative' if is_cumulative else 'batch'}_{batch_num}.png"
    plt.savefig(filename, dpi=300)
    print(f"Graph saved as {filename}")
    plt.close()  # Close the figure to prevent display and save memory

def save_cumulative_results(all_closure_times, save_batch_num):
    """Save cumulative results from start to current batch."""
    # Convert to serializable format
    serializable_data = [(ip, float(duration)) for ip, duration in all_closure_times]
    
    # Save as JSON
    filename = f"results/cumulative_results_through_batch_{save_batch_num}.json"
    with open(filename, 'w') as f:
        json.dump(serializable_data, f)
    
    print(f"Cumulative results saved to {filename}")

async def main():
    """Main execution flow with batch processing and per-batch results."""
    # Create results directory if it doesn't exist
    os.makedirs("results", exist_ok=True)
    
    try:
        # Read IP addresses from file change this to your file name
        # Ensure the file exists and is not empty
        with open("ip.txt", "r") as file:
            ip_addresses = [line.strip() for line in file if line.strip()]
        
        total_batches = (len(ip_addresses) + BATCH_SIZE - 1) // BATCH_SIZE
        all_closure_times = []  # To track all results cumulatively
        last_save_batch = 0
        
        # Process IPs in batches of 100
        for batch_num, i in enumerate(range(0, len(ip_addresses), BATCH_SIZE), 1):
            batch = ip_addresses[i:i+BATCH_SIZE]
            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} IPs)")
            
            # Clear batch-specific closure times
            closure_times.clear()
            
            # Start packet capture for this batch
            pcap_file = start_packet_capture(batch_num)
            
            # Create and run tasks for this batch
            batch_tasks = [send_connect_packet(ip) for ip in batch]
            await asyncio.gather(*batch_tasks)
            
            # Stop packet capture for this batch
            stop_packet_capture()
            
            # Save batch results
            all_closure_times.extend(closure_times)
            
            # Plot and save batch-specific graph
            plot_closure_timeline(closure_times, batch_num, is_cumulative=False)
            
            # Check if it's time to save cumulative results (every 100 batches)
            if batch_num % SAVE_INTERVAL == 0:
                # Plot and save cumulative graph (from start to current batch)
                plot_closure_timeline(all_closure_times, batch_num, is_cumulative=True)
                
                # Save cumulative results from start to current batch
                save_cumulative_results(all_closure_times, batch_num)
                last_save_batch = batch_num
                
                print(f"SAVE POINT: Cumulative results through batch {batch_num} saved")
            
            print(f"Completed batch {batch_num}/{total_batches}")
            print(f"Results saved in pcap file: {pcap_file}")
            print(f"Batch connections: {len(closure_times)}")
            print(f"Total connections so far: {len(all_closure_times)}")
            print("=" * 50)

        # If we've processed batches but haven't saved the final set
        # (when total batches isn't a multiple of SAVE_INTERVAL)
        if last_save_batch != batch_num:
            # Plot and save final cumulative graph
            plot_closure_timeline(all_closure_times, batch_num, is_cumulative=True)
            
            # Save final cumulative results
            save_cumulative_results(all_closure_times, batch_num)
            
            print(f"FINAL SAVE: Cumulative results through batch {batch_num} saved")

    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        
        # Save results up to the point of interruption if not recently saved
        current_batch = len(all_closure_times) // BATCH_SIZE + 1
        if current_batch - last_save_batch > 10:  # If it's been a while since last save
            save_cumulative_results(all_closure_times, current_batch - 1)
            print(f"INTERRUPT SAVE: Cumulative results through batch {current_batch-1} saved")
    
    finally:
        # Ensure packet capture is stopped
        stop_packet_capture()
        print(f"Total tested connections: {len(all_closure_times)}")

if __name__ == "__main__":
    asyncio.run(main())
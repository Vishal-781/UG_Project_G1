import paho.mqtt.client as mqtt
import time
import threading
import csv
from queue import Queue
from scapy.all import sniff, IP, TCP, wrpcap

# Configuration
TTL_VALUES = [40]  # Test with different TTL values
MQTT_PORT = 1883
PCAP_FILE = "mqtt_capture4.pcap"
LOG_FILE = "mqtt_vulnerability_report4.csv"
SUMMARY_FILE = "summary_report4.txt"
THREAD_COUNT = 50  # Number of parallel connections

# Store results
results = []
result_lock = threading.Lock()

# Counters for real-time printing
secure_count = 0
vulnerable_count = 0

# Read IPs from file
def read_ip_addresses(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        print(f"[-] File not found: {file_path}")
        return []

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    userdata['connected_time'] = time.time()

def on_disconnect(client, userdata, rc):
    userdata['disconnected_time'] = time.time()

# Attempt MQTT connection with TTL settings
def test_broker(ip, ttl):
    global secure_count, vulnerable_count

    client = mqtt.Client()
    client.reconnect_delay_set(min_delay=0, max_delay=0)  # Prevent auto-reconnect
    userdata = {
        'start_time': time.time(),
        'ttl': ttl,
        'status': "No Response",
        'connected_time': None,
        'disconnected_time': None
    }
    client.user_data_set(userdata)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    try:
        client.connect(ip, MQTT_PORT, keepalive=ttl)
        client.loop_start()

        # Wait until TTL + 5s or until the broker disconnects
        while time.time() - userdata['start_time'] < ttl + 5:
            if userdata['disconnected_time'] is not None:
                break  
            time.sleep(0.5)

        client.loop_stop()  

        # Determine broker behavior
        if userdata['connected_time'] is None:
            userdata['status'] = "Secure"
            secure_count += 1
        elif userdata['disconnected_time'] is None:
            userdata['status'] = "Vulnerable (Never closed)"
            vulnerable_count += 1
        else:
            elapsed = userdata['disconnected_time'] - userdata['connected_time']
            if elapsed <= ttl:
                userdata['status'] = "Secure"
                secure_count += 1
            else:
                userdata['status'] = "Vulnerable (Delayed)"
                vulnerable_count += 1

    except Exception:
        userdata['status'] = "Secure"
        secure_count += 1

    total_time = time.time() - userdata['start_time']

    with result_lock:
        results.append([ip, ttl, total_time, userdata['status']])

    print(f"[*] {ip} - TTL={ttl}s - Total Time={total_time:.2f}s - Status={userdata['status']}")
    print(f"[🔹] Secure: {secure_count} | Vulnerable: {vulnerable_count}")

# Worker function for threading
def worker(ip_queue):
    while not ip_queue.empty():
        ip, ttl = ip_queue.get()
        test_broker(ip, ttl)
        ip_queue.task_done()

# Packet capture function
def packet_callback(packet):
    if packet.haslayer(TCP) and packet.haslayer(IP):
        wrpcap(PCAP_FILE, packet, append=True)

def start_sniffing():
    sniff(filter=f"port {MQTT_PORT}", prn=packet_callback, store=0)

# Run the attack
if __name__ == '__main__':
    ip_list = read_ip_addresses("Scan_Log_Final.txt")
    ip_queue = Queue()
    
    for ip in ip_list:
        for ttl in TTL_VALUES:
            ip_queue.put((ip, ttl))
    
    # Start packet capture in a separate thread
    sniff_thread = threading.Thread(target=start_sniffing, daemon=True)
    sniff_thread.start()

    # Start worker threads
    threads = []
    for _ in range(THREAD_COUNT):
        thread = threading.Thread(target=worker, args=(ip_queue,))
        thread.start()
        threads.append(thread)
    
    # Wait for all threads to finish
    ip_queue.join()
    for thread in threads:
        thread.join()
    
    # Save results to CSV
    with open(LOG_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Broker IP", "TTL", "Response Time", "Status"])
        writer.writerows(results)

    # Save summary report
    with open(SUMMARY_FILE, "w") as file:
        file.write(f"Total Secure Brokers: {secure_count}\n")
        file.write(f"Total Vulnerable Brokers: {vulnerable_count}\n")

    print(f"[✅] Vulnerability report saved: {LOG_FILE}")
    print(f"[✅] Summary report saved: {SUMMARY_FILE}")
    print(f"[✅] Packet capture saved: {PCAP_FILE}")

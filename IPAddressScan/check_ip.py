import socket


def check_mqtt_service(ip, port):
    try:
        # Attempt to connect to the IP address on the specified port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)  # Set a timeout for the connection attempt
        result = s.connect_ex((ip, port))
        if result == 0:
            print(f"IP Address {ip} has MQTT service running on port {port} \n")
        else:
            print(f"IP Address {ip} does not have MQTT service running on port {port} \n")
        s.close()
    except socket.error as e:
        print(f"Error: {e}")


# Define a list of IP addresses to check
ip_addresses = ["45.41.94.174", "192.56.226.148", "83.220.247.170", "80.81.224.254", "92.134.111.203", "185.73.39.214",
                "10.0.49.110", "45.192.214.51"]

# Check each IP address in the list
for ip_address in ip_addresses:
    check_mqtt_service(ip_address, 1883)

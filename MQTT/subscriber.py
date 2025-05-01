# import paho.mqtt.client as mqtt

# # Define the MQTT broker's address and port
# broker_address = "localhost"
# broker_port = 1883


# # Callback function to handle incoming messages
# def on_message(client, userdata, message):
#     print("Received message on topic '{}': {}".format(message.topic, message.payload.decode()))


# # Create a client instance
# client = mqtt.Client("subscriber",protocol=mqtt.MQTTv311)

# # Attach the callback function to the client
# client.on_message = on_message

# # Connect to the broker
# client.connect(broker_address, broker_port)

# # Subscribe to the topic "test"
# client.subscribe("test")

# # Start the MQTT loop to listen for messages
# client.loop_forever()

import paho.mqtt.client as mqtt
import sys

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully")
        # Subscribe to topic after successful connection
        client.subscribe("test")
        print("Subscribed to topic: test")
    else:
        print(f"Connection failed with code {rc}")
        sys.exit(1)

def on_message(client, userdata, message):
    try:
        decoded_message = message.payload.decode()
        print(f"Received message on topic '{message.topic}': {decoded_message}")
    except Exception as e:
        print(f"Error decoding message: {e}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"Unexpected disconnection. Code: {rc}")
    else:
        print("Disconnected successfully")

try:
    # Create client instance
    client = mqtt.Client("subscriber", protocol=mqtt.MQTTv311)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    # Connect to broker
    print(f"Connecting to broker at {broker_address}:{broker_port}")
    client.connect(broker_address, broker_port)
    
    # Start the loop to process messages
    print("Starting message loop... Press Ctrl+C to exit")
    client.loop_forever()

except KeyboardInterrupt:
    print("\nDisconnecting from broker...")
    client.disconnect()
    print("Exited successfully")
except Exception as e:
    print(f"An error occurred: {e}")
    if client:
        client.disconnect()
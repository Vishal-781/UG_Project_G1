# import paho.mqtt.client as mqtt # type: ignore

# # Define the MQTT broker's address and port
# broker_address = "localhost"
# broker_port = 1883

# # Create a client instance
# client = mqtt.Client("publisher", callback_api_version=2)

# # Connect to the broker
# client.connect(broker_address, broker_port)

# # Publish a message to the topic "test"
# client.publish("test", "Hello! This is a test message!")

# # Disconnect from the broker
# client.disconnect()
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully")
    else:
        print(f"Connection failed with code {rc}")

def on_publish(client, userdata, mid):
    print(f"Message {mid} published successfully")

try:
    # Create client instance without specifying callback_api_version
    client = mqtt.Client("publisher", protocol=mqtt.MQTTv311)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_publish = on_publish
    
    # Connect to broker
    client.connect("localhost", 1883)
    
    # Start the loop
    client.loop_start()
    
    # Publish message
    result = client.publish("test", "Hello! This is a test message!")
    
    # Wait briefly for the message to be published
    import time
    time.sleep(1)
    
    # Disconnect
    client.loop_stop()
    client.disconnect()

except Exception as e:
    print(f"An error occurred: {e}")
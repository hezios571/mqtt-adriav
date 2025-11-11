import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
TOPIC = "adriav/test"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, PORT)

message = "hello from injector"
client.publish(TOPIC, message)
print(f"[injector] sent: {message}")

client.disconnect()

import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
TOPIC = "adriav/test"

def on_message(client, userdata, msg):
    print(f"[controller] received on {msg.topic}: {msg.payload.decode()}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(BROKER, PORT)
client.subscribe(TOPIC)

print("[controller] connected and waiting for messages...")
client.loop_forever()

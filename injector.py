import paho.mqtt.client as mqtt
import base64
import json
import os

BROKER = "localhost"
PORT = 1883
FILE_TOPIC = "adriav/file/transfer"
ACK_TOPIC = "adriav/file/ack"

CHUNK_SIZE = 50000  # ~50KB chunks

def on_message(client, userdata, msg):
    print(f"\n[injector] received on {msg.topic}: {msg.payload.decode()}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(BROKER, PORT)

client.subscribe(ACK_TOPIC)
client.loop_start()

def send_file(path):
    with open(path, "rb") as f:
        data = f.read()

    file_type = path.split(".")[-1]
    total_bytes = len(data)
    encoded = base64.b64encode(data).decode()

    # break into chunks
    chunks = [encoded[i:i+CHUNK_SIZE] for i in range(0, len(encoded), CHUNK_SIZE)]
    total_chunks = len(chunks)

    print(f"[injector] sending {path} in {total_chunks} chunks...")

    # send all chunks
    for idx, chunk in enumerate(chunks):
        message = {
            "header": {
                "title": "chunk",
                "file_type": file_type,
                "total_bytes": total_bytes,
                "chunk_index": idx,
                "total_chunks": total_chunks
            },
            "payload": chunk
        }
        client.publish(FILE_TOPIC, json.dumps(message))

    # send final done message
    done_msg = {"header": {"title": "done"}}
    client.publish(FILE_TOPIC, json.dumps(done_msg))
    print("[injector] file fully sent!")

# CLI loop
while True:
    cmd = input("enter file to send (or 'exit'): ")
    if cmd == "exit":
        break
    if os.path.isfile(cmd):
        send_file(cmd)
    else:
        print("file not found")

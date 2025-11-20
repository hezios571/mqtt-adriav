import paho.mqtt.client as mqtt
import base64
import json

BROKER = "localhost"
PORT = 1883
FILE_TOPIC = "adriav/file/transfer"
ACK_TOPIC = "adriav/file/ack"

chunks = {}  # temporary storage

def on_message(client, userdata, msg):
    global chunks

    data = json.loads(msg.payload.decode())
    header = data.get("header", {})
    title = header.get("title")

    if title == "chunk":
        idx = header["chunk_index"]
        total = header["total_chunks"]
        file_type = header["file_type"]

        print(f"[controller] chunk {idx+1}/{total} received")

        # store chunk
        if "buffer" not in chunks:
            chunks["buffer"] = [""] * total
            chunks["file_type"] = file_type
            chunks["total_chunks"] = total

        chunks["buffer"][idx] = data["payload"]

        # send ack
        ack = {"header": {"title": "ack", "chunk": idx}}
        client.publish(ACK_TOPIC, json.dumps(ack))

    elif title == "done":
        print("[controller] last chunk received, assembling file...")

        full_b64 = "".join(chunks["buffer"])
        file_bytes = base64.b64decode(full_b64)

        output = "received_file." + chunks["file_type"]
        with open(output, "wb") as f:
            f.write(file_bytes)

        print(f"[controller] file saved as: {output}")
        chunks.clear()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(BROKER, PORT)
client.subscribe(FILE_TOPIC)

print("[controller] ready")
client.loop_forever()

import paho.mqtt.client as mqtt
import base64
import json
import os

BROKER = "localhost"
PORT = 1883

FILE_TOPIC_IN = "adriav/file/to_controller"
FILE_TOPIC_OUT = "adriav/file/to_injector"

CHAT_IN = "adriav/chat/injector_to_controller"
CHAT_OUT = "adriav/chat/controller_to_injector"

CHUNK_SIZE = 50000

recv = {
    "chunks": [],
    "expected": 0,
    "type": None
}

os.makedirs("controller", exist_ok=True)

def on_message(client, userdata, msg):
    print(f"\n[controller] MQTT message on {msg.topic}")
    payload = msg.payload.decode()

    try:
        obj = json.loads(payload)

        # chat
        if "chat" in obj:
            print(f"[controller] message: {obj['chat']}")
            return

        header = obj.get("header", {})
        title = header.get("title")

        if title == "chunk":
            idx = header["chunk_index"]
            total = header["total_chunks"]
            ftype = header["file_type"]

            if not recv["chunks"]:
                recv["chunks"] = [""] * total
                recv["expected"] = total
                recv["type"] = ftype

            recv["chunks"][idx] = obj["payload"]
            print(f"[controller] received chunk {idx+1}/{total}")

        elif title == "done":
            print("[controller] assembling file...")

            full = "".join(recv["chunks"])
            data = base64.b64decode(full)

            filename = f"received_by_controller.{recv['type']}"
            path = os.path.join("controller", filename)

            with open(path, "wb") as f:
                f.write(data)

            print(f"[controller] file saved to {path}")

            recv["chunks"] = []
            recv["expected"] = 0
            recv["type"] = None

    except Exception as e:
        print("Error:", e)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(BROKER, PORT)

client.subscribe(FILE_TOPIC_IN)
client.subscribe(CHAT_IN)
client.loop_start()

print("[controller] Ready. Commands:")
print("  msg <text>")
print("  file <path>")
print("  exit")

def send_file(path):
    with open(path, "rb") as f:
        content = f.read()

    ftype = path.split(".")[-1]
    b64 = base64.b64encode(content).decode()

    chunks = [b64[i:i+CHUNK_SIZE] for i in range(0, len(b64), CHUNK_SIZE)]
    total = len(chunks)

    for idx, chunk in enumerate(chunks):
        packet = {
            "header": {
                "title": "chunk",
                "file_type": ftype,
                "chunk_index": idx,
                "total_chunks": total
            },
            "payload": chunk
        }
        client.publish(FILE_TOPIC_OUT, json.dumps(packet))

    client.publish(FILE_TOPIC_OUT, json.dumps({"header": {"title": "done"}}))
    print("[controller] file sent")

while True:
    cmd = input("> ")

    if cmd == "exit":
        break

    if cmd.startswith("msg "):
        text = cmd[4:]
        client.publish(CHAT_OUT, json.dumps({"chat": text}))
        print("[controller] message sent")

    elif cmd.startswith("file "):
        path = cmd[5:]
        if os.path.isfile(path):
            send_file(path)
        else:
            print("File not found.")

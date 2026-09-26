// dweilrobo firmware v0.1: connect to the home hub, answer pings, run commands.
// Safety rule for all later versions: no hub message for LINK_TIMEOUT_MS -> safe state.
#include <Arduino.h>
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include "config.h"

static const char *FW_VERSION = "0.1.0";
static const uint32_t LINK_TIMEOUT_MS = 1000;
static const uint32_t TELEMETRY_MS = 1000;

WebSocketsClient ws;
uint32_t lastHubMsg = 0;
uint32_t lastTelemetry = 0;
bool linkUp = false;

void setLed(uint8_t r, uint8_t g, uint8_t b) { neopixelWrite(RGB_PIN, r, g, b); }

void safeState() {
  // v0.1 only has the LED; motors and pumps get switched off here later.
  setLed(8, 4, 0);  // dim orange = no link
}

void sendJson(JsonDocument &doc) {
  String out;
  serializeJson(doc, out);
  ws.sendTXT(out);
}

void sendHello() {
  JsonDocument doc;
  doc["type"] = "hello";
  doc["id"] = DEVICE_ID;
  doc["fw"] = FW_VERSION;
  JsonArray caps = doc["caps"].to<JsonArray>();
  caps.add("led");
  sendJson(doc);
}

void sendAck(uint32_t cmdId, bool ok, const char *error) {
  JsonDocument doc;
  doc["type"] = "ack";
  doc["cmd_id"] = cmdId;
  doc["ok"] = ok;
  if (error) doc["error"] = error; else doc["error"] = nullptr;
  sendJson(doc);
}

void handleMessage(const uint8_t *payload, size_t len) {
  JsonDocument msg;
  if (deserializeJson(msg, payload, len)) return;
  lastHubMsg = millis();
  const char *type = msg["type"] | "";

  if (strcmp(type, "ping") == 0) {
    JsonDocument pong;
    pong["type"] = "pong";
    pong["t"] = msg["t"];
    sendJson(pong);
  } else if (strcmp(type, "cmd") == 0) {
    uint32_t id = msg["cmd_id"] | 0;
    const char *name = msg["name"] | "";
    if (strcmp(name, "led") == 0) {
      setLed(msg["args"]["r"] | 0, msg["args"]["g"] | 0, msg["args"]["b"] | 0);
      sendAck(id, true, nullptr);
    } else {
      sendAck(id, false, "unknown command");
    }
  }
}

void onWsEvent(WStype_t type, uint8_t *payload, size_t length) {
  switch (type) {
    case WStype_CONNECTED:
      Serial.println("hub connected");
      sendHello();
      lastHubMsg = millis();
      linkUp = true;
      setLed(0, 8, 0);
      break;
    case WStype_DISCONNECTED:
      if (linkUp) Serial.println("hub disconnected");
      linkUp = false;
      safeState();
      break;
    case WStype_TEXT:
      handleMessage(payload, length);
      break;
    default:
      break;
  }
}

void setup() {
  Serial.begin(115200);
  safeState();
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);  // Wi-Fi power save adds 100+ ms latency spikes
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("wifi");
  while (WiFi.status() != WL_CONNECTED) { delay(250); Serial.print("."); }
  Serial.printf("\nip %s rssi %d\n", WiFi.localIP().toString().c_str(), WiFi.RSSI());

  String path = String("/ws/device?token=") + DEVICE_TOKEN;
  ws.begin(HUB_HOST, HUB_PORT, path.c_str());
  ws.onEvent(onWsEvent);
  ws.setReconnectInterval(1000);
}

void loop() {
  ws.loop();
  uint32_t now = millis();
  if (linkUp && now - lastHubMsg > LINK_TIMEOUT_MS) {
    Serial.println("link timeout -> safe state");
    linkUp = false;
    safeState();
    ws.disconnect();
  }
  if (linkUp && now - lastTelemetry > TELEMETRY_MS) {
    lastTelemetry = now;
    JsonDocument t;
    t["type"] = "telemetry";
    t["uptime_ms"] = now;
    t["rssi"] = WiFi.RSSI();
    t["free_heap"] = ESP.getFreeHeap();
    sendJson(t);
  }
}

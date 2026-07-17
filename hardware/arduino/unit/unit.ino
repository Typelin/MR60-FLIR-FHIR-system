#include <WiFi.h>
#include <WiFiUdp.h>
#include "Seeed_Arduino_mmWave.h"

// WiFi 熱點設定
const char* ssid = "Realme";
const char* password = "RealmeZZZ";

// 使用 UDP 廣播位址 (255.255.255.255)，ESP32 會自動將數據廣播至整個區域網路。
// 電腦端運行 Python 即可直接接收，無須手動輸入或修改電腦的實體 IP。
const char* udpAddress = "255.255.255.255";  
const int udpPort = 12345;

// 當前感測器識別碼 (第二台請改為 "MR60_2")
const char* sensorId = "MR60_1";

WiFiUDP udp;

#ifdef ESP32
#  include <HardwareSerial.h>
HardwareSerial mmWaveSerial(0);
#else
#  define mmWaveSerial Serial1
#endif

SEEED_MR60BHA2 mmWave;

float breath_rate = 0.0;
float heart_rate = 0.0;
float distance = 0.0;

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  Serial.print("正在連接 WiFi 熱點");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi 已連接，IP: " + WiFi.localIP().toString());

  // 初始化 UDP 連線
  udp.begin(udpPort);
  sendUdpInitMessage();

  mmWave.begin(&mmWaveSerial);
}

void loop() {
  // 讀取最新感測資料
  if (mmWave.update(100)) {
    bool gotBreath = mmWave.getBreathRate(breath_rate);
    bool gotHeart = mmWave.getHeartRate(heart_rate);
    bool gotDistance = mmWave.getDistance(distance);

    Serial.printf("[%s] breath_rate: %.2f bpm, heart_rate: %.2f bpm, distance: %.2f cm\n",
                  sensorId, breath_rate, heart_rate, distance);

    // 只要指標非零，就透過 UDP 發送資料
    if (breath_rate != 0 && heart_rate != 0 && distance != 0) {
      sendUdpData(breath_rate, heart_rate, distance);
    }
  }

  delay(1000);
}

void sendUdpInitMessage() {
  if (WiFi.status() == WL_CONNECTED) {
    String payload = String(sensorId) + ",init,ESP32已上線";
    
    udp.beginPacket(udpAddress, udpPort);
    udp.print(payload);
    udp.endPacket();
    
    Serial.println("已發送 UDP 初始化上線訊息 (廣播)");
  }
}

void sendUdpData(float breath, float heart, float dist) {
  if (WiFi.status() == WL_CONNECTED) {
    // 封裝格式: Sensor_ID,breath_rate,heart_rate,distance
    String payload = String(sensorId) + "," + 
                     String(breath, 2) + "," + 
                     String(heart, 2) + "," + 
                     String(dist, 2);
    
    udp.beginPacket(udpAddress, udpPort);
    udp.print(payload);
    udp.endPacket();
    
    Serial.println("已發送 UDP 觀測數據包 (廣播): " + payload);
  } else {
    Serial.println("WiFi 未連線，無法傳送 UDP 數據");
  }
}

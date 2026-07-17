#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include "Seeed_Arduino_mmWave.h"

// WiFi設定
const char* ssid = "Realme";
const char* password = "RealmeZZZ";

// PHP API URL
const char* serverUrl = "https://mr60.ngrok.pizza/sensor_to_db/connect.php";

WiFiClientSecure client;

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

  Serial.print("正在連接 WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi 已連接，IP: " + WiFi.localIP().toString());

  client.setInsecure();

  sendInitMessage();

  mmWave.begin(&mmWaveSerial);
}

void loop() {
  // 讀取最新感測資料
  if (mmWave.update(100)) {
    bool gotBreath = mmWave.getBreathRate(breath_rate);
    bool gotHeart = mmWave.getHeartRate(heart_rate);
    bool gotDistance = mmWave.getDistance(distance);

    Serial.printf("breath_rate: %.2f bpm, heart_rate: %.2f bpm, distance: %.2f cm\n",
                  breath_rate, heart_rate, distance);

    // 只要三個都非零，就送資料
    if (breath_rate != 0 && heart_rate != 0 && distance != 0) {
      sendData(breath_rate, heart_rate, distance);
    }
  }

  delay(1000);
}

void sendInitMessage() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    bool ok = http.begin(client, serverUrl);
    if (!ok) {
      Serial.println("http.begin() 初始化失敗！");
      return;
    }

    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    String postData = "type=init&message=ESP32已上線";

    int httpResponseCode = http.POST(postData);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("初始化訊息回應：" + response);
    } else {
      Serial.printf("初始化訊息傳送失敗，錯誤碼: %d, 錯誤: %s\n",
                    httpResponseCode, http.errorToString(httpResponseCode).c_str());
    }
    http.end();
  } else {
    Serial.println("WiFi 未連線，無法發送初始化訊息");
  }
}

void sendData(float breath, float heart, float dist) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    bool ok = http.begin(client, serverUrl);
    if (!ok) {
      Serial.println("http.begin() 初始化失敗！");
      return;
    }

    http.addHeader("Content-Type", "application/x-www-form-urlencoded");

    String postData = "type=data&breath=" + String(breath, 2) +
                      "&heart=" + String(heart, 2) +
                      "&distance=" + String(dist, 2);

    int httpResponseCode = http.POST(postData);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("HTTP 回應：" + response);
    } else {
      Serial.printf("HTTP 傳送失敗，錯誤碼: %d, 錯誤: %s\n",
                    httpResponseCode, http.errorToString(httpResponseCode).c_str());
    }
    http.end();
  } else {
    Serial.println("WiFi 未連線，無法傳送資料");
  }
}

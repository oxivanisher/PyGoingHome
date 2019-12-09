#include <Wire.h>
#include <ESP8266WiFi.h>
#include <LiquidCrystal_I2C.h>
#include <ArduinoJson.h>
#include <stdio.h>

// Read settings from config.h
#include "config.h"

const char* ssid     = WIFI_SSID;
const char* password = WIFI_PASSWORD;
const char *host     = HOST;

LiquidCrystal_I2C lcd(0x3F, 2, 1, 0, 4, 5, 6, 7, 3, POSITIVE);  // Set the LCD I2C address

void setup()  
{
  Serial.begin(9600);
  int cursorPosition=0;

  lcd.begin(16,2); 
  lcd.setCursor(0,0);
  lcd.print("Connecting ....");

  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    lcd.setCursor(cursorPosition,1); 
    lcd.print(".");
    cursorPosition++;
  }
  
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("Connected!");
  delay(1000);
}

void loop() 
{
  String goingHome = getGoingHome();
  String ghheader = getValue(goingHome, '|', 0);
  String ghdelay = getValue(goingHome, '|', 1);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(ghheader);
  lcd.setCursor(0, 1);
  lcd.print(ghdelay);

  delay(30000);
}

String getValue(String data, char separator, int index)
{
    int found = 0;
    int strIndex[] = { 0, -1 };
    int maxIndex = data.length() - 1;

    for (int i = 0; i <= maxIndex && found <= index; i++) {
        if (data.charAt(i) == separator || i == maxIndex) {
            found++;
            strIndex[0] = strIndex[1] + 1;
            strIndex[1] = (i == maxIndex) ? i+1 : i;
        }
    }
    return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}

String getGoingHome()
{
  WiFiClientSecure client;
  Serial.print("connecting to "); Serial.println(host);
  if (!client.connect(host, PORT)) {
    Serial.println("connection failed");
    return "false";
  }
  String cmd = String("GET / HTTP/1.1\r\nHost: ") + host + "\r\nUser-Agent: ESP8266/1.1\r\nConnection: close\r\n\r\n";
  client.print(cmd);

  int repeatCounter = 10;
  while (!client.available() && repeatCounter--) {
    delay(500);
  }
  String line,buf="";
  int startJson=0;
  
  while (client.connected() && client.available()) {
    line = client.readStringUntil('\n');
    if(line[0]=='{') startJson=1;
    if(startJson) 
    {
      for(int i=0;i<line.length();i++)
        if(line[i]=='[' || line[i]==']') line[i]=' ';
      buf+=line+"\n";
    }
  }
  client.stop();

  DynamicJsonBuffer jsonBuf;
  JsonObject &root = jsonBuf.parseObject(buf);
  if (!root.success()) {
    Serial.println("parseObject() failed");
    delay(10);
    return "false";
  }
  
  String goingHome;
  //goingHome.concat(root["header"]);
  goingHome.concat("|");
  //subscribers.concat(root["delay"]);
  Serial.println(goingHome);
  return goingHome;
}

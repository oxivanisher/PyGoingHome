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

int status_count = -1;

LiquidCrystal_I2C lcd(0x3F, 2, 1, 0, 4, 5, 6, 7, 3, POSITIVE);  // Set the LCD I2C address

void setup()  
{
  Serial.begin(115200);
  int cursorPosition=0;

  lcd.begin(16,2); 
  displayOnLcd("Connecting WiFi:");
  lcd.setCursor(0,0);

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
  delay(6000);
}

void loop() 
{
  displayOnLcd(getGoingHome());
  delay(10000);
}

void displayOnLcd(String text)
{
  status_count++;

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(text.substring(0,15));
  lcd.setCursor(0, 1);
  lcd.print(text.substring(16,30));

  lcd.setCursor(15, 1);
  switch (status_count) {
    case 1:
      lcd.print('.');
      break;
    case 2:
      lcd.print('o');
      break;
    case 3:
      lcd.print('O');
      break;
    default:
      lcd.print('o');
      status_count = -1;
      break;
  }
}

String getGoingHome()
{
  WiFiClientSecure client;
  client.setInsecure();
  // the certificate is ignored due to several reasons:
  // * since we do not sync local time to a ntp, most certs would be invalid anyways
  // * we want to support also self signed certificates
  // * we do not transfer any sensible data (only reading)
  Serial.print("try to connect to: "); Serial.print(host); Serial.print(":"); Serial.println(PORT);
  int conn_result = client.connect(host, PORT);
  if (! conn_result) {
    Serial.print("connection failed with return: ");
    Serial.println(conn_result);
    char ret[32];
    sprintf(ret, "Unable to connect to server %i", conn_result);
    return ret;
  }
  String cmd = String("GET / HTTP/1.1\r\nHost: ") + host + "\r\nUser-Agent: ESP8266/1.1\r\nConnection: close\r\n\r\n";
  client.print(cmd);

  int repeatCounter = 10;
  while (!client.available() && repeatCounter--) {
    delay(500);
  }
  String line,json="";
  int startJson=0;
  
  while (client.connected() && client.available()) {
    line = client.readStringUntil('\n');
    if(line[0]=='{') startJson=1;
    if(startJson) 
    {
      for(int i=0;i<line.length();i++)
        if(line[i]=='[' || line[i]==']') line[i]=' ';
      json+=line+"\n";
    }
  }
  client.stop();

  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, json);
  if (error)
    return "Unable to deserialize Json";

  String goingHome = doc["short"];
  Serial.print("RCV: ");
  Serial.println(goingHome);
  return goingHome;
}

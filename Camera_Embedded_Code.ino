   #include <MQTT.h>
   #include <MQTTClient.h>
   #include <WiFiClientSecure.h>
   #include <JPEGDecoder.h>
   #include <WiFi.h>
   #include "esp_camera.h"
   #include "secret.h"//this secret file contains our AWS mqtt key and Wifi information
   #include <stdlib.h>
   #include <string>
// WARNING!!! PSRAM IC required for UXGA resolution and high JPEG quality
//            Ensure ESP32 Wrover Module or other board with PSRAM is selected
//            Partial images will be transmitted if image exceeds buffer size
//
//            You must select partition scheme from the board menu that has at least 3MB APP space.
//            Face Recognition is DISABLED for ESP32 and ESP32-S2, because it takes up from 15 
//            seconds to process single frame. Face Detection is ENABLED if PSRAM is enabled as well



// ===========================
#define PWDN_GPIO_NUM    -1
#define RESET_GPIO_NUM   -1
#define XCLK_GPIO_NUM    21
#define SIOD_GPIO_NUM    26
#define SIOC_GPIO_NUM    27

#define Y9_GPIO_NUM      35
#define Y8_GPIO_NUM      34
#define Y7_GPIO_NUM      39
#define Y6_GPIO_NUM      36
#define Y5_GPIO_NUM      19
#define Y4_GPIO_NUM      18
#define Y3_GPIO_NUM       5
#define Y2_GPIO_NUM       4
#define VSYNC_GPIO_NUM   25
#define HREF_GPIO_NUM    23
#define PCLK_GPIO_NUM    22


int i=0;
const int bufferSize=1024*30;
int frameRate=30;
double frameTime=1000/frameRate;
//JPEGDecoder decoder;
WiFiClientSecure espClient=WiFiClientSecure();
MQTTClient client(bufferSize);
sensor_t* sensor;
void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.println("\n\n=====================");
  Serial.println("Connecting to Wi-Fi");
  Serial.println("=====================\n\n");

  while (WiFi.status() != WL_CONNECTED){
    delay(500);
    Serial.print(".");
  }

  // Configure WiFiClientSecure to use the AWS IoT device credentials
  espClient.setCACert(AWS_CERT_CA);
  espClient.setCertificate(AWS_CERT_CRT);
  espClient.setPrivateKey(AWS_CERT_PRIVATE);
}

void connectMQTT() {
  client.begin(AWS_IOT_ENDPOINT, 8883, espClient);
  client.setCleanSession(true);  
  while (!client.connect(THINGNAME)) {
    Serial.print(".");
    delay(100);
  }

  if(!client.connected()){
    Serial.println("Mqtt Timeout!");
    ESP.restart();
    return;
  }
  Serial.println("Mqtt connected!");
}

 void setupCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA; // 640x480
  config.jpeg_quality = 15;
  config.fb_count = 2;

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    ESP.restart();
    return;
  }
   }


void publishImage() {
  camera_fb_t * fb = esp_camera_fb_get();
  if(fb != NULL && fb->format == PIXFORMAT_JPEG && fb->len < bufferSize){
    Serial.print("Image Length: ");
    Serial.print(fb->len);
    Serial.print("\t Publish Image: ");
    bool result = client.publish(THINGNAME, (const char*)fb->buf, fb->len);
    Serial.println(result);

    if(!result){
      ESP.restart();
    }
  }
  esp_camera_fb_return(fb);
  delay(frameTime);
      
  }
 void messageReceived(String &topic, String &payload) {
  Serial.print("Message received on topic: ");
  Serial.println(topic);
  Serial.print("Message: ");
  Serial.println(payload);
  if (topic==CONFIG_SIZE){
      if(payload=="f:0"){sensor->set_framesize(sensor,FRAMESIZE_QVGA); Serial.println("FRAMESIZE_QVGA");}
      else if (payload=="f:1"){sensor->set_framesize(sensor,FRAMESIZE_CIF);}
      else if (payload=="f:2"){sensor->set_framesize(sensor,FRAMESIZE_VGA);}
      else if (payload=="f:3"){sensor->set_framesize(sensor,FRAMESIZE_SVGA);}
    }
  if(topic==CONFIG_FRAME){
      frameRate=atoi(payload.c_str());
      frameTime=1000/frameRate;
    }
  if(topic==CONFIG_BRIGHTNESS){
      sensor->set_brightness(sensor,atof(payload.c_str()));
    }
  if(topic==CONFIG_CONTRAST){
      sensor->set_contrast(sensor,atof(payload.c_str()));
    }
  if(topic==CONFIG_SATURATION){
      sensor->set_saturation(sensor,atof(payload.c_str()));
    }   
  if(topic==CONFIG_EFFECT){
      sensor->set_special_effect(sensor,atoi(payload.c_str()));
      Serial.println(atoi(payload.c_str()));
    }  
  if(topic==CONFIG_WHITEBAL){
      sensor->set_whitebal(sensor,atoi(payload.c_str()));
    }  
  if(topic==CONFIG_AWB){
      sensor->set_awb_gain(sensor,atoi(payload.c_str()));
    }    
  if(topic==CONFIG_WB){
      sensor->set_wb_mode(sensor,atoi(payload.c_str()));
    }
  if(topic==CONFIG_EXPOSURE){
      sensor->set_exposure_ctrl(sensor,atoi(payload.c_str()));
    }               
}

void setup() {
  Serial.begin(115200);
//  Serial.setDebugOutput(true);
  setupCamera();
  connectWiFi();
  connectMQTT();
  client.subscribe(CONFIG_SIZE);
  client.subscribe(CONFIG_FRAME);
  client.subscribe(CONFIG_BRIGHTNESS);
  client.subscribe(CONFIG_CONTRAST);
  client.subscribe(CONFIG_SATURATION);
  client.subscribe(CONFIG_EFFECT);
  client.subscribe(CONFIG_WHITEBAL);
  client.subscribe(CONFIG_AWB);
  client.subscribe(CONFIG_WB);
  client.subscribe(CONFIG_EXPOSURE);
  client.onMessage(messageReceived);
  sensor = esp_camera_sensor_get();
//  publishImage();
}

void loop() {
  client.loop();
  //delay(10); 
  if(client.connected()) publishImage();
 // Adjust the delay as needed
}

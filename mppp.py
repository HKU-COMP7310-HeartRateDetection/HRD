from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import base64
from PIL import Image
import io

# AWS MQTT连接参数
ENDPOINT = "a12ej9mk5jajtb-ats.iot.ap-east-1.amazonaws.com"
CLIENT_ID = "Kzmlaptop"
PATH_TO_CERTIFICATE = "cert.crt"
PATH_TO_PRIVATE_KEY = "private.key"
PATH_TO_AMAZON_ROOT_CA_1 = "rootCA.crt"
TOPIC = "HEARTRATE"

# 创建MQTT客户端
mqtt_client = AWSIoTMQTTClient(CLIENT_ID)

# 配置TLS证书和连接参数
mqtt_client.configureEndpoint(ENDPOINT, 8883)
mqtt_client.configureCredentials(PATH_TO_AMAZON_ROOT_CA_1, PATH_TO_PRIVATE_KEY, PATH_TO_CERTIFICATE)

# 连接到AWS IoT Core
mqtt_client.connect()

# MQTT消息处理函数
def on_message(client, userdata, message):
    # 解码Base64编码的图片数据
    base64_data = message.payload
    image_data = base64.b64decode(base64_data)

    # 创建图像对象
    image = Image.open(io.BytesIO(image_data))

    # 显示图像
    image.show()

# 订阅MQTT主题
mqtt_client.subscribe(TOPIC, 1, on_message)

# 保持连接
while True:
    pass

# 断开连接
mqtt_client.disconnect()
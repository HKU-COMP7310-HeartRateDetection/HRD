import io
import queue
import traceback
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT
import PySimpleGUI as sg
import matplotlib.pyplot as plt
import matplotlib
from PIL import Image
import numpy as np
import json
import time
import base64
import threading
from PIL import Image


matplotlib.use('TkAgg')
class Application:
    def __init__(self):
        self.myAWSIoTMQTTClient = None
        self.gui_queue = queue.Queue()
        self.hr_queue = queue.Queue()
        self.hr_list = []
        self.hr_lg_queue = queue.Queue()# Line Graph
        middle_font = ('Times', 14)
        context_font = ('Arial', 12)
        self.plot_timer = None
        self.subscribe_hr = True
        # self.current_fr = 30
        self.global_brightness = 0.0
        self.plot_lock = threading.Lock()
        sg.theme('LightBrown3')
        
        # Column 1: panel 1
        col1 = [[sg.Column([
            [sg.Frame('MQTT Panel 1', [[sg.Column([
                [sg.Text('Client Id:', font=middle_font)],
                [sg.Input('Sheer_Heart_Attack', key='_CLIENTID_IN_', size=(17, 1), font=('Arial', 12)),
                 sg.Button('Connect', key='_CONNECT_BTN_', font=context_font)],
                [sg.Text('')],
                # Add text boxes and buttons for user input
                [sg.Text('Frame Size', font=middle_font)],
                [sg.Combo(['FRAMESIZE_QVGA (320 x 240)', 'FRAMESIZE_CIF (352 x 288)', 'FRAMESIZE_VGA (640 x 480)', 'FRAMESIZE_SVGA (800 x 600)'],
                default_value='FRAMESIZE_QVGA (320 x 240)', key='_INPUT1_', font=('Arial', 11))],
                [sg.Button('Set Frame Size', key='_SUBMIT1_', font=context_font)],
                [sg.Text('')],
                [sg.Text('Frame Rate', font=middle_font)],
                [sg.Combo([60,30, 20, 10],
                default_value=30, key='_INPUT2_'), sg.Button('Set Frame Rate', key='_SUBMIT2_', font=context_font)],
                [sg.Text('')],
                [sg.Text('Notes:', font=middle_font)],
                [sg.Multiline(key='_NOTES_', autoscroll=True, size=(23, 15), font=context_font, )],
            ], size=(250, 640), pad=(0, 0))]], font=middle_font)], ], pad=(0, 0), element_justification='c')]]

        # Column 2: panel 2
        col2 = [[sg.Column([
            [sg.Frame('MQTT Panel 2', [[sg.Column([
                # Add text boxes and buttons for user input
                # Brightness
                [sg.Text('Brightness', font=middle_font)],
                [sg.Slider(range=(-2.0, 2.0), default_value=0.0, orientation='h', resolution=0.01, key='_INPUT3_', enable_events=True)],
                # [sg.Button('Submit', key='_SUBMIT3_', font=('Arial', 12))],
                [sg.Text('')],
                # Contrast
                [sg.Text('Contrast', font=middle_font)],
                [sg.Slider(range=(-2.0, 2.0), default_value=0.0, orientation='h', resolution=0.01, key='_INPUT4_', enable_events=True)],
                # [sg.Button('Submit', key='_SUBMIT4_', font=context_font)],
                [sg.Text('')],
                # _saturation
                [sg.Text('Saturation', font=middle_font)],
                [sg.Slider(range=(-2.0, 2.0), default_value=0.0, orientation='h', resolution=0.01, key='_INPUT5_', enable_events=True)],
                # [sg.Button('Submit', key='_SUBMIT5_', font=context_font)],
                [sg.Text('')],
                # special_effect
                [sg.Text('Special Effects', font=middle_font)],
                [sg.Combo(['No Effect', 'Negative', 'Grayscale', 'Red Tint', 'Green Tint', 'Blue Tint', 'Sepia'],
                default_value='No Effect', key='_INPUT6_'), sg.Text('  '),sg.Button('Set Special Effects', key='_SUBMIT6_', font=context_font)],
                [sg.Text('')],
                # whitebal
                [sg.Text('White Balance', font=middle_font), sg.Radio('disable', "RADIO1",key = '_WHIDIS_', enable_events=True), sg.Radio('enable', "RADIO1", key = '_WHIENA_', default=True, enable_events=True)],
                # [sg.Button('Submit', key='_SUBMIT7_', font=context_font)],
                [sg.Text('')],
                # wb_mode
                [sg.Text('White Blanace Mode', font=middle_font), 
                    sg.Combo(['Auto', 'Sunny', 'Cloudy', 'Office', 'Home'], 
                                default_value='Auto', key='_INPUT8_'),
                    sg.Button('Set Mode', key='_SUBMIT8_', font=context_font)
                ],
                [sg.Text('')],
                # exposure control
                [sg.Text('Exposure Control', font=middle_font), sg.Radio('disable', "RADIO2",key = '_EXPDIS_', enable_events=True), sg.Radio('enable', "RADIO2", key = '_EXPENA_', default=True, enable_events=True)],
                # [sg.Button('Submit', key='_SUBMIT9_', font=context_font)],
                [sg.Text('')],
                [sg.Text('Heart Rate Plot'), sg.Checkbox('ON', key='_TOGGLE_', default=True, enable_events=True)]
            ], size=(350, 640), pad=(0, 0))]], font=middle_font)], ], pad=(0, 0), element_justification='c')]]
        
        # Column 3: 
        col3 = [[sg.Column([
            # First frame: Camera from mqtt
                [sg.Frame('CAMERA', [
                [sg.Image(key='_COMP7310_', size=(480, 320))],
                ], font=middle_font)],
                # [sg.Frame('Heart Rate', [
                # [sg.Text(key='_HEARTRATE_')],
                # ], font=middle_font)],
            # Second frame: Heart rate from backend
                [sg.Frame('Heart Rate Line Graph',[
                [sg.Image(key='_HEARTRATE_', size = (480, 320))],
                ], font=middle_font)]
                ], pad=(0, 0), element_justification='c')] 
                ]
        layout = [[
            sg.Column(col1), sg.Column(col2), sg.Column(col3)
        ]]

        self.window = sg.Window('Python MQTT Client - AWS IoT - COMP7310', layout)
        while True:
            event, values = self.window.Read(timeout=5)
            if event is None or event == 'Exit':
                break
            # Get connection
            if event == '_CONNECT_BTN_':
                if self.window[event].get_text() == 'Connect':
                    if len(self.window['_CLIENTID_IN_'].get()) == 0:
                        self.popup_dialog('Client Id is empty', 'Error', context_font)
                    else:
                        self.window['_CONNECT_BTN_'].update('Disconnect')
                        self.aws_connect(self.window['_CLIENTID_IN_'].get())

                else:
                    self.window['_CONNECT_BTN_'].update('Connect')
                    self.aws_disconnect()
            # Frame size
            if event == '_SUBMIT1_':
                if self.window['_CONNECT_BTN_'].get_text() == 'Connect':
                     sg.popup('Please Connect First!')
                else:
                    input1_value = self.window['_INPUT1_'].get()
                    options = ['FRAMESIZE_QVGA (320 x 240)', 'FRAMESIZE_CIF (352 x 288)', 'FRAMESIZE_VGA (640 x 480)', 'FRAMESIZE_SVGA (800 x 600)']
                    index = options.index(input1_value)
                    self.publish_message('config_size', 'f:'+str(index))
                    self.window['_NOTES_'].print('Set frame size: ' + str(input1_value))
            # resolution
            if event == '_SUBMIT2_':
                if self.window['_CONNECT_BTN_'].get_text() == 'Connect':
                     sg.popup('Please Connect First!')
                else:
                    input2_value = self.window['_INPUT2_'].get()
                    if input2_value:
                        self.current_fr = input2_value
                        self.publish_message('config_frame', str(input2_value))
                        self.window['_NOTES_'].print('Set rating frame: ' + str(input2_value))
            # brightness
            # if event == '_SUBMIT3_':
            if event == '_INPUT3_':
                if self.window['_CONNECT_BTN_'].get_text() == 'Connect':
                     sg.popup('Please Connect First!')
                else:
                    slider_value = values['_INPUT3_']
                    self.publish_message('config_brightness', slider_value)
                    self.window['_NOTES_'].print('Set brightness ' + str(slider_value))  
            # contrast
            # if event == '_SUBMIT4_':
            if event == '_INPUT4_':
                if self.window['_CONNECT_BTN_'].get_text() == 'Connect':
                     sg.popup('Please Connect First!')
                else:
                    slider_value = values['_INPUT4_']
                    self.publish_message('config_contrast', slider_value)
                    self.window['_NOTES_'].print('Set contrast ' + str(slider_value))  
            # saturation
            # if event == '_SUBMIT5_':
            if event == '_INPUT5_':
                if self.window['_CONNECT_BTN_'].get_text() == 'Connect':
                     sg.popup('Please Connect First!')
                else:
                    slider_value = values['_INPUT5_']
                    self.publish_message('config_saturation', slider_value)     
                    self.window['_NOTES_'].print('Set saturation ' + str(slider_value))  
            # special effects:
            if event == '_SUBMIT6_':
                if self.window['_CONNECT_BTN_'].get_text() == 'Connect':
                     sg.popup('Please Connect First!')
                else:
                    input6_value = self.window['_INPUT6_'].get()
                    options = ['No Effect', 'Negative', 'Grayscale', 'Red Tint', 'Green Tint', 'Blue Tint', 'Sepia']
                    index = options.index(input6_value)
                    self.publish_message('config_effect', index)
                    self.window['_NOTES_'].print('Set effect ' + str(input6_value)) 
            # whitebal
            # if event == '_SUBMIT7_':
            if event == '_WHIDIS_' or event == '_WHIENA_':
                msg = 0
                value = 'enable'
                if self.window['_CONNECT_BTN_'].get_text() == 'Connect':
                     sg.popup('Please Connect First!')
                else:
                    if values['_WHIDIS_']:
                        msg = 0
                        value = 'disable'
                    elif values['_WHIENA_']:
                        msg = 1
                    self.publish_message('config_whitebal', msg)
                    self.window['_NOTES_'].print('Set white balance ' + value) 
            # whitebal mode
            if event == '_SUBMIT8_':
                if self.window['_CONNECT_BTN_'].get_text() == 'Connect':
                     sg.popup('Please Connect First!')
                else:
                    input8_value = self.window['_INPUT8_'].get()
                    options = ['Auto', 'Sunny', 'Cloudy', 'Office', 'Home']
                    index = options.index(input8_value)
                    self.publish_message('config_wb', index)
                    self.window['_NOTES_'].print('Set effect ' + str(input8_value)) 
            # exposure control
            # if event == '_SUBMIT9_':
            if event == '_EXPDIS_' or event == '_EXPENA_':
                msg = 0
                value = 'enable'
                if self.window['_CONNECT_BTN_'].get_text() == 'Connect':
                     sg.popup('Please Connect First!')
                else:
                    if values['_EXPDIS_']:
                        msg = 0
                        value = 'disable'
                    elif values['_EXPENA_']:
                        msg = 1
                    self.publish_message('config_exposure', msg)
                    self.window['_NOTES_'].print('Set exposure ' + value) 
            
            # Switch of hr plot
            if event == '_TOGGLE_':
                self.toggle_subscription()
                self.window['_NOTES_'].print('Switch toggle status ' + str(values['_TOGGLE_'])) 

            # Send camera data to gui queue
            try:
                message = self.gui_queue.get_nowait()
            except queue.Empty:
                message = None
            if message is not None:
                _target_ui = message.get("Target_UI")
                _image = message.get("Image")
                self.window[_target_ui].update(data=_image)
            
            # Send heart rate data to hr queue
            try:
                message = self.hr_queue.get_nowait()
            except queue.Empty:
                message = None
            if message is not None:
                _target_ui = message.get("Target_UI")
                _image = message.get("Image")
                self.window[_target_ui].update(data=_image)
            
            # Privious codes: Take the heart rate from mqtt server and update the heart rate text
            # try: message = self.hr_queue.get_nowait()
            # except queue.Empty:
            #     message = None
            # if message is not None:
            #     _heartrate = message.get("HEARTRATE")
            #     _text = message.get("Text")
            #     if len(self.hr_list)<self.current_fr*60:
            #         self.hr_list.append(_text)
            #     else:
            #         self.hr_list = self.hr_list[1:]  # 删除第一个元素
            #         self.hr_list.append(_text)  # 在末尾添加新元素
            #     self.window[_heartrate].update(_text)
                    
            # Previous codes: Take the heart rate graph from server and plot
            # try:
            #     message = self.hr_lg_queue.get_nowait()
            # except queue.Empty:
            #     message = None
            # if message is not None:
            #     _target_ui = message.get("Target_UI")
            #     _image = message.get("Image")
            #     self.window[_target_ui].update(data=_image)

            # self.plot_hr_graph()
        # Don't delete this line
        self.window.Close()

# Aws connect
    def aws_connect(self, client_id):
        ENDPOINT = "a12ej9mk5jajtb-ats.iot.ap-east-1.amazonaws.com"
        PATH_TO_CERT = "cert.crt"
        PATH_TO_KEY = "private.key"
        PATH_TO_ROOT = "rootCA.crt"

        self.myAWSIoTMQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient(client_id)
        self.myAWSIoTMQTTClient.configureEndpoint(ENDPOINT, 8883)
        self.myAWSIoTMQTTClient.configureCredentials(PATH_TO_ROOT, PATH_TO_KEY, PATH_TO_CERT)

        try:
            if self.myAWSIoTMQTTClient.connect():
                self.add_note('[MQTT] Connected')
                self.mqtt_subscribe('COMP7310')
                self.mqtt_subscribe_hr('HEARTRATE')
                self.subscribe_hr = True
            else:
                self.add_note('[MQTT] Cannot Access AWS IOT')
        except Exception as e:
            tb = traceback.format_exc()
            sg.Print(f'An error happened.  Here is the info:', e, tb)

# Aws disconnect
    def aws_disconnect(self):
        if self.myAWSIoTMQTTClient is not None:
            self.myAWSIoTMQTTClient.disconnect()
            self.add_note('[MQTT] Successfully Disconnected!')

# Subscribe binary stuff from mqtt server, then, put them into gui queue
    def mqtt_subscribe(self, topic):
        if self.myAWSIoTMQTTClient.subscribe(topic, 0, lambda client, userdata, message: {

            self.gui_queue.put({"Target_UI": "_{}_".format(str(message.topic).upper()),
                                "Image": self.byte_image_to_png(message)})
        }):
            self.add_note('[MQTT] Topic: {}\n-> Subscribed\n'.format(topic))
        else:
            self.add_note('[MQTT] Cannot subscribe\nthis Topic: {}'.format(topic))

# Another subcribe function which decodes received data with byte64
    def mqtt_subscribe_hr(self, topic):
        if self.myAWSIoTMQTTClient.subscribe(topic, 0, lambda client, userdata, message: {

            self.gui_queue.put({"Target_UI": "_{}_".format(str(message.topic).upper()),
                                "Image": self.base64_to_png(message)})
        }):
            self.add_note('[MQTT] Topic: {}\n-> Subscribed\n'.format(topic))
        else:
            self.add_note('[MQTT] Cannot subscribe\nthis Topic: {}'.format(topic))

# Subscribe string data from server, and update the text content. No longer in use
    def mqtt_subscribe_String(self, topic):
        if self.myAWSIoTMQTTClient.subscribe(topic, 0, lambda client, userdata, message: {

            self.gui_queue.put({"Target_UI": "_{}_".format(str(message.topic).upper()),
                                "Image": self.byte_image_to_png(message)})
        }):
            self.add_note('[MQTT] Topic: {}\n-> Subscribed\n'.format(topic))
        else:
            self.add_note('[MQTT] Cannot subscribe\nthis Topic: {}'.format(topic))


# Add note to notes
    def add_note(self, note):
        note_history = self.window['_NOTES_'].get()
        self.window['_NOTES_'].update(note_history + note if len(note_history) > 1 else note)

# Convert byte to png file
    def byte_image_to_png(self, message):
        bytes_image = io.BytesIO(message.payload)
        picture = Image.open(bytes_image)

        im_bytes = io.BytesIO()
        picture.save(im_bytes, format="PNG")
        return im_bytes.getvalue()

# Convert base64 file to png
    def base64_to_png(self, message):
        base64_image = message.payload.decode('utf-8')
        image_data = base64.b64decode(base64_image)

        # Return the image data as bytes
        return image_data

# Pop up a window
    def popup_dialog(self, contents, title, font):
        sg.Popup(contents, title=title, keep_on_top=True, font=font)

# Publish message to TOPIC
    def publish_message(self, TOPIC, message):
        self.myAWSIoTMQTTClient.publish(TOPIC, str(message), 1) 
        # self.window['_NOTES_'].print("Published to"+str(TOPIC))
        # self.window['_NOTES_'].print("Published: '" + str(message) + "' to the topic: " + str(TOPIC))
# Switch status of subscription
    def toggle_subscription(self):
        if self.subscribe_hr:
            self.myAWSIoTMQTTClient.unsubscribe('HEARTRATE')
            self.subscribe_hr = False
            self.add_note('[MQTT] Unsubscribed from HEARTRATE topic')
        else:
            self.mqtt_subscribe_hr('HEARTRATE')
            self.subscribe_hr = True
            self.add_note('[MQTT] Subscribed to HEARTRATE topic')

# Plot heart rate graph(line graph). No longer in use
    def plot_hr_graph(self):
        if self.window['_CONNECT_BTN_'].get_text() != 'Connect':
            self.update_plot(self.current_fr)
            image = Image.open('./heart_rate_line_graph/heart_rate_plot.png')
            image.thumbnail((480, 320))
            bytes_io = io.BytesIO()
            image.save(bytes_io, format='PNG')
            self.hr_lg_queue.put({"Target_UI": '_HRLG_', "Image": bytes_io.getvalue()})

# Draw the line graph. Update the plot of line graph. No longer in use
    def update_plot(self, frame_rate):
        frame_interval = int(frame_rate)  # 每秒取一个点，取整数部分作为帧间隔 30点（帧）分一次秒

        hr_data = self.hr_list  # 获取要绘制的心率数据

        num_points = len(hr_data)  # 数据点的数量
        # print(num_points)
        num_seconds = num_points // frame_interval  # 根据帧间隔计算秒数 1800帧/30 = 60秒

        time_values = np.arange(0, num_seconds) * frame_interval
        hr_values = hr_data[:num_seconds * frame_interval: frame_interval]  # 根据帧间隔获取相应的心率值

        plt.plot(time_values, hr_values)
        plt.xlabel('Time (seconds)')  # 更新横轴标签为秒
        plt.ylabel('Heart Rate')
        plt.title('Heart Rate Variation')
        plt.grid(True)
        # plt.tight_layout()
        plt.savefig('./heart_rate_line_graph/heart_rate_plot.png')

if __name__ == '__main__':
    Application()

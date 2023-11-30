import io
import queue
import traceback
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT
import PySimpleGUI as sg
from PIL import Image
import json

class Application:
    def __init__(self):
        self.myAWSIoTMQTTClient = None
        self.gui_queue = queue.Queue()

        middle_font = ('Consolas', 14)
        context_font = ('Consolas', 12)
        sg.theme('DarkGrey14')

        col1 = [[sg.Column([
            [sg.Frame('MQTT Panel 1', [[sg.Column([
                [sg.Text('Client Id:', font=middle_font)],
                [sg.Input('Python_Client', key='_CLIENTID_IN_', size=(15, 1), font=context_font),
                 sg.Button('Connect', key='_CONNECT_BTN_', font=context_font)],
                # Add text boxes and buttons for user input
                [sg.Text('Frame Size', font=middle_font)],
                [sg.Combo(['FRAMESIZE_QVGA (320 x 240)', 'FRAMESIZE_CIF (352 x 288)', 'FRAMESIZE_VGA (640 x 480)', 'FRAMESIZE_SVGA (800 x 600)'],
                default_value='FRAMESIZE_QVGA (320 x 240)', key='_INPUT1_')],
                [sg.Button('Submit', key='_SUBMIT1_', font=context_font)],
                [sg.Text('Sampling rate', font=middle_font)],
                [sg.Combo([60,30, 20, 10],
                default_value=30, key='_INPUT2_')],
                [sg.Button('Submit', key='_SUBMIT2_', font=context_font)],
                [sg.Text('Brightness', font=middle_font)],
                [sg.Slider(range=(-2.0, 2.0), default_value=0.0, orientation='h', resolution=0.01, key='_INPUT3_')],
                [sg.Button('Submit', key='_SUBMIT3_', font=('Arial', 12))],
                [sg.Text('Notes:', font=middle_font)],
                [sg.Multiline(key='_NOTES_', autoscroll=True, size=(20, 10), font=context_font, )],
            ], size=(250, 640), pad=(0, 0))]], font=middle_font)], ], pad=(0, 0), element_justification='c')]]

        col2 = [[sg.Column([
            [sg.Frame('MQTT Panel 2', [[sg.Column([
                # Add text boxes and buttons for user input
                # Contrast
                [sg.Text('Contrast', font=middle_font)],
                [sg.Slider(range=(-2.0, 2.0), default_value=0.0, orientation='h', resolution=0.01, key='_INPUT4_')],
                [sg.Button('Submit', key='_SUBMIT4_', font=context_font)],
                # _saturation
                [sg.Text('Saturation', font=middle_font)],
                [sg.Slider(range=(-2.0, 2.0), default_value=0.0, orientation='h', resolution=0.01, key='_INPUT5_')],
                [sg.Button('Submit', key='_SUBMIT5_', font=context_font)],
                # special_effect
                [sg.Text('Special effects', font=middle_font)],
                [sg.Combo(['No Effect', 'Negative', 'Grayscale', 'Red Tint', 'Green Tint', 'Blue Tint', 'Sepia'],
                default_value='Sepia', key='_INPUT6_')],
                [sg.Button('Submit', key='_SUBMIT6_', font=context_font)],
                # whitebal
                [sg.Text('whitebalance', font=middle_font), sg.Radio('disable', "RADIO1",key = '_WHIDIS_'), sg.Radio('enable', "RADIO1", key = '_WHIENA_', default=True)],
                [sg.Button('Submit', key='_SUBMIT7_', font=context_font)],
                # wb_mode
                [sg.Text('white blanace mode', font=middle_font)],
                [sg.Combo(['Auto', 'Sunny', 'Cloudy', 'Office', 'Home'],
                default_value='Auto', key='_INPUT8_')],
                [sg.Button('Submit', key='_SUBMIT8_', font=context_font)],
                # exposure control
                [sg.Text('Exposure Control', font=middle_font), sg.Radio('disable', "RADIO2",key = '_EXPDIS_'), sg.Radio('enable', "RADIO2", key = '_EXPENA_', default=True)],
                [sg.Button('Submit', key='_SUBMIT9_', font=context_font)],
            ], size=(350, 640), pad=(0, 0))]], font=middle_font)], ], pad=(0, 0), element_justification='c')]]
        
        col3 = [[sg.Column([
                [sg.Frame('CAMERA', [
                [sg.Image(key='_COMP7310_', size=(480, 320))],
                ], font=middle_font)],
                [sg.Text('Heart Rate:', font=middle_font)],
                [sg.Text('Put Heart Rate Here', font =('Arial', 20) )]
                ], pad=(0, 0), element_justification='c')] 
                ]
        layout = [[
            sg.Column(col1), sg.Column(col2), sg.Column(col3)
        ]]

        self.window = sg.Window('Python MQTT Client - AWS IoT -', layout)
        while True:
            event, values = self.window.Read(timeout=5)
            if event is None or event == 'Exit':
                break

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
                        self.publish_message('config_frame', str(input2_value))
                        self.window['_NOTES_'].print('Set rating frame: ' + str(input2_value))
            # brightness
            if event == '_SUBMIT3_':
                if self.window['_CONNECT_BTN_'].get_text() == 'Connect':
                     sg.popup('Please Connect First!')
                else:
                    slider_value = values['_INPUT3_']
                    self.publish_message('config_brightness', slider_value)
                    self.window['_NOTES_'].print('Set brightness ' + str(slider_value))  
            # contrast
            if event == '_SUBMIT4_':
                if self.window['_CONNECT_BTN_'].get_text() == 'Connect':
                     sg.popup('Please Connect First!')
                else:
                    slider_value = values['_INPUT4_']
                    self.publish_message('config_contrast', slider_value)
                    self.window['_NOTES_'].print('Set contrast ' + str(slider_value))  
            # saturation
            if event == '_SUBMIT5_':
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
            if event == '_SUBMIT7_':
                message = 0
                if self.window['_CONNECT_BTN_'].get_text() == 'Connect':
                     sg.popup('Please Connect First!')
                else:
                    if values['_WHIDIS_']:
                        message = 0
                    elif values['_WHIENA_']:
                        message = 1
                    self.publish_message('config_whitebal', message)
                    self.window['_NOTES_'].print('Set whitebal ' + str(message)) 
            # wb mode
            if event == '_SUBMIT8_':
                if self.window['_CONNECT_BTN_'].get_text() == 'Connect':
                     sg.popup('Please Connect First!')
                else:
                    input8_value = self.window['_INPUT8_'].get()
                    options = ['Auto', 'Sunny', 'Cloudy', 'Office', 'Home']
                    index = options.index(input8_value)
                    self.publish_message('config_wb', index)
                    self.window['_NOTES_'].print('Set effect ' + str(input8_value)) 
            # expo ctr
            if event == '_SUBMIT9_':
                message = 0
                if self.window['_CONNECT_BTN_'].get_text() == 'Connect':
                     sg.popup('Please Connect First!')
                else:
                    if values['_EXPDIS_']:
                        message = 0
                    elif values['_EXPENA_']:
                        message = 1
                    self.publish_message('config_exposure', message)
                    self.window['_NOTES_'].print('Set exposure ' + str(message)) 

            try:
                message = self.gui_queue.get_nowait()
            except queue.Empty:
                message = None
            if message is not None:
                _target_ui = message.get("Target_UI")
                _image = message.get("Image")
                self.window[_target_ui].update(data=_image)

        self.window.Close()

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

            else:
                self.add_note('[MQTT] Cannot Access AWS IOT')
        except Exception as e:
            tb = traceback.format_exc()
            sg.Print(f'An error happened.  Here is the info:', e, tb)

    def aws_disconnect(self):
        if self.myAWSIoTMQTTClient is not None:
            self.myAWSIoTMQTTClient.disconnect()
            self.add_note('[MQTT] Successfully Disconnected!')

    def mqtt_subscribe(self, topic):
        if self.myAWSIoTMQTTClient.subscribe(topic, 0, lambda client, userdata, message: {

            self.gui_queue.put({"Target_UI": "_{}_".format(str(message.topic).upper()),
                                "Image": self.byte_image_to_png(message)})
        }):
            self.add_note('[MQTT] Topic: {}\n-> Subscribed\n'.format(topic))
        else:
            self.add_note('[MQTT] Cannot subscribe\nthis Topic: {}'.format(topic))

    def add_note(self, note):
        note_history = self.window['_NOTES_'].get()
        self.window['_NOTES_'].update(note_history + note if len(note_history) > 1 else note)

    def byte_image_to_png(self, message):
        bytes_image = io.BytesIO(message.payload)
        picture = Image.open(bytes_image)

        im_bytes = io.BytesIO()
        picture.save(im_bytes, format="PNG")
        return im_bytes.getvalue()

    def popup_dialog(self, contents, title, font):
        sg.Popup(contents, title=title, keep_on_top=True, font=font)

    def publish_message(self, TOPIC, message):
        self.myAWSIoTMQTTClient.publish(TOPIC, str(message), 1) 
        self.window['_NOTES_'].print("Published: '" + str(message) + "' to the topic: " + str(TOPIC))

if __name__ == '__main__':
    Application()

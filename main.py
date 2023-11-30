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
            [sg.Frame('MQTT Panel', [[sg.Column([
                [sg.Text('Client Id:', font=middle_font)],
                [sg.Input('Python_Client', key='_CLIENTID_IN_', size=(15, 1), font=context_font),
                 sg.Button('Connect', key='_CONNECT_BTN_', font=context_font)],
                # Add text boxes and buttons for user input
                [sg.Text('Frame Size', font=middle_font)],
                [sg.Combo(['FRAMESIZE_QVGA (320 x 240)', 'FRAMESIZE_CIF (352 x 288)', 'FRAMESIZE_VGA (640 x 480)', 'FRAMESIZE_SVGA (800 x 600)'],
                default_value='FRAMESIZE_VGA (640 x 480)', key='_INPUT1_')],
                [sg.Button('Submit', key='_SUBMIT1_', font=context_font)],
                [sg.Text('Sampling rate', font=middle_font)],
                [sg.Combo([60,30, 20, 10],
                default_value=30, key='_INPUT2_')],
                [sg.Button('Submit', key='_SUBMIT2_', font=context_font)],
                [sg.Slider(range=(-2, 2), default_value=0, orientation='h', key='_INPUT3_')],
                [sg.Button('Submit', key='_SUBMIT3_', font=('Arial', 12))],
                [sg.Text('Notes:', font=middle_font)],
                [sg.Multiline(key='_NOTES_', autoscroll=True, size=(26, 34), font=context_font, )],
            ], size=(235, 640), pad=(0, 0))]], font=middle_font)], ], pad=(0, 0), element_justification='c')]]

        col2 = [[sg.Column([
                [sg.Frame('CAMERA', [
                    [sg.Image(key='_COMP7310_', size=(480, 320))],
                    ], font=middle_font)]], pad=(0, 0), element_justification='c')] 
                ]
        col3 = [[sg.Column([
            [sg.Text('Heart Rate:', font=middle_font)],
            [sg.Text('Put Heart Rate Here', font =('Arial', 20) )]
        ])]]
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
            if event == '_SUBMIT1_':
                if self.window['_CONNECT_BTN_'].get_text() == 'Connect':
                     sg.popup('Please Connect First!')
                else:
                    input1_value = self.window['_INPUT1_'].get()
                    if input1_value:
                        options = ['FRAMESIZE_QVGA (320 x 240)', 'FRAMESIZE_CIF (352 x 288)', 'FRAMESIZE_VGA (640 x 480)', 'FRAMESIZE_SVGA (800 x 600)']
                        index = options.index(input1_value)
                        self.publish_message('config_size', 'f:'+str(index))
                        self.window['_NOTES_'].print('Set frame size: ' + str(input1_value))
            if event == '_SUBMIT2_':
                if self.window['_CONNECT_BTN_'].get_text() == 'Connect':
                     sg.popup('Please Connect First!')
                else:
                    input2_value = self.window['_INPUT2_'].get()
                    if input2_value:
                        self.publish_message('config_frame', str(input2_value))
                        self.window['_NOTES_'].print('Set rating frame: ' + str(input2_value))

            if event == '_SUBMIT3_':
                if self.window['_CONNECT_BTN_'].get_text() == 'Connect':
                     sg.popup('Please Connect First!')
                else:
                    slider_value = self.window['_INPUT3_']
                    self.publish_message('config_brightness', slider_value)
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

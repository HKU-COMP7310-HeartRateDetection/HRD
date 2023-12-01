#!/usr/bin/env python
# coding: utf-8

# In[1]:


import scipy.io as sio
import numpy as np
import matplotlib.pyplot as plt
import math
import base64
from scipy import signal
from scipy import sparse
import matplotlib.pyplot as plt
import time
import scipy
import scipy.io
from scipy.signal import butter
from scipy.sparse import spdiags
from scipy.signal import find_peaks
#####
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import io
import cv2
RGB =np.empty((0, 3))
heart_rates = [] 
#global_i=0
ENDPOINT = "a12ej9mk5jajtb-ats.iot.ap-east-1.amazonaws.com"
PATH_TO_CERT = "cert.crt"
PATH_TO_KEY = "private.key"
PATH_TO_ROOT = "rootCA.crt"

myAWSIoTMQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient('Other_Client')
myAWSIoTMQTTClient.configureEndpoint(ENDPOINT, 8883)
myAWSIoTMQTTClient.configureCredentials(PATH_TO_ROOT, PATH_TO_KEY, PATH_TO_CERT)

# Connect to the MQTT broker
myAWSIoTMQTTClient.connect()

# OpenCV window to display the image
def on_message(client, userdata, message):
    #print("no")
    global RGB
    global heart_rates
    # Get the image data from the MQTT message
    #RGB = np.array([])
    image_data = message.payload
    
    # Convert the image data to a numpy array
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    sum = np.sum(np.sum(image, axis=0), axis=0)
    #print(sum.shape)
    RGB=np.vstack((RGB,sum/(image.shape[0]*image.shape[1])))
    print(RGB.shape[0],RGB[0],RGB[RGB.shape[0]-1])
    if(RGB.shape[0]>200):
        RGB=RGB[1:]
 
        
myAWSIoTMQTTClient.subscribe("COMP7310",0,on_message)

def POS_WANG(RGB, fs):
    WinSec = 1.6
    N = RGB.shape[0]
    H = np.zeros((1, N))
    l = math.ceil(WinSec * fs)

    for n in range(N):
        m = n - l
        if m >= 0:
            Cn = np.true_divide(RGB[m:n, :], np.mean(RGB[m:n, :], axis=0))
            Cn = np.mat(Cn).H
            S = np.matmul(np.array([[0, 1, -1], [-2, 1, 1]]), Cn)
            h = S[0, :] + (np.std(S[0, :]) / np.std(S[1, :])) * S[1, :]
            mean_h = np.mean(h)
            for temp in range(h.shape[1]):
                h[0, temp] = h[0, temp] - mean_h
            H[0, m:n] = H[0, m:n] + (h[0])

    BVP = H
    BVP = detrend(np.mat(BVP).H, 100)
    BVP = np.asarray(np.transpose(BVP))[0]
    b, a = signal.butter(1, [0.75 / fs * 2, 3 / fs * 2], btype='bandpass')
    BVP = signal.filtfilt(b, a, BVP.astype(np.double))
    return BVP
def detrend(input_signal, lambda_value):
    signal_length = input_signal.shape[0]
    # observation matrix
    H = np.identity(signal_length)
    ones = np.ones(signal_length)
    minus_twos = -2 * np.ones(signal_length)
    diags_data = np.array([ones, minus_twos, ones])
    diags_index = np.array([0, 1, 2])
    D = sparse.spdiags(diags_data, diags_index,
                (signal_length - 2), signal_length).toarray()
    filtered_signal = np.dot(
        (H - np.linalg.inv(H + (lambda_value ** 2) * np.dot(D.T, D))), input_signal)
    return filtered_signal
def _calculate_fft_hr(ppg_signal, fs=30, low_pass=0.75, high_pass=2.5):
    """Calculate heart rate based on PPG using Fast Fourier transform (FFT)."""
    ppg_signal = np.expand_dims(ppg_signal, 0)
    N = _next_power_of_2(ppg_signal.shape[1])
    f_ppg, pxx_ppg = scipy.signal.periodogram(ppg_signal, fs=fs, nfft=N, detrend=False)
    fmask_ppg = np.argwhere((f_ppg >= low_pass) & (f_ppg <= high_pass))
    mask_ppg = np.take(f_ppg, fmask_ppg)
    mask_pxx = np.take(pxx_ppg, fmask_ppg)
    fft_hr = np.take(mask_ppg, np.argmax(mask_pxx, 0))[0] * 60
    return fft_hr
def _next_power_of_2(x):
    """Calculate the nearest power of 2."""
    return 1 if x == 0 else 2 ** (x - 1).bit_length()

#init time
timelist=[]
interval=0.5#time interval
stamp=0#used with interval to append timelist
while True:
        #Process data
    global RGB
    print("HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
    ##After getting 200 frame start to calculate BVP
    if(RGB.shape[0]==200):   
        plt.clf()  
        BVP=POS_WANG(RGB,30)
        heart_rate = _calculate_fft_hr(BVP)
        timelist.append(interval*stamp)
        stamp=stamp+1
        heart_rates.append(heart_rate)
        plt.plot(timelist,heart_rates,color='blue')
        plt.xlabel('Time(s)')
        plt.ylabel('BPM')
        # Save the plot as an image file
        image_buffer = io.BytesIO()
        plt.savefig(image_buffer, format='png')
        image_buffer.seek(0)

        # Read the image file as binary data
        image_data = image_buffer.read()

        # Encode the image data as base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        myAWSIoTMQTTClient.publish("HEARTRATE",base64_image, 0)
        ##
        if(len(heart_rates)==60):
            heart_rates=heart_rates[1:] 
            timelist=timelist[1:]    
    time.sleep(interval)
# Subscribe to the MQTT topic
# Start the MQTT loop
#myAWSIoTMQTTClient.online=myOnOnlineCallback


# In[ ]:





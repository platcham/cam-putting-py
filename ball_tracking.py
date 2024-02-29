# import the necessary packages
from collections import deque
import numpy as np
import argparse
import cv2
import imutils
import time
import sys
import cvzone
from ColorModuleExtended import ColorFinder
import math
from decimal import *
import requests
from configparser import ConfigParser
import ast
import os
import shutil

parser = ConfigParser()
CFG_FILE = 'config.ini'

parser.read(CFG_FILE)

## Check for folder replay1 and replay2 and empty if necessary

if os.path.exists('replay1'):
    try:
        shutil.rmtree('replay1')
        time.sleep(1)
        os.mkdir('replay1')
    except os.error as e:  # This is the correct syntax
        print(e)
else:
    os.mkdir('replay1')

if os.path.exists('replay2'):
    try:
        shutil.rmtree('replay2')
        time.sleep(1)
        os.mkdir('replay2')
    except os.error as e:  # This is the correct syntax
        print(e)
else:
    os.mkdir('replay2')


# Startpoint Zone

ballradius = 0
darkness = 0
flipImage = 0
mjpegenabled = 0
ps4=0
overwriteFPS = 0

customhsv = {}

replaycam=0
replaycamindex=0
timeSinceTriggered = 0
replaycamps4 = 0
replay = False
noOfStarts = 0
replayavail = False
frameskip = 0



if parser.has_option('putting', 'startx1'):
    sx1=int(parser.get('putting', 'startx1'))
else:
    sx1=10
if parser.has_option('putting', 'startx2'):
    sx2=int(parser.get('putting', 'startx2'))
else:
    sx2=180
if parser.has_option('putting', 'y1'):
    y1=int(parser.get('putting', 'y1'))
else:
    y1=180
if parser.has_option('putting', 'y2'):
    y2=int(parser.get('putting', 'y2'))
else:
    y2=450
if parser.has_option('putting', 'radius'):
    ballradius=int(parser.get('putting', 'radius'))
else:
    ballradius=0
if parser.has_option('putting', 'flip'):
    flipImage=int(parser.get('putting', 'flip'))
else:
    flipImage=0
if parser.has_option('putting', 'flipview'):
    flipView=int(parser.get('putting', 'flipview'))
else:
    flipView=0
if parser.has_option('putting', 'darkness'):
    darkness=int(parser.get('putting', 'darkness'))
else:
    darkness=0
if parser.has_option('putting', 'mjpeg'):
    mjpegenabled=int(parser.get('putting', 'mjpeg'))
else:
    mjpegenabled=0
if parser.has_option('putting', 'ps4'):
    ps4=int(parser.get('putting', 'ps4'))
else:
    ps4=0
if parser.has_option('putting', 'fps'):
    overwriteFPS=int(parser.get('putting', 'fps'))
else:
    overwriteFPS=0
if parser.has_option('putting', 'height'):
    height=int(parser.get('putting', 'height'))
else:
    height=360
if parser.has_option('putting', 'width'):
    width=int(parser.get('putting', 'width'))
else:
    width=640
if parser.has_option('putting', 'customhsv'):
    customhsv=ast.literal_eval(parser.get('putting', 'customhsv'))
    print(customhsv)
else:
    customhsv={}
if parser.has_option('putting', 'showreplay'):
    showreplay=int(parser.get('putting', 'showreplay'))
else:
    showreplay=0
if parser.has_option('putting', 'replaycam'):
    replaycam=int(parser.get('putting', 'replaycam'))
else:
    replaycam=0
if parser.has_option('putting', 'replaycamindex'):
    replaycamindex=int(parser.get('putting', 'replaycamindex'))
else:
    replaycamindex=0
if parser.has_option('putting', 'replaycamps4'):
    replaycamps4=int(parser.get('putting', 'replaycamps4'))
else:
    replaycamps4=0
if parser.has_option('putting', 'angleAdjust'):
	hlaAdjust=float(parser.get('putting', 'angleAdjust'))
else:
	hlaAdjust=0.0

# Globals

# Detection Gateway
x1=sx2+10
x2=x1+10

#coord of polygon in frame::: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
startcoord=[[sx1,y1],[sx2,y1],[sx1,y2],[sx2,y2]]

#coord of polygon in frame::: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
coord=[[x1,y1],[x2,y1],[x1,y2],[x2,y2]]

golfballradius = 21.33; # in mm

actualFPS = 0

videoStartTime = time.time()

# initialize variables to store the start and end positions of the ball
startCircle = (0, 0, 0)
endCircle = (0, 0, 0)
startPos = (0,0)
endPos = (0,0)
startTime = time.time()
timeSinceEntered = 0
replaytimeSinceEntered = 0
pixelmmratio = 0

# initialize variable to store start candidates of balls
startCandidates = []
startminimum = 30

# Initialize Entered indicator
entered = False
started = False
left = False

lastShotStart = (0,0)
lastShotEnd = (0,0)
lastShotSpeed = 0
lastShotHLA = 0 

speed = 0

tim1 = 0
tim2 = 0
replaytrigger = 0

# calibration

colorcount = 0
calibrationtime = time.time()
calObjectCount = 0
calColorObjectCount = []
calibrationTimeFrame = 30

# Calibrate Recording Indicator

record = True

# Videofile Indicator

videofile = False

# remove duplicate advanced screens for multipla 'a' and 'd' key presses)
a_key_pressed = False 
d_key_pressed = False 


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video",
                help="path to the (optional) video file")
ap.add_argument("-i", "--img",
                help="path to the (optional) image file")
ap.add_argument("-b", "--buffer", type=int, default=64,
                help="max buffer size - default is 64")
ap.add_argument("-w", "--camera", type=int, default=0,
                help="webcam index number - default is 0")
ap.add_argument("-c", "--ballcolor",
                help="ball color - default is yellow")
ap.add_argument("-d", "--debug",
                help="debug - color finder and wait timer")
ap.add_argument("-r", "--resize", type=int, default=640,
                help="window resize in width pixel - default is 640px")
args = vars(ap.parse_args())

# define the lower and upper boundaries of the different ball color options (-c)
# ball in the HSV color space, then initialize the

#red                   
red = {'hmin': 1, 'smin': 208, 'vmin': 0, 'hmax': 50, 'smax': 255, 'vmax': 249} # light
red2 = {'hmin': 1, 'smin': 240, 'vmin': 61, 'hmax': 50, 'smax': 255, 'vmax': 249} # dark

#white
white = {'hmin': 168, 'smin': 218, 'vmin': 118, 'hmax': 179, 'smax': 247, 'vmax': 216} # very light
white2 = {'hmin': 159, 'smin': 217, 'vmin': 152, 'hmax': 179, 'smax': 255, 'vmax': 255} # light
white3 = {'hmin': 0, 'smin': 181, 'vmin': 0, 'hmax': 42, 'smax': 255, 'vmax': 255}

#yellow

yellow = {'hmin': 0, 'smin': 210, 'vmin': 0, 'hmax': 15, 'smax': 255, 'vmax': 255} # light
yellow2 = {'hmin': 0, 'smin': 150, 'vmin': 100, 'hmax': 46, 'smax': 255, 'vmax': 206} # dark

#green
green = {'hmin': 0, 'smin': 169, 'vmin': 161, 'hmax': 177, 'smax': 204, 'vmax': 255} # light
green2 = {'hmin': 0, 'smin': 109, 'vmin': 74, 'hmax': 81, 'smax': 193, 'vmax': 117} # dark

#orange
orange = {'hmin': 0, 'smin': 219, 'vmin': 147, 'hmax': 19, 'smax': 255, 'vmax': 255}# light
orange2 = {'hmin': 3, 'smin': 181, 'vmin': 134, 'hmax': 40, 'smax': 255, 'vmax': 255}# dark
orange3 = {'hmin': 0, 'smin': 73, 'vmin': 150, 'hmax': 40, 'smax': 255, 'vmax': 255}# test
orange4 = {'hmin': 3, 'smin': 181, 'vmin': 216, 'hmax': 40, 'smax': 255, 'vmax': 255}# ps3eye

calibrate = {}

# for Colorpicker
# default yellow option
hsvVals = yellow

if customhsv == {}:

    if args.get("ballcolor", False):
        if args["ballcolor"] == "white":
            hsvVals = white
        elif args["ballcolor"] == "white2":
            hsvVals = white2
        elif args["ballcolor"] ==  "yellow":
            hsvVals = yellow 
        elif args["ballcolor"] ==  "yellow2":
            hsvVals = yellow2 
        elif args["ballcolor"] ==  "orange":
            hsvVals = orange
        elif args["ballcolor"] ==  "orange2":
            hsvVals = orange2
        elif args["ballcolor"] ==  "orange3":
            hsvVals = orange3
        elif args["ballcolor"] ==  "orange4":
            hsvVals = orange4
        elif args["ballcolor"] ==  "green":
            hsvVals = green 
        elif args["ballcolor"] ==  "green2":
            hsvVals = green2               
        elif args["ballcolor"] ==  "red":
            hsvVals = red             
        elif args["ballcolor"] ==  "red2":
            hsvVals = red2             
        else:
            hsvVals = yellow

        if args["ballcolor"] is not None:
            print("Ballcolor: "+str(args["ballcolor"]))
else:
    hsvVals = customhsv
    print("Custom HSV Values set in config.ini")




calibrationcolor = [("white",white),("white2",white2),("yellow",yellow),("yellow2",yellow2),("orange",orange),("orange2",orange2),("orange3",orange3),("orange4",orange4),("green",green),("green2",green2),("red",red),("red2",red2)]

def resizeWithAspectRatio(image, width=None, height=None, inter=cv2.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]

    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))

    return cv2.resize(image, dim, interpolation=inter)


# Start Splash Screen

frame = cv2.imread("error.png")
origframe2 = cv2.imread("error.png")
cv2.putText(frame,"Starting Video: Try MJPEG option in advanced settings for faster startup",(20,100),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))
outputframe = resizeWithAspectRatio(frame, width=int(args["resize"]))
cv2.imshow("Putting View: Press q to exit / a for adv. settings", outputframe)

# Create the color Finder object set to True if you need to Find the color

if args.get("debug", False):
    myColorFinder = ColorFinder(True)
    myColorFinder.setTrackbarValues(hsvVals)
else:
    myColorFinder = ColorFinder(False)

pts = deque(maxlen=args["buffer"])
tims = deque(maxlen=args["buffer"])
fpsqueue = deque(maxlen=240)
replay1queue = deque(maxlen=600)
replay2queue = deque(maxlen=600)

webcamindex = 0

message = ""


# if a webcam index is supplied, grab the reference
if args.get("camera", False):
    webcamindex = args["camera"]
    print("Putting Cam activated at "+str(webcamindex))

# if a video path was not supplied, grab the reference
# to the webcam
if not args.get("video", False):
    if mjpegenabled == 0:
        vs = cv2.VideoCapture(webcamindex)
    else:
        vs = cv2.VideoCapture(webcamindex + cv2.CAP_DSHOW)
        # Check if FPS is overwritten in config
        if overwriteFPS != 0:
            vs.set(cv2.CAP_PROP_FPS, overwriteFPS)
            print("Overwrite FPS: "+str(vs.get(cv2.CAP_PROP_FPS)))
        if height != 0 and width != 0:
            vs.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            vs.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        mjpeg = cv2.VideoWriter_fourcc('M','J','P','G')
        vs.set(cv2.CAP_PROP_FOURCC, mjpeg)
    if vs.get(cv2.CAP_PROP_BACKEND) == -1:
        message = "No Camera could be opened at webcamera index "+str(webcamindex)+". If your webcam only supports compressed format MJPEG instead of YUY2 please set MJPEG option to 1"
    else:
        if ps4 == 1:
            vs.set(cv2.CAP_PROP_FPS, 120)
            vs.set(cv2.CAP_PROP_FRAME_WIDTH, 1724)
            vs.set(cv2.CAP_PROP_FRAME_HEIGHT, 404)
            #cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3448)
            #cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 808)
        print("Backend: "+str(vs.get(cv2.CAP_PROP_BACKEND)))
        print("FourCC: "+str(vs.get(cv2.CAP_PROP_FOURCC)))
        print("FPS: "+str(vs.get(cv2.CAP_PROP_FPS)))
else:
    vs = cv2.VideoCapture(args["video"])
    videofile = True

# Get video metadata

video_fps = vs.get(cv2.CAP_PROP_FPS)
height = vs.get(cv2.CAP_PROP_FRAME_HEIGHT)
width = vs.get(cv2.CAP_PROP_FRAME_WIDTH)

if parser.has_option('putting', 'saturation'):
    saturation=float(parser.get('putting', 'saturation'))
else:
    saturation = vs.get(cv2.CAP_PROP_SATURATION)
if parser.has_option('putting', 'exposure'):
    exposure=float(parser.get('putting', 'exposure'))
else:
    exposure = vs.get(cv2.CAP_PROP_EXPOSURE)
if parser.has_option('putting', 'autowb'):
    autowb=float(parser.get('putting', 'autowb'))
else:
    autowb = vs.get(cv2.CAP_PROP_AUTO_WB)
if parser.has_option('putting', 'whiteBalanceBlue'):
    whiteBalanceBlue=float(parser.get('putting', 'whiteBalanceBlue'))
else:
    whiteBalanceBlue = vs.get(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U)
if parser.has_option('putting', 'whiteBalanceRed'):
    whiteBalanceRed=float(parser.get('putting', 'whiteBalanceRed'))
else:
    whiteBalanceRed = vs.get(cv2.CAP_PROP_WHITE_BALANCE_RED_V)
if parser.has_option('putting', 'brightness'):
    brightness=float(parser.get('putting', 'brightness'))
else:
    brightness = vs.get(cv2.CAP_PROP_BRIGHTNESS)
if parser.has_option('putting', 'contrast'):
    contrast=float(parser.get('putting', 'contrast'))
else:
    contrast = vs.get(cv2.CAP_PROP_CONTRAST)
if parser.has_option('putting', 'hue'):
    hue=float(parser.get('putting', 'hue'))
else:
    hue = vs.get(cv2.CAP_PROP_HUE)
if parser.has_option('putting', 'gain'):
    gain=float(parser.get('putting', 'gain'))
else:
    gain = vs.get(cv2.CAP_PROP_HUE)
if parser.has_option('putting', 'monochrome'):
    monochrome=float(parser.get('putting', 'monochrome'))
else:
    monochrome = vs.get(cv2.CAP_PROP_MONOCHROME)
if parser.has_option('putting', 'sharpness'):
    sharpness=float(parser.get('putting', 'sharpness'))
else:
    sharpness = vs.get(cv2.CAP_PROP_SHARPNESS)
if parser.has_option('putting', 'autoexposure'):
    autoexposure=float(parser.get('putting', 'autoexposure'))
else:
    autoexposure = vs.get(cv2.CAP_PROP_AUTO_EXPOSURE)
if parser.has_option('putting', 'gamma'):
    gamma=float(parser.get('putting', 'gamma'))
else:
    gamma = vs.get(cv2.CAP_PROP_GAMMA)
if parser.has_option('putting', 'zoom'):
    zoom=float(parser.get('putting', 'zoom'))
else:
    zoom = vs.get(cv2.CAP_PROP_ZOOM)
    gamma = vs.get(cv2.CAP_PROP_GAMMA)
if parser.has_option('putting', 'focus'):
    focus=float(parser.get('putting', 'focus'))
else:
    focus = vs.get(cv2.CAP_PROP_FOCUS)
if parser.has_option('putting', 'autofocus'):
    autofocus=float(parser.get('putting', 'autofocus'))
else:
    autofocus = vs.get(cv2.CAP_PROP_AUTOFOCUS)

vs.set(cv2.CAP_PROP_SATURATION,saturation)
vs.set(cv2.CAP_PROP_EXPOSURE,exposure)
vs.set(cv2.CAP_PROP_AUTO_WB,autowb)
vs.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U,whiteBalanceBlue)
vs.set(cv2.CAP_PROP_WHITE_BALANCE_RED_V,whiteBalanceRed)
vs.set(cv2.CAP_PROP_BRIGHTNESS,brightness)
vs.set(cv2.CAP_PROP_CONTRAST,contrast)
vs.set(cv2.CAP_PROP_HUE,hue)
vs.set(cv2.CAP_PROP_GAIN,gain)
vs.set(cv2.CAP_PROP_MONOCHROME,monochrome)
vs.set(cv2.CAP_PROP_SHARPNESS,sharpness)
vs.set(cv2.CAP_PROP_AUTO_EXPOSURE,autoexposure)
vs.set(cv2.CAP_PROP_GAMMA,gamma)
vs.set(cv2.CAP_PROP_ZOOM,zoom)
vs.set(cv2.CAP_PROP_FOCUS,focus)
vs.set(cv2.CAP_PROP_AUTOFOCUS,autofocus)


print("video_fps: "+str(video_fps))
print("height: "+str(height))
print("width: "+str(width))

if replaycam == 1:
    if replaycamindex == webcamindex:
        print("Replaycamindex must be different to webcam index")
        replaycam = 0
    else:

        print("Replay Cam activated at "+str(replaycamindex))


# replay is enabled start a 2nd video capture
if replaycam == 1:
    if mjpegenabled == 0:
        vs2 = cv2.VideoCapture(replaycamindex)
    else:
        vs2 = cv2.VideoCapture(replaycamindex + cv2.CAP_DSHOW)
        # Check if FPS is overwritten in config
        if overwriteFPS != 0:
            vs2.set(cv2.CAP_PROP_FPS, overwriteFPS)
            print("Overwrite FPS: "+str(vs.get(cv2.CAP_PROP_FPS)))
        if height != 0 and width != 0:
            vs2.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            vs2.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        mjpeg = cv2.VideoWriter_fourcc('M','J','P','G')
        vs2.set(cv2.CAP_PROP_FOURCC, mjpeg)
    if vs2.get(cv2.CAP_PROP_BACKEND) == -1:
        message = "No Camera could be opened at webcamera index "+str(replaycamindex)+". If your webcam only supports compressed format MJPEG instead of YUY2 please set MJPEG option to 1"
    else:
        if replaycamps4 == 1:
            #cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3448)
            #cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 808)
            vs2.set(cv2.CAP_PROP_FPS, 120)
            vs2.set(cv2.CAP_PROP_FRAME_WIDTH, 1724)
            vs2.set(cv2.CAP_PROP_FRAME_HEIGHT, 404)
        print("Backend: "+str(vs.get(cv2.CAP_PROP_BACKEND)))
        print("FourCC: "+str(vs.get(cv2.CAP_PROP_FOURCC)))
        print("FPS: "+str(vs.get(cv2.CAP_PROP_FPS)))
    replaycamheight = vs2.get(cv2.CAP_PROP_FRAME_HEIGHT)
    replaycamwidth = vs2.get(cv2.CAP_PROP_FRAME_WIDTH)
else:
    print("Replay Cam not activated")



if type(video_fps) == float:
    if video_fps == 0.0:
        e = vs.set(cv2.CAP_PROP_FPS, 60)
        new_fps = []
        new_fps.append(0)

    if video_fps > 0.0:
        new_fps = []
        new_fps.append(video_fps)
    video_fps = new_fps


# we are using x264 codec for mp4
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out2 = cv2.VideoWriter('Calibration.mp4', apiPreference=0, fourcc=fourcc,fps=120, frameSize=(int(width), int(height)))



def decode(myframe):
    left = np.zeros((400,632,3), np.uint8)
    right = np.zeros((400,632,3), np.uint8)
    
    for i in range(400):
        left[i] = myframe[i, 32: 640 + 24] 
        right[i] = myframe[i, 640 + 24: 640 + 24 + 632] 
    
    return (left, right)

def setFPS(value):
    print(value)
    vs.set(cv2.CAP_PROP_FPS,value)
    pass 

def setXStart(value):
    print(value)
    startcoord[0][0]=value
    startcoord[2][0]=value

    global sx1
    sx1=int(value)    
    parser.set('putting', 'startx1', str(sx1))
    parser.write(open(CFG_FILE, "w"))
    pass

def setXEnd(value):
    print(value)
    startcoord[1][0]=value
    startcoord[3][0]=value 

    global x1
    global x2
    global sx2
     
    # Detection Gateway
    x1=int(value+10)
    x2=int(x1+10)

    #coord=[[x1,y1],[x2,y1],[x1,y2],[x2,y2]]
    coord[0][0]=x1
    coord[2][0]=x1
    coord[1][0]=x2
    coord[3][0]=x2

    sx2=int(value)    
    parser.set('putting', 'startx2', str(sx2))
    parser.write(open(CFG_FILE, "w"))
    pass  

def setYStart(value):
    print(value)
    startcoord[0][1]=value
    startcoord[1][1]=value

    global y1

    #coord=[[x1,y1],[x2,y1],[x1,y2],[x2,y2]]
    coord[0][1]=value   
    coord[1][1]=value

    y1=int(value)    
    parser.set('putting', 'y1', str(y1))
    parser.write(open(CFG_FILE, "w"))     
    pass


def setYEnd(value):
    print(value)
    startcoord[2][1]=value
    startcoord[3][1]=value 

    global y2

    #coord=[[x1,y1],[x2,y1],[x1,y2],[x2,y2]]
    coord[2][1]=value   
    coord[3][1]=value

    y2=int(value)    
    parser.set('putting', 'y2', str(y2))
    parser.write(open(CFG_FILE, "w"))     
    pass 

def setBallRadius(value):
    print(value)    
    global ballradius
    ballradius = int(value)
    parser.set('putting', 'radius', str(ballradius))
    parser.write(open(CFG_FILE, "w"))
    pass

def setFlip(value):
    print(value)    
    global flipImage
    flipImage = int(value)
    parser.set('putting', 'flip', str(flipImage))
    parser.write(open(CFG_FILE, "w"))
    pass

def setFlipView(value):
    print(value)    
    global flipView
    flipView = int(value)
    parser.set('putting', 'flipView', str(flipView))
    parser.write(open(CFG_FILE, "w"))
    pass

def setMjpeg(value):
    print(value)    
    global mjpegenabled
    global message
    if mjpegenabled != int(value):
        vs.release()
        message = "Video Codec changed - Please restart the putting app"
    mjpegenabled = int(value)
    parser.set('putting', 'mjpeg', str(mjpegenabled))
    parser.write(open(CFG_FILE, "w"))
    pass

def setOverwriteFPS(value):
    print(value)    
    global overwriteFPS
    global message
    if overwriteFPS != int(value):
        vs.release()
        message = "Overwrite of FPS changed - Please restart the putting app"
    overwriteFPS = int(value)
    parser.set('putting', 'fps', str(overwriteFPS))
    parser.write(open(CFG_FILE, "w"))
    pass

def setDarkness(value):
    print(value)    
    global darkness
    darkness = int(value)
    parser.set('putting', 'darkness', str(darkness))
    parser.write(open(CFG_FILE, "w"))
    pass

def GetAngle (p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    dX = x2 - x1
    dY = y2 - y1
    rads = math.atan2 (-dY, dX)

    if flipImage == 1 and videofile == False:    	
        rads = rads*-1
    return math.degrees (rads)

def rgb2yuv(rgb):
    m = np.array([
        [0.29900, -0.147108,  0.614777],
        [0.58700, -0.288804, -0.514799],
        [0.11400,  0.435912, -0.099978]
    ])
    yuv = np.dot(rgb, m)
    yuv[:,:,1:] += 0.5
    return yuv

def yuv2rgb(yuv):
    m = np.array([
        [1.000,  1.000, 1.000],
        [0.000, -0.394, 2.032],
        [1.140, -0.581, 0.000],
    ])
    yuv[:, :, 1:] -= 0.5
    rgb = np.dot(yuv, m)
    return rgb

# allow the camera or video file to warm up
time.sleep(0.5)

previousFrame = cv2.Mat

while True:
    # set the frameTime
    frameTime = time.time()
    fpsqueue.append(frameTime)
    
    actualFPS = actualFPS + 1
    videoTimeDiff = fpsqueue[len(fpsqueue)-1] - fpsqueue[0]
    if videoTimeDiff != 0:
        fps = len(fpsqueue) / videoTimeDiff
    else:
        fps = 0

    if args.get("img", False):
        frame = cv2.imread(args["img"])
    else:
        # get webcam frame
        ret, frame = vs.read()
        if ps4 == 1 and ret == True:
            leftframe, rightframe = decode(frame)
            frame = leftframe[0:400,20:632]
            width = 612
            height = 400
        # get replaycam frame
        if replaycam == 1:
            ret2, origframe2 = vs2.read()
            if replaycamps4 == 1 and ret2 == True:
                leftframe2, rightframe2 = decode(origframe2)
                origframe2 = leftframe2[0:400,20:632]
                replaycamwidth = 612
                replaycamheight = 400
        # flip image on y-axis
        if flipImage == 1 and videofile == False:	
            frame = cv2.flip(frame, flipImage)
        
        if args["ballcolor"] == "calibrate":
            if record == False:
                if args.get("debug", False):
                    cv2.waitKey(int(args["debug"]))
                if frame is None:
                    calColorObjectCount.append((calibrationcolor[colorcount][0],calObjectCount))
                    colorcount += 1
                    calObjectCount = 0
                    if colorcount == len(calibrationcolor):
                        vs.release()
                        vs = cv2.VideoCapture(webcamindex)
                        videofile = False
                        #vs.set(cv2.CAP_PROP_FPS, 60)
                        ret, frame = vs.read()
                        # flip image on y-axis
                        if flipImage == 1 and videofile == False:    	
                            frame = cv2.flip(frame, flipImage)
                        print("Calibration Finished:"+str(calColorObjectCount))
                        cv2.putText(frame,"Calibration Finished:",(150,100),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))
                        i = 20
                        texty = 100
                        for calObject in calColorObjectCount:
                            texty = texty+i
                            cv2.putText(frame,str(calObject),(150,texty),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))
                        texty = texty+i
                        cv2.putText(frame,"Hit any key and choose color with the highest count.",(150,texty),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))
                        cv2.imshow("Putting View: Press Q to exit / changing Ball Color", frame)
                        cv2.waitKey(0)
                        # Show Results back to Connect App and set directly highest count - maybe also check for false Exit lowest value if 2 colors have equal hits
                        break
                    else:
                        vs.release()                        
                        # grab the calibration video
                        vs = cv2.VideoCapture('Calibration.mp4')
                        videofile = True
                        # grab the current frame
                        ret, frame = vs.read()
                else:
                    hsvVals = calibrationcolor[colorcount][1]
                    if args.get("debug", False):
                        myColorFinder.setTrackbarValues(hsvVals)
                    cv2.putText(frame,"Calibration Mode:"+str(calibrationcolor[colorcount][0]),(200,100),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))
            else:
                if (frameTime - calibrationtime) > calibrationTimeFrame:
                    record =  False
                    out2.release()
                    vs.release()
                    # grab the calibration video
                    vs = cv2.VideoCapture('Calibration.mp4')
                    videofile = True
                    # grab the current frame
                    ret, frame = vs.read()
                cv2.putText(frame,"Calibration Mode:",(200,100),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255)) 

        # handle the frame from VideoCapture or VideoStream
        # frame = frame[1] if args.get("video", False) else frame

        # if we are viewing a video and we did not grab a frame,
        # then we have reached the end of the video
        if frame is None:
            print("no frame")
            frame = cv2.imread("error.png")
            cv2.putText(frame,"Error: "+"No Frame",(20, 20),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))
            cv2.putText(frame,"Message: "+message,(20, 40),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))
            cv2.imshow("Putting View: Press q to exit / a for adv. settings", frame)
            cv2.waitKey(0)
            break

    origframe = frame.copy()
    
    
    cv2.normalize(frame, frame, 0-darkness, 255-darkness, norm_type=cv2.NORM_MINMAX)
       
    # cropping needed for video files as they are too big
    if args.get("debug", False):   
        # wait for debugging
        cv2.waitKey(int(args["debug"]))
    
    # resize the frame, blur it, and convert it to the HSV
    # color space
    frame = imutils.resize(frame, width=640, height=360)
    #origframe2 = imutils.resize(origframe2, width=640, height=360) 
    #origframe = imutils.resize(frame, width=640, height=360)  
    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # construct a mask for the color "green", then perform
    # a series of dilations and erosions to remove any small
    # blobs left in the mask
    
    # Find the Color Ball
    
    imgColor, mask, newHSV = myColorFinder.update(hsv, hsvVals)
    if hsvVals != newHSV:
        print(newHSV)
        parser.set('putting', 'customhsv', str(newHSV)) #['hmin']+newHSV['smin']+newHSV['vmin']+newHSV['hmax']+newHSV['smax']+newHSV['vmax']))
        parser.write(open(CFG_FILE, "w"))
        hsvVals = newHSV
        print("HSV values changed - Custom Color Set to config.ini")



    mask = mask[y1:y2, sx1:640]

    # Mask now comes from ColorFinder
    #mask = cv2.erode(mask, None, iterations=1)
    #mask = cv2.dilate(mask, None, iterations=5)

    # find contours in the mask and initialize the current
    # (x, y) center of the ball
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # testing with cirlces
    # grayframe = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # circles = cv2.HoughCircles(blurred,cv2.HOUGH_GRADIENT,1,10) 
    # # loop over the (x, y) coordinates and radius of the circles
    # if (circles and len(circles) >= 1):
    #     for (x, y, r) in circles:
    #         cv2.circle(frame, (x, y), r, (0, 255, 0), 4)
    #         cv2.rectangle(frame, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)


    cnts = imutils.grab_contours(cnts)
    center = None
    
    # Startpoint Zone

    cv2.line(frame, (startcoord[0][0], startcoord[0][1]), (startcoord[1][0], startcoord[1][1]), (0, 210, 255), 2)  # First horizontal line
    cv2.line(frame, (startcoord[0][0], startcoord[0][1]), (startcoord[2][0], startcoord[2][1]), (0, 210, 255), 2)  # Vertical left line
    cv2.line(frame, (startcoord[2][0], startcoord[2][1]), (startcoord[3][0], startcoord[3][1]), (0, 210, 255), 2)  # Second horizontal line
    cv2.line(frame, (startcoord[1][0], startcoord[1][1]), (startcoord[3][0], startcoord[3][1]), (0, 210, 255), 2)  # Vertical right line

    # Detection Gateway

    cv2.line(frame, (coord[0][0], coord[0][1]), (coord[1][0], coord[1][1]), (0, 0, 255), 2)  # First horizontal line
    cv2.line(frame, (coord[0][0], coord[0][1]), (coord[2][0], coord[2][1]), (0, 0, 255), 2)  # Vertical left line
    cv2.line(frame, (coord[2][0], coord[2][1]), (coord[3][0], coord[3][1]), (0, 0, 255), 2)  # Second horizontal line
    cv2.line(frame, (coord[1][0], coord[1][1]), (coord[3][0], coord[3][1]), (0, 0, 255), 2)  # Vertical right line

    
    

    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
    # only proceed if at least one contour was found
    if len(cnts) > 0:

        x = 0
        y = 0
        radius = 0
        center= (0,0)
        
        for index in range(len(cnts)):
            circle = (0,0,0)
            center= (0,0)
            radius = 0
            # Eliminate countours that are outside the y dimensions of the detection zone
            ((tempcenterx, tempcentery), tempradius) = cv2.minEnclosingCircle(cnts[index])
            tempcenterx = tempcenterx + sx1
            tempcentery = tempcentery + y1
            if (tempcentery >= y1 and tempcentery <= y2):
                rangefactor = 50
                cv2.drawContours(mask, cnts, index, (60, 255, 255), 1)
                #cv2.putText(frame,"Radius:"+str(int(tempradius)),(int(tempcenterx)+3, int(tempcentery)),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))
                # Eliminate countours significantly different than startCircle by comparing radius in range
                if (started == True and startCircle[2]+rangefactor > tempradius and startCircle[2]-rangefactor < tempradius):
                    x = int(tempcenterx)
                    y = int(tempcentery)
                    radius = int(tempradius)
                    center= (x,y)
                else:
                    if not started:
                        x = int(tempcenterx)
                        y = int(tempcentery)
                        radius = int(tempradius)
                        center= (x,y)
                        #print("No Startpoint Set Yet: "+str(center)+" "+str(startCircle[2]+rangefactor)+" > "+str(radius)+" AND "+str(startCircle[2]-rangefactor)+" < "+str(radius))
            else:
                break
            
            
            #print(cnts)
            

            # only proceed if the radius meets a minimum size
            if radius >=5:
                # draw the circle and centroid on the frame,
                # then update the list of tracked points  
                circle = (x,y,radius)
                if circle:
                    # check if the circle is stable to detect if a new start is there
                    if not started or startPos[0]+10 <= center[0] or startPos[0]-10 >= center[0]:
                        if (center[0] >= sx1 and center[0] <= sx2):
                            startCandidates.append(center)
                            if len(startCandidates) > startminimum :
                                startCandidates.pop(0)
                                #filtered = startCandidates.filter(center.x == value.x and center.y == value.y)
                                arr = np.array(startCandidates)
                                # Create an empty list
                                filter_arr = []
                                # go through each element in arr
                                for element in arr:
                                # if the element is completely divisble by 2, set the value to True, otherwise False
                                    if (element[0] == center[0] and center[1] == element[1]):
                                        filter_arr.append(True)
                                    else:
                                        filter_arr.append(False)

                                filtered = arr[filter_arr]

                                #print(filtered)
                                if len(filtered) >= (startminimum/2):
                                    print("New Start Found")
                                    replayavail = False
                                    noOfStarts = noOfStarts + 1
                                    lastShotSpeed = 0
                                    pts.clear()
                                    tims.clear()
                                    filteredcircles = []
                                    filteredcircles.append(circle)
                                    startCircle = circle
                                    startPos = center
                                    startTime = frameTime
                                    #print("Start Position: "+ str(startPos[0]) +":" + str(startPos[1]))
                                    # Calculate the pixel per mm ratio according to z value of circle and standard radius of 2133 mm
                                    if ballradius == 0:
                                        pixelmmratio = circle[2] / golfballradius
                                    else:
                                        pixelmmratio = ballradius / golfballradius
                                    #print("Pixel ratio to mm: " +str(pixelmmratio))    
                                    started = True
                                    replay = True
                                    replaytrigger = 0          
                                    entered = False
                                    left = False
                                    # update the points and tims queues
                                    pts.appendleft(center)
                                    tims.appendleft(frameTime)  
                                    global replay1
                                    global replay2

                                    replay1 = cv2.VideoWriter('replay1/Replay1_'+ str(noOfStarts) +'.mp4', apiPreference=0, fourcc=fourcc,fps=120, frameSize=(int(width), int(height)))
                                    if replaycam == 1:
                                        replay2 = cv2.VideoWriter('replay2/Replay2_'+ str(noOfStarts) +'.mp4', apiPreference=0, fourcc=fourcc,fps=120, frameSize=(int(replaycamwidth), int(replaycamheight)))

                        else:

                            if (x >= coord[0][0] and entered == False and started == True):
                                cv2.line(frame, (coord[0][0], coord[0][1]), (coord[2][0], coord[2][1]), (0, 255, 0),2)  # Changes line color to green
                                tim1 = frameTime
                                print("Ball Entered. Position: "+str(center))
                                startPos = center
                                entered = True
                                # update the points and tims queues
                                pts.appendleft(center)
                                tims.appendleft(frameTime)
                                
                                break
                            else:
                                if ( x > coord[1][0] and entered == True and started == True):
                                    #calculate hla for circle and pts[0]
                                    previousHLA = (GetAngle((startCircle[0],startCircle[1]),pts[0])*-1) + hlaAdjust
                                    #calculate hla for circle and now
                                    currentHLA = (GetAngle((startCircle[0],startCircle[1]),center)*-1) + hlaAdjust
                                    #check if HLA is inverted
                                    similarHLA = False
                                    if left == True:
                                        if ((previousHLA <= 0 and currentHLA <=2) or (previousHLA >= 0 and currentHLA >=-2)):
                                            hldDiff = (pow(currentHLA, 2) - pow(previousHLA, 2))
                                            if  hldDiff < 30:
                                                similarHLA = True
                                        else:
                                            similarHLA = False
                                    else:
                                        similarHLA = True
                                    if ( x > (pts[0][0]+50)and similarHLA == True): # and (pow((y - (pts[0][1])), 2)) <= pow((y - (pts[1][1])), 2) 
                                        cv2.line(frame, (coord[1][0], coord[1][1]), (coord[3][0], coord[3][1]), (0, 255, 0),2)  # Changes line color to green
                                        tim2 = frameTime # Final time
                                        print("Ball Left. Position: "+str(center))
                                        left = True
                                        endPos = center
                                        # calculate the distance traveled by the ball in pixel
                                        a = endPos[0] - startPos[0]
                                        b = endPos[1] - startPos[1]
                                        distanceTraveled = math.sqrt( a*a + b*b )
                                        if not pixelmmratio is None:
                                            # convert the distance traveled to mm using the pixel ratio
                                            distanceTraveledMM = distanceTraveled / pixelmmratio
                                            # take the time diff from ball entered to this frame
                                            timeElapsedSeconds = (tim2 - tim1)
                                            # calculate the speed in MPH
                                            if not timeElapsedSeconds  == 0:
                                                speed = ((distanceTraveledMM / 1000 / 1000) / (timeElapsedSeconds)) * 60 * 60 * 0.621371
                                            # debug out
                                            print("Time Elapsed in Sec: "+str(timeElapsedSeconds))
                                            print("Distance travelled in MM: "+str(distanceTraveledMM))
                                            print("Speed: "+str(speed)+" MPH")
                                            # update the points and tims queues
                                            pts.appendleft(center)
                                            tims.appendleft(frameTime)
                                            break
                                    else:
                                        print("False Exit after the Ball")

                                        # flip image on y-axis for view only





    # loop over the set of tracked points
    if len(pts) != 0 and entered == True:
        for i in range(1, len(pts)):
            
            # if either of the tracked points are None, ignore
            # them
            if pts[i - 1] is None or pts[i] is None:
                continue

            # otherwise, compute the thickness of the line and
            # draw the connecting lines
            thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 1.5)
            #cv2.line(frame, pts[i - 1], pts[i], (0, 0, 150), thickness)
            # print("Point:"+str(pts[i])+"; Timestamp:"+str(tims[i]))


        timeSinceEntered = (frameTime - tim1)
        replaytrigger = tim1

    if left == True:

        # Send Shot Data
        if (tim2 and timeSinceEntered > 0.5 and distanceTraveledMM and timeElapsedSeconds and speed >= 0.5 and speed <= 25):
            print("----- Shot Complete --------")
            print("Time Elapsed in Sec: "+str(timeElapsedSeconds))
            print("Distance travelled in MM: "+str(distanceTraveledMM))
            print("Speed: "+str(speed)+" MPH")

            #     ballSpeed: ballData.BallSpeed,
            #     totalSpin: ballData.TotalSpin,
            totalSpin = 0
            #     hla: ballData.LaunchDirection,
            launchDirection = (GetAngle((startCircle[0],startCircle[1]),endPos)*-1) + hlaAdjust
            print("HLA: Line"+str((startCircle[0],startCircle[1]))+" Angle "+str(launchDirection))
            #Decimal(launchDirection);
            if (launchDirection > -40 and launchDirection < 40):

                lastShotStart = (startCircle[0],startCircle[1])
                lastShotEnd = endPos
                lastShotSpeed = speed
                lastShotHLA = launchDirection
                    
                # Data that we will send in post request.
                data = {"ballData":{"BallSpeed":"%.2f" % speed,"TotalSpin":totalSpin,"LaunchDirection":"%.2f" % launchDirection}}

                # The POST request to our node server
                if args["ballcolor"] == "calibrate":
                    print("calibration mode - shot data not send")
                else:
                    try:
                        res = requests.post('http://127.0.0.1:8888/putting', json=data)
                        res.raise_for_status()
                        # Convert response data to json
                        returned_data = res.json()

                        print(returned_data)
                        result = returned_data['result']
                        print("Response from Node.js:", result)

                    except requests.exceptions.HTTPError as e:  # This is the correct syntax
                        print(e)
                    except requests.exceptions.RequestException as e:  # This is the correct syntax
                        print(e)
            else:
                print("Misread on HLA - Shot not send!!!")    
            if len(pts) > calObjectCount:
                calObjectCount = len(pts)
            print("----- Data reset --------")
            started = False
            entered = False
            left = False
            speed = 0
            timeSinceEntered = 0
            tim1 = 0
            tim2 = 0
            distanceTraveledMM = 0
            timeElapsedSeconds = 0
            startCircle = (0, 0, 0)
            endCircle = (0, 0, 0)
            startPos = (0,0)
            endPos = (0,0)
            startTime = time.time()
            pixelmmratio = 0
            pts.clear()
            tims.clear()

            # Further clearing - startPos, endPos
    else:
        # Send Shot Data
        if (tim1 and timeSinceEntered > 0.5):
            print("----- Data reset --------")
            started = False
            entered = False
            left = False
            replay = False
            speed = 0
            timeSinceEntered = 0
            tim1 = 0
            tim2 = 0
            distanceTraveledMM = 0
            timeElapsedSeconds = 0
            startCircle = (0, 0, 0)
            endCircle = (0, 0, 0)
            startPos = (0,0)
            endPos = (0,0)
            startTime = time.time()
            pixelmmratio = 0
            pts.clear()
            tims.clear()
            
    #cv2.putText(frame,"entered:"+str(entered),(20,180),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))
    #cv2.putText(frame,"FPS:"+str(fps),(20,200),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))

    if not lastShotSpeed == 0:
        cv2.line(frame,(lastShotStart),(lastShotEnd),(0, 255, 255),4,cv2.LINE_AA)      
    
    if started:
        cv2.line(frame,(sx2,startCircle[1]),(sx2+400,startCircle[1]),(255, 255, 255),4,cv2.LINE_AA)
    else:
        cv2.line(frame,(sx2,int(y1+((y2-y1)/2))),(sx2+400,int(y1+((y2-y1)/2))),(255, 255, 255),4,cv2.LINE_AA) 

        # Mark Start Circle
    if started:
        cv2.circle(frame, (startCircle[0],startCircle[1]), startCircle[2],(0, 0, 255), 2)
        cv2.circle(frame, (startCircle[0],startCircle[1]), 5, (0, 0, 255), -1) 

    # Mark Entered Circle
    if entered:
        cv2.circle(frame, (startPos), startCircle[2],(0, 0, 255), 2)
        cv2.circle(frame, (startCircle[0],startCircle[1]), 5, (0, 0, 255), -1)  

    # Mark Exit Circle
    if left:
        cv2.circle(frame, (endPos), startCircle[2],(0, 0, 255), 2)
        cv2.circle(frame, (startCircle[0],startCircle[1]), 5, (0, 0, 255), -1)  

    if flipView:	
       frame = cv2.flip(frame, -1)
                                    
    cv2.putText(frame,"Start Ball",(20,20),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))
    cv2.putText(frame,"x:"+str(startCircle[0]),(20,40),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))
    cv2.putText(frame,"y:"+str(startCircle[1]),(20,60),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))

    if not lastShotSpeed == 0:
        cv2.putText(frame,"Last Shot",(400,40),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255),1)
        cv2.putText(frame,"Ball Speed: %.2f" % lastShotSpeed+" MPH",(400,60),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255),1)
        cv2.putText(frame,"HLA:  %.2f" % lastShotHLA+" Degrees",(400,80),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255),1)
    
    if ballradius == 0:
        cv2.putText(frame,"radius:"+str(startCircle[2]),(20,80),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))
    else:
        cv2.putText(frame,"radius:"+str(startCircle[2])+" fixed at "+str(ballradius),(20,80),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))    

    cv2.putText(frame,"Actual FPS: %.2f" % fps,(200,20),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))
    if overwriteFPS != 0:
        cv2.putText(frame,"Fixed FPS: %.2f" % overwriteFPS,(400,20),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))
    else:
        cv2.putText(frame,"Detected FPS: %.2f" % video_fps[0],(400,20),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255))
    
    #if args.get("video", False):
    #    out1.write(frame)

    if out2:
        try:
            out2.write(origframe)
        except Exception as e:
            print(e)

    # Record Replay1 Video

    if replay == True:
        if replaytrigger != 0:
            timeSinceTriggered = frameTime - replaytrigger
        if timeSinceTriggered < 3:
            replay1queue.appendleft(origframe)
            if replaycam == 1:
                replay2queue.appendleft(origframe2)
        else:
            print("Replay recording stopped")

    try:
        if len(replay1queue) > 0 and replaytrigger != 0:
            replay1frame = replay1queue.pop()
            replay1.write(replay1frame)
            if replaycam == 1:
                replay2frame = replay2queue.pop()
                replay2.write(replay2frame)
    except Exception as e:
        print(e)

    try:
        if replaytrigger != 0 and timeSinceTriggered > 3 :
            while len(replay1queue) > 0:
                replay1frame = replay1queue.pop()
                replay1.write(replay1frame)                
            replay1.release()
            print("Replay 1 released")
            # grab the replay video
            global vs_replay1
            vs_replay1 = cv2.VideoCapture('replay1/Replay1_'+ str(noOfStarts) +'.mp4')
            replayavail = True
            frameskip = 0
            replay1queue.clear()
            if replaycam == 1:
                while len(replay2queue) > 0:
                    replay2frame = replay2queue.pop()
                    replay2.write(replay2frame)             
                replay2.release()
                print("Replay 2 released")
                global vs_replay2
                vs_replay2 = cv2.VideoCapture('replay2/Replay2_'+ str(noOfStarts) +'.mp4')
                replay2queue.clear()
            replaytrigger = 0
            timeSinceTriggered = 0
            replay = False
            print("Replay reset")
    except Exception as e:
        print(e)

    if showreplay == 1 and replayavail == True:
        frameskip = frameskip + 1
        if frameskip%2 == 0:
            # grab the current frame from Replay1
            _, frame_vs_replay1 = vs_replay1.read()
            if frame_vs_replay1 is not None:
                cv2.imshow("Replay1", frame_vs_replay1)
            else:
                print("Reset Replay Video")
                vs_replay1 = cv2.VideoCapture('replay1/Replay1_'+ str(noOfStarts) +'.mp4')
            if replaycam == 1:
                _, frame_vs_replay2 = vs_replay2.read()
                if frame_vs_replay2 is not None:
                    cv2.imshow("Replay2", frame_vs_replay2)
                                
                else:
                    print("Reset Replay Video")
                    vs_replay2 = cv2.VideoCapture('replay2/Replay2_'+ str(noOfStarts) +'.mp4')    
  
    # show main putting window
    
    outputframe = resizeWithAspectRatio(frame, width=int(args["resize"]))
    
    cv2.imshow("Putting View: Press q to exit / a for adv. settings", outputframe)
    
    
    #cv2.moveWindow("Putting View: Press q to exit / a for adv. settings", 20,20)

    # cv2.namedWindow("Putting View: Press q to exit / a for adv. settings",cv2.WINDOW_KEEPRATIO)
    # Resize the Window
    # cv2.resizeWindow("Putting View: Press q to exit / a for adv. settings", 340, 240)
    
    if args.get("debug", False):    
        # flip image on y-axis for view only
        if flipView:	
            mask = cv2.flip(mask, flipView)	
            origframe = cv2.flip(origframe, flipView)
        cv2.imshow("MaskFrame", mask)
        cv2.imshow("Original", origframe)

    
    if replaycam == 1:
        cv2.imshow("Replay Camera", origframe2)
    
    key = cv2.waitKey(1) & 0xFF
    # if the 'q' key is pressed, stop the loop
    if key == ord("q"):
        break
    if key == ord("a"):

        if not a_key_pressed:
            cv2.namedWindow("Advanced Settings")
            if mjpegenabled != 0:
                vs.set(cv2.CAP_PROP_SETTINGS, 37)  
            cv2.resizeWindow("Advanced Settings", 1000, 440)
            cv2.createTrackbar("X Start", "Advanced Settings", int(sx1), 640, setXStart)
            cv2.createTrackbar("X End", "Advanced Settings", int(sx2), 640, setXEnd)
            cv2.createTrackbar("Y Start", "Advanced Settings", int(y1), 460, setYStart)
            cv2.createTrackbar("Y End", "Advanced Settings", int(y2), 460, setYEnd)
            cv2.createTrackbar("Radius", "Advanced Settings", int(ballradius), 50, setBallRadius)
            cv2.createTrackbar("Flip Image", "Advanced Settings", int(flipImage), 1, setFlip)
            cv2.createTrackbar("Flip View", "Advanced Settings", int(flipView), 1, setFlipView)
            cv2.createTrackbar("MJPEG", "Advanced Settings", int(mjpegenabled), 1, setMjpeg)
            cv2.createTrackbar("FPS", "Advanced Settings", int(overwriteFPS), 240, setOverwriteFPS)
            cv2.createTrackbar("Darkness", "Advanced Settings", int(darkness), 255, setDarkness)
            # cv2.createTrackbar("Saturation", "Advanced Settings", int(saturation), 255, setSaturation)
            # cv2.createTrackbar("Exposure", "Advanced Settings", int(exposure), 255, setExposure)
            a_key_pressed = True
        else:
            cv2.destroyWindow("Advanced Settings")

            exposure = vs.get(cv2.CAP_PROP_EXPOSURE)
            saturation = vs.get(cv2.CAP_PROP_SATURATION)
            autowb = vs.get(cv2.CAP_PROP_AUTO_WB)
            whiteBalanceBlue = vs.get(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U)
            whiteBalanceRed = vs.get(cv2.CAP_PROP_WHITE_BALANCE_RED_V)
            brightness = vs.get(cv2.CAP_PROP_BRIGHTNESS)
            contrast = vs.get(cv2.CAP_PROP_CONTRAST)
            hue = vs.get(cv2.CAP_PROP_HUE)
            gain = vs.get(cv2.CAP_PROP_GAIN)
            monochrome = vs.get(cv2.CAP_PROP_MONOCHROME)
            sharpness = vs.get(cv2.CAP_PROP_SHARPNESS)
            autoexposure = vs.get(cv2.CAP_PROP_AUTO_EXPOSURE)
            gamma = vs.get(cv2.CAP_PROP_GAMMA)
            zoom = vs.get(cv2.CAP_PROP_ZOOM)
            focus = vs.get(cv2.CAP_PROP_FOCUS)
            autofocus = vs.get(cv2.CAP_PROP_AUTOFOCUS)


            print("Saving Camera Settings to config.ini for restart")

            parser.set('putting', 'exposure', str(exposure))
            parser.set('putting', 'saturation', str(saturation))
            parser.set('putting', 'autowb', str(autowb))
            parser.set('putting', 'whiteBalanceBlue', str(whiteBalanceBlue))
            parser.set('putting', 'whiteBalanceRed', str(whiteBalanceRed))
            parser.set('putting', 'brightness', str(brightness))
            parser.set('putting', 'contrast', str(contrast))
            parser.set('putting', 'hue', str(hue))
            parser.set('putting', 'gain', str(gain))
            parser.set('putting', 'monochrome', str(monochrome))
            parser.set('putting', 'sharpness', str(sharpness))
            parser.set('putting', 'autoexposure', str(autoexposure))
            parser.set('putting', 'gamma', str(gamma))
            parser.set('putting', 'zoom', str(zoom))
            parser.set('putting', 'focus', str(focus))
            parser.set('putting', 'autofocus', str(autofocus))

            parser.write(open(CFG_FILE, "w"))

            a_key_pressed = False

    if key == ord("d"):
        if not d_key_pressed:
            args["debug"] = 1
            myColorFinder = ColorFinder(True)
            myColorFinder.setTrackbarValues(hsvVals)
            d_key_pressed = True
        else:
            args["debug"] = 0            
            myColorFinder = ColorFinder(False)
            cv2.destroyWindow("Original")
            cv2.destroyWindow("MaskFrame")
            cv2.destroyWindow("TrackBars")
            d_key_pressed = False

    if actualFPS > 1:
        grayPreviousFrame = cv2.cvtColor(previousFrame, cv2.COLOR_BGR2GRAY)
        grayOrigframe = cv2.cvtColor(origframe, cv2.COLOR_BGR2GRAY)
        changedFrame = cv2.compare(grayPreviousFrame, grayOrigframe,cv2.CMP_NE)
        nz = cv2.countNonZero(changedFrame)
        #print(nz)
        if nz == 0:
            actualFPS = actualFPS - 1
            fpsqueue.pop()
    previousFrame = origframe.copy()


# close all windows
vs.release()
if replaycam == 1:
    vs2.release()
cv2.destroyAllWindows()

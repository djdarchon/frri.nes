#!/usr/bin/python3
# system
import os, sys, time, pathlib, socket, errno
from threading import Thread
from queue import Queue
from datetime import datetime
import urllib.request

# proprietary
import pygame
import tweepy

# user
from secrets import Secrets

#---
# Global Constants
class FRRIConst:
    CONST_PATH_ROOT = pathlib.Path(__file__).parent.resolve()
    CONST_PATH_ASSETS = os.path.join(CONST_PATH_ROOT, "assets")

    CONST_FPS = 60.

#---
# Logic
class FRRIUtil:
    def Print(*args, **kwargs):
        print(*args, file=sys.stdout, **kwargs)

    def Error(*args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)

class FRRINet:
    def __init(self):
        pass

    def Begin(self):
        pass

    def End(self):
        pass

    def InternetActive(self, host="8.8.8.8", port=53, timeout=5):
        """
        Host: 8.8.8.8 (google-public-dns-a.google.com)
        OpenPort: 53/tcp
        Service: domain (DNS/TCP)
        """
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except socket.error as ex:
            FRRIUtil.Error(ex)
            return False

    def Serialize(message):
        return message.encode('utf-8')

class FRRITwitter:
    def __init__(self):
        pass

    def Begin(self):
        FRRIUtil.Print("Logging into Twitter...")
        self.client = tweepy.Client(consumer_key = Secrets.API_KEY,
                                    consumer_secret = Secrets.API_SECRET,
                                    access_token = Secrets.OAUTH_TOKEN,
                                    access_token_secret = Secrets.OAUTH_TOKEN_SECRET)
        FRRIUtil.Print("Logged in successfully!")

    def End(self):
        pass

    def Tweet(self):
        #message = "[Furmeet Roaming Relay Interface is now Online]" 
        #response = client.create_tweet(text=message)
        pass

class FRRIControllerState:
    def __init__(self, new_state):
        self.state = new_state

    def __str__(self):
        return str(self.state)

    def Connected(self):
        return not (self.A() & self.B() & self.Start() & self.Select() & self.Up() & self.Down() & self.Left() & self.Right())

    def A(self):
        return self.state['A']

    def B(self):
        return self.state['B']

    def Start(self):
        return self.state['START']

    def Select(self):
        return self.state['SELECT']

    def Up(self):
        return self.state['UP']

    def Down(self):
        return self.state['DOWN']

    def Left(self):
        return self.state['LEFT']

    def Right(self):
        return self.state['RIGHT']

class FRRIControllerManager:
    CONST_CTRL_FILE = "/proc/nes_ctrl"
    CONST_CTRL_FILE_BYTES = 4

    def __init__(self):
        pass

    def Begin(self):
        self.proc_file = os.open(FRRIControllerManager.CONST_CTRL_FILE, os.O_RDONLY)

    def End(self):
        os.close(self.proc_file)

    def InterpretController(self, value):
        state = {}
        value = int(value, 16)

        state['A'] = int(value & 0x80) != 0
        state['B'] = int(value & 0x40) != 0
        state['START'] = int(value & 0x20) != 0
        state['SELECT'] = int(value & 0x10) != 0
        state['UP'] = int(value & 0x08) != 0
        state['DOWN'] = int(value & 0x04) != 0
        state['LEFT'] = int(value & 0x02) != 0
        state['RIGHT'] = int(value & 0x01) != 0

        return state

    def InterpretControllers(self, value):
        return [ FRRIControllerState(self.InterpretController(value[0:2])), 
                FRRIControllerState(self.InterpretController(value[2:4]))]

    def GetControllers(self):
        return self.InterpretControllers((os.read(self.proc_file, FRRIControllerManager.CONST_CTRL_FILE_BYTES)).decode().strip())

class FRRISpeaker:
    CONST_PATH_SOUND = os.path.join(FRRIConst.CONST_PATH_ASSETS, "sound")
    CONST_SOUND_WELCOME = os.path.join(CONST_PATH_SOUND, "welcome.wav")

    def __init__(self):
        pass

    def Begin(self):
        pygame.mixer.init()
        self.sound_welcome = pygame.mixer.Sound(FRRISpeaker.CONST_SOUND_WELCOME)
        pygame.mixer.Sound.play(self.sound_welcome)

    def End(self):
        pass

    def PlaySound(self, filename):
        pygame.mixer.Sound.play(pygame.mixer.Sound(os.path.join(FRRISpeaker.CONST_PATH_SOUND, filename)))

class FRRICamera:
    CONST_WEBCAM_URL = "192.168.8.80:8080/photo.jpg"
    CONST_PATH_TEMP = os.path.join(FRRIConst.CONST_PATH_ASSETS, "temp")
    CONST_FILENAME_PHOTO = "photo.jpg"

    def __init__(self):
        pass

    def Begin(self):
        pass

    def End(self):
        pass

    def GetPhoto(self):
        return urllib.request.urlretrieve(CONST_WEBCAM_URL, os.path.join(CONST_PATH_TEMP, CONST_FILENAME_PHOTO))

#---
# Script
frri_net = FRRINet()
frri_net.Begin()

FRRIUtil.Print("Testing network connection...")
if (not frri_net.InternetActive()):
    FRRIUtil.Error("Not Good!")
    sys.exit()

frri_twitter = FRRITwitter()
frri_twitter.Begin()

frri_controller_manager = FRRIControllerManager()
frri_controller_manager.Begin()

frri_speaker = FRRISpeaker()
frri_speaker.Begin()

previous_state = None

while(True):
    time.sleep(1./FRRIConst.CONST_FPS)
    next_state = frri_controller_manager.GetControllers()

    if previous_state is not None:
        if not previous_state[0].Connected() and next_state[0].Connected():
            frri_speaker.PlaySound("plugged.wav")
            FRRIUtil.Print("P1 connected")
        if previous_state[0].Connected() and not next_state[0].Connected():
            frri_speaker.PlaySound("unplugged.wav")
            FRRIUtil.Print("P1 discconnected")

    previous_state = next_state

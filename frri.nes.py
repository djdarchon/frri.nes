#!/usr/bin/python3
# system
import os, sys, time, pathlib, socket, errno
from threading import Thread
from queue import Queue
from datetime import datetime
import urllib.request
import configparser

# proprietary
import pygame
import pygame._sdl2.audio as sdl2_audio
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

class FRRIConfig:
    CONST_CONFIG_FILE = "frri.cfg"

    def __init__(self):
        pass

    def Begin(self):
        self.config = configparser.ConfigParser()

        if not os.path.isfile(FRRIConfig.CONST_CONFIG_FILE):
            FRRIUtil.Print("Writing out new config file...")
            self.config['AUDIO'] = {'MUTED' : 'False',
                                    'WELCOME' : 'True',
                                    'DEVICENAME' : 'USB2.0 Device, USB Audio'}
            self.config['TWITTER'] = {'ENABLED' : 'False'}
            self.config['MAIN'] = {'ANNOUNCE_COUNTDOWN' : 'True'}
            self.WriteConfig()
            FRRIUtil.Print("Done")

        FRRIUtil.Print("Reading config file...")
        self.config.read(FRRIConfig.CONST_CONFIG_FILE)
        FRRIUtil.Print("Done")

    def End(self):
        self.WriteConfig()

    def GetConfig(self):
        return self.config

    def SetConfig(self, section, field, value):
        self.config.set(section, field, str(value))
        self.WriteConfig()

    def WriteConfig(self):
        with open(FRRIConfig.CONST_CONFIG_FILE, 'w') as configfile:
            self.config.write(configfile)

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
        global frri_config
        self.client = None
        self.api = None
        self.enabled = frri_config.GetConfig().getboolean('TWITTER', 'ENABLED')

        if self.enabled:
            self.TwitterConnect()
        else:
            FRRIUtil.Print("Not logging into Twitter - not Enabled in config file")

    def End(self):
        pass

    def TwitterConnect(self):
        FRRIUtil.Print("Logging into Twitter...")
        self.client = tweepy.Client(consumer_key = Secrets.API_KEY,
                                    consumer_secret = Secrets.API_SECRET,
                                    access_token = Secrets.OAUTH_TOKEN,
                                    access_token_secret = Secrets.OAUTH_TOKEN_SECRET)

        auth = tweepy.OAuthHandler(Secrets.API_KEY,
                                    Secrets.API_SECRET)

        auth.set_access_token(Secrets.OAUTH_TOKEN,
                                Secrets.OAUTH_TOKEN_SECRET)

        self.api = tweepy.API(auth)

        FRRIUtil.Print("Logged in successfully!")

    def TwitterDisconnect(self):
        self.client = None
        self.api = None

    def GetTwitterConnected(self):
        return (self.client is not None and self.api is not None)

    def ToggleEnabled(self):
        global frri_config
        self.enabled = not self.enabled
        if self.enabled:
            self.TwitterConnect()
        else:
            self.TwitterDisconnect()
        frri_config.SetConfig('TWITTER', 'ENABLED', self.enabled)

    def GetEnabled(self):
        return self.enabled

    def Tweet(self, message, media_str=None):
        if self.enabled:
            if media_str is not None:
                media = self.api.media_upload(media_str)
                try:
                    response = self.client.create_tweet(text=message, media_ids=[media.media_id])
                except Exception as e:
                    FRRIUtil.Error("Caught exception during Tweet: "+str(e))
                    return False
                FRRIUtil.Print("Tweeted: "+message+" along with photo at "+media_str+" !!!")
                return True
            else:
                FRRIUtil.Error("Unable to Tweet without an image; media not supplied to function call")
                return False
        else:
            FRRIUtil.Error("Attempted to Tweet while Twitter is disabled (see config file)")
            return False

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
        state['SELECT'] = int(value & 0x20) != 0
        state['START'] = int(value & 0x10) != 0
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
    CONST_SOUND_SPEECH = os.path.join(CONST_PATH_SOUND, "speech.wav")

    def __init__(self):
        pass

    def Begin(self):
        global frri_config
        pygame.mixer.init(devicename=frri_config.GetConfig().get('AUDIO', 'DEVICENAME'))
        self.muted = frri_config.GetConfig().getboolean('AUDIO', 'MUTED')
        if frri_config.GetConfig().getboolean('AUDIO', 'WELCOME'):
            self.PlaySound(FRRISpeaker.CONST_SOUND_WELCOME, True)
            self.Wait()
            self.TTS("System Online!")

    def End(self):
        pass

    def ToggleMuted(self):
        global frri_config
        self.muted = not self.muted
        frri_config.SetConfig('AUDIO', 'MUTED', self.muted)

    def GetMuted(self):
        return self.muted

    def PlaySound(self, filename, mute_override=False):
        if (not self.GetMuted()) or mute_override:
            pygame.mixer.Sound.play(pygame.mixer.Sound(os.path.join(FRRISpeaker.CONST_PATH_SOUND, filename)))

    def Wait(self):
        while(pygame.mixer.get_busy()):
            time.sleep(0.1)

    def TTS(self, text, mute_override=False):
        command = "espeak --stdout -s 155 -a 200 \""+text+"\" > "+FRRISpeaker.CONST_SOUND_SPEECH
        os.system(command)
        self.PlaySound(FRRISpeaker.CONST_SOUND_SPEECH, mute_override)
        try:
            os.remove(FRRISpeaker.CONST_SOUND_SPEECH)
        except Exception as e:
            FRRIUtil.Error("Unable to delete speech file")

class FRRICamera:
    CONST_WEBCAM_URL = "http://192.168.8.80:8080/photo.jpg"
    CONST_PATH_TEMP = os.path.join(FRRIConst.CONST_PATH_ASSETS, "temp")
    CONST_FILENAME_PHOTO = "photo.jpg"

    def __init__(self):
        pass

    def Begin(self):
        pass

    def End(self):
        pass

    def GetPhoto(self):
        try:
            urllib.request.urlretrieve(FRRICamera.CONST_WEBCAM_URL, os.path.join(FRRICamera.CONST_PATH_TEMP, FRRICamera.CONST_FILENAME_PHOTO))
            if not os.path.isfile(os.path.join(FRRICamera.CONST_PATH_TEMP, FRRICamera.CONST_FILENAME_PHOTO)):
                raise Exception()
        except Exception as e:
            FRRIUtil.Error("Unable to GetPhoto()")
            return None
        return os.path.join(FRRICamera.CONST_PATH_TEMP, FRRICamera.CONST_FILENAME_PHOTO)

    def DeletePhoto(self):
        try:
            os.remove(os.path.join(FRRICamera.CONST_PATH_TEMP, FRRICamera.CONST_FILENAME_PHOTO))
        except Exception as e:
            FRRIUtil.Error("Unable to DeletePhoto()")
            return False
        return True


#---
# Script
FRRIUtil.Print("Config Begin")
frri_config = FRRIConfig()
frri_config.Begin()

FRRIUtil.Print("Net Begin")
frri_net = FRRINet()
frri_net.Begin()

FRRIUtil.Print("Testing network connection...")
connected = False
while not connected:
    if (not frri_net.InternetActive()):
        time.sleep(3)
        FRRIUtil.Error("Waiting...")
    else:
        FRRIUtil.Print("Connection successful")
        connected = True

FRRIUtil.Print("Twitter Begin")
frri_twitter = FRRITwitter()
frri_twitter.Begin()

FRRIUtil.Print("Controller Begin")
frri_controller_manager = FRRIControllerManager()
frri_controller_manager.Begin()

FRRIUtil.Print("Speaker Begin")
frri_speaker = FRRISpeaker()
frri_speaker.Begin()

FRRIUtil.Print("Camera Begin")
frri_camera = FRRICamera()
frri_camera.Begin()

previous_state = None

last_press = datetime.now()
captured = False

while(True):
    time.sleep(1./FRRIConst.CONST_FPS)

    now = datetime.now()

    current_state = frri_controller_manager.GetControllers()
    if previous_state is None:
        previous_state = current_state

    # controller disconnect and connet
    if previous_state is not None:
        if not previous_state[0].Connected() and current_state[0].Connected():
            frri_speaker.PlaySound("plugged.wav")
            time.sleep(0.5)
            frri_speaker.TTS("Player one connected")
            FRRIUtil.Print("P1 connected")
        if previous_state[0].Connected() and not current_state[0].Connected():
            frri_speaker.PlaySound("unplugged.wav")
            time.sleep(0.5)
            frri_speaker.TTS("Player one disconnected")
            FRRIUtil.Print("P1 discconnected")

    # user configuration
    if previous_state[0].Connected() and current_state[0].Connected():
        # mute control

        if current_state[0].Select():
            # SELECT + DOWN: mute toggle
            if (not previous_state[0].Down()) and current_state[0].Down():
                frri_speaker.ToggleMuted()
                if frri_speaker.GetMuted():
                    frri_speaker.TTS("Countdown Muted", True)
                    frri_speaker.Wait()
                else:
                    frri_speaker.TTS("Countdown Unmuted", True)
                    frri_speaker.Wait()

            # SELECT + UP: twitter toggle
            if (not previous_state[0].Up()) and current_state[0].Up():
                frri_twitter.ToggleEnabled()
                if frri_twitter.GetEnabled():
                    temp = "Twitter enabled "
                    if frri_twitter.GetTwitterConnected():
                        temp += "and connected"
                    else:
                        temp += "but failed to connect"
                    frri_speaker.TTS(temp, True)
                    frri_speaker.Wait()
                else:
                    frri_speaker.TTS("Twitter Disabled", True)
                    frri_speaker.Wait()

            # SELECT + START: config report
            if (not previous_state[0].Start()) and current_state[0].Start():
                frri_speaker.TTS("System Configuration", True)
                frri_speaker.Wait()
                if frri_speaker.GetMuted():
                    frri_speaker.TTS("Countdown is Muted", True)
                    frri_speaker.Wait()
                else:
                    frri_speaker.TTS("Countdown is Unmuted", True)
                    frri_speaker.Wait()
                if frri_twitter.GetEnabled():
                    temp = "Twitter is Enabled "
                    if frri_twitter.GetTwitterConnected():
                        temp += "and connected"
                    else:
                        temp += "but not connected"
                    frri_speaker.TTS(temp, True)
                    frri_speaker.Wait()
                else:
                    frri_speaker.TTS("Twitter is Disabled", True)
                    frri_speaker.Wait()

    # if controller is plugged in and we know the last state
    # and they're pressing A now, process
    if not current_state[0].Connected() or not previous_state[0].A():
        last_press = datetime.now()
        last_tts = 999
        captured = False
    elif not captured:
        delta = (now - last_press).total_seconds()

        if delta > 4.2:
            FRRIUtil.Print("Taking photo!")
            photo = frri_camera.GetPhoto()
            if (photo is not None) and frri_twitter.Tweet("Fuzzy greetings from #FRRI_nes!", photo):
                frri_speaker.PlaySound("photosnap.wav")
                frri_camera.DeletePhoto()
            else:
                frri_speaker.PlaySound("photoerror.wav")
            captured = True
        if delta > 3.2:
            if last_tts != 0:
                frri_speaker.TTS("LET'S GO!")
                last_tts = 0
        elif delta > 2.2:
            if last_tts != 1:
                frri_speaker.TTS("ONE!")
                last_tts = 1
        elif delta > 1.2:
            if last_tts != 2:
                frri_speaker.TTS("TWO!")
                last_tts = 2
        elif delta > 0.2:
            if last_tts != 3:
                frri_speaker.TTS("THREE!")
                last_tts = 3

    previous_state = current_state


FRRIUtil.Print("Camera End")
frri_camera.End()
FRRIUtil.Print("Speaker End")
frri_speaker.End()
FRRIUtil.Print("Controller End")
frri_controller_manager.End()
FRRIUtil.Print("Twitter End")
frri_twitter.End()
FRRIUtil.Print("Net End")
frri_net.End()
FRRIUtil.Print("Config End")
frri_config.End()

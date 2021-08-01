"""
    POCCA GIF
"""
import sys
sys.path.append("../")
import time
import configparser
import os
import signal

from pocca.display.interface import Interface
from pocca.vision.camera import Camera #Pi Camera Manager
from pocca.vision.effects import Effects # OpenCV Effects
from pocca.vision.convert import Convert # FFMPEG Conversion
from pocca.controls.buttons import Buttons # Joystick / Buttons

# Detect a CTRL-C abord program interrupt, and gracefully exit the application
def sigint_handler(signal, frame):
    print(TEXT.DEV_STOP)
    going = False
    sys.exit(0)

# Enable abord program interrupt
signal.signal(signal.SIGINT, sigint_handler)

settings = configparser.ConfigParser()
settings.read("/media/usb/pocca.ini")
if settings["APPLICATION"]["lang"]:
    from pocca.localization.fr import TEXT
else:
    from pocca.localization.en import TEXT
path_images = settings["FOLDERS"]["pictures"]
path_temp = settings["FOLDERS"]["temp"]

print("\033c", end="") # Clear Terminal
print(" ~~~~~~ 📷 POCCA GIF 📷 ~~~~~~")
print(TEXT.LOCK_WARNING)

interface = Interface(settings)
camera = Camera(settings, TEXT)
effects = Effects()
convert = Convert(TEXT)
buttons = Buttons(TEXT)

interface.start()
camera.start()
camera.clear_temp() # Remove Previous Images

going = True
start_timer = 0
countdown = 0
# Enable Screen
tft_enable = True

print (" ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

gif_rate = 1 / float(settings["CAMERA"]["gif_rate"])
gif_nb = int(settings["CAMERA"]["gif_images"])

while going:
    # Viewfinder (Live preview)
    if interface.state == "viewfinder":
        try:
            # Capture frame continously
            for frame in camera.stream.capture_continuous(camera.rawCapture, format='bgr', use_video_port=True):
                # Get array of RGB from images
                frame = frame.array

                # Effects
                if(effects.id == effects.EFFECT_CONTOURS):
                    # Canny Detection Effects (contours)
                    frame = effects.canny_edge(frame)
                    frame = effects.color_change(frame, (0,0,255)) # RED

                # Resize image to screen resolution
                frame_resize = camera.resize(frame, (interface.resolution))
                # Copy image to screen
                interface.to_screen(frame_resize)
                interface.top_left(interface.state)
                interface.top_right("gif")

                if(countdown > 0):
                    interface.bottom(str(countdown))

                if interface.state == "countdown" :
                    if time.time() > (start_timer + 1):
                        print(TEXT.TIMER + " : " + str(countdown))
                        if countdown > 0:
                            countdown = countdown - 1
                        else:
                            interface.state = "record"
                        start_timer = time.time()

                # If we are in record mode
                if interface.state == "record":
                        # Take a timelapse
                        # gif_nb : number of pictures taken
                        # gif_rate : delay between each picture
                        if time.time() > (start_timer + gif_rate):
                            if(camera.count() < gif_nb):
                                camera.save(frame, path_temp, "gif")
                            else:
                                interface.state = "preview"
                                print(TEXT.TIMELAPSE_END)
                                camera.rawCapture.truncate(0)
                                # Truncate camera raw capture (need to avoid crash)
                                break

                            # Reset timer (to take another pictures)
                            start_timer = time.time()

                # Check if a button is pressed
                pressed = buttons.check()


                # If the button is pressed
                if pressed == buttons.BTN: # or  web_action == 1:
                    start_timer = time.time()
                    countdown = 3
                    interface.state = "countdown"
                elif pressed == buttons.BTN2:
                    if(effects.id == effects.EFFECT_NONE):
                        effects.id = effects.EFFECT_CONTOURS
                    else:
                        effects.id = effects.EFFECT_NONE
                camera.rawCapture.truncate(0)

        # If the video capture failed, crash gracefully
        except Exception as error:
            raise # Add this to check error
            print("❌ ➡️" + str(error))
            going = False

    # Preview mode (show timelapse/panorama)
    if interface.state == "preview":
        pressed = buttons.check()

        images = os.listdir(path_temp)
        sorted(images)
        # print(images)
        counter = 0
        preview = True
        if(len(images) != 0):
            while(preview):
                pressed = buttons.check()
                if time.time() > (start_timer + gif_rate):
                    interface.load(path_temp + "/" + images[counter])
                    start_timer = time.time()

                    if counter < len(images) - 1:
                        counter = counter + 1
                    else:
                        counter = 0
                    # If a button is pressed, convert images to gif
                if pressed != buttons.NOACTION:
                    interface.image("saving" , 0, 0)
                    error = convert.gif(path_temp, path_images)
                    if error == 0:
                        print(TEXT.TIMELAPSE_CONVERTED)
                        camera.clear_temp() # Delete old timelapse
                    else:
                        print(TEXT.TIMELAPSE_CONVERT_FAILED)
                    preview = False
                    interface.state = "viewfinder"
                    break
                interface.top_left(interface.state)
                interface.top_right("gif")

            camera.rawCapture.truncate(0)

# If we exit the application, we go here
print(TEXT.SHUTDOWN_APP)
camera.stop()
interface.stop()
sys.exit(1)

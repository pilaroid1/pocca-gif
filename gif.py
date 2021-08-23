"""
    POCCA GIF
"""
import sys
sys.path.append("/media/usb/apps")
import time
import os
from pocca.display.interface import Interface
from pocca.display.countdown import Countdown
from pocca.vision.camera import Camera #Pi Camera Manager
from pocca.vision.effects import Effects # OpenCV Effects
from pocca.vision.convert import Convert # FFMPEG Conversion
from pocca.controls.buttons import Buttons # Joystick / Buttons
from pocca.utils.app import App # Application Manager (Settings / Secrets / utilities)

app = App()
app.clear_terminal()
print(app.TEXT.LOCK_WARNING)
print(" ~~~~~~ 📷 Pilaroid GIF 📷  ~~~~~~")
print(" https://github.com/usini/pocca-gif")

interface = Interface(app.settings, app.system)
countdown = Countdown(app.settings, app.TEXT)
effects = Effects(app.settings)
convert = Convert(app.TEXT)
buttons = Buttons(app.TEXT)

camera = Camera(app.settings, app.TEXT, app.camera_resolution)
camera.clear_temp() # Remove Previous Images

# If we exit the application, we go here
def stop(signal, frame):
    print(app.TEXT.SHUTDOWN_APP)
    app.running = False
app.stop_function(stop)

gif_rate = 1 / float(app.settings["APPLICATION"]["gif_rate"])
gif_fps = app.settings["APPLICATION"]["gif_rate"]
gif_nb = int(app.settings["APPLICATION"]["gif_images"])
start_timer = 0
color_id = 0


def run():
    # Viewfinder (Live preview)
    if interface.state == "viewfinder":
        # Capture frame continously
        for frame in camera.stream.capture_continuous(camera.rawCapture, format='bgr', use_video_port=True):
            # Get array of RGB from images
            frame = frame.array

            if not app.running:
                sys.exit(0)

            # Effects
            if(effects.id == effects.CONTOURS):
                # Canny Detection Effects (contours)
                frame = effects.canny_edge(frame)
                frame = effects.color_change(frame) # RED

            # Resize image to screen resolution
            frame_resize = camera.resize(frame, (interface.resolution))
            # Copy image to screen
            interface.to_screen(frame_resize)
            interface.top_left(interface.state)
            interface.top_right("gif")

            if countdown.running():
                if countdown.started:
                    interface.bottom(str(countdown.current()))
                else:
                    interface.state = "record"

            interface.update()

            # If we are in record mode
            if interface.state == "record":
                    # Take a timelapse
                    # gif_nb : number of pictures taken
                    # gif_rate : delay between each picture
                    if time.time() > (start_timer + gif_rate):
                        if(camera.count() < gif_nb):
                            camera.save(frame, app.path["temp"] + "/images/", "gif")
                        else:
                            interface.image("saving" , 0, 0)
                            interface.update()
                            error, filename = convert.gif(app.path["temp"] + "/images/", app.path["images"], gif_fps)
                            if error == 0:
                                print(app.TEXT.TIMELAPSE_CONVERTED)
                                camera.save_timestamp(filename)
                            else:
                                print(app.TEXT.TIMELAPSE_CONVERT_FAILED)
                            interface.state = "preview"
                            print(app.TEXT.TIMELAPSE_END)

            camera.refresh()
            controls()

def controls():
    global color_id
    # Check if a button is pressed
    pressed = buttons.check()

    if interface.state == "viewfinder":
        # If the button is pressed
        if pressed == buttons.BTN: # or  web_action == 1:
            if not countdown.running():
                countdown.start()
        elif pressed == buttons.BTN2:
            if color_id < 6:
                effects.id = effects.CONTOURS
                color_id += 1
                if color_id == 1:
                    effects.color_lines = (0,0,1)
                    effects.color_background = (0,0,0)
                elif color_id == 2:
                    effects.color_lines = (0,1,0)
                    effects.color_background = (0,0,0)
                elif color_id == 3:
                    effects.color_lines = (1,0,0)
                    effects.color_background = (0,0,0)
                elif color_id == 4:
                    effects.color_lines = (1,1,1)
                    effects.color_background = (0,0,255)
                elif color_id == 5:
                    effects.color_lines = (1,1,1)
                    effects.color_background = (0,255,0)
                elif color_id == 6:
                    effects.color_lines = (1,1,1)
                    effects.color_background = (255,0,0)
            else:
                color_id = 0
                effects.id = effects.NO
            print(color_id)
            print(effects.name)

   # Preview mode (show timelapse/panorama)
    if interface.state == "preview":
        images = os.listdir(app.path["temp"] + "/images/")
        sorted(images)
        # print(images)
        counter = 0
        preview = True
        start_timer = 0
        if(len(images) != 0):
            while(preview):
                pressed = buttons.check()
                if time.time() > (start_timer + gif_rate):
                    interface.load(app.path["temp"] + "/images/" + images[counter])
                    start_timer = time.time()

                    if counter < len(images) - 1:
                        counter = counter + 1
                    else:
                        counter = 0
                    # If a button is pressed, convert images to gif
                if pressed != buttons.NOACTION:
                    camera.clear_temp() # Delete old timelapse
                    preview = False
                    interface.state = "viewfinder"
                interface.top_left(interface.state)
                interface.top_right("gif")
                interface.update()
                if not app.running:
                    sys.exit(0)

            camera.refresh()


run()

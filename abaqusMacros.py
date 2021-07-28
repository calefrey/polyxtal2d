# -*- coding: mbcs -*-
# Do not delete the following import lines
# Save in your working directory or in your home directory
from abaqus import *
from abaqusConstants import *
import __main__
import os


def frame2imgs():
    """
    Steps through the frames and saves them as images
    Need to create the images dir first
    """
    os.system("mkdir images")  # make images directory
    odb = session.odbs.values()[0]
    viewport = session.viewports["Viewport: 1"]
    num_frames = len(odb.steps["Step-1"].frames)
    for frame in range(num_frames):
        viewport.odbDisplay.setFrame(step=0, frame=frame)
        filename = "images/frame{}.png".format(frame)
        session.printToFile(fileName=filename, format=PNG)

    # if you have ffmpeg installed make it into an animation
    os.chdir("images")
    result = os.popen("ffmpeg -i frame%01d.png animation.mp4 -y")
    if result.close():  # ffmpeg error
        print(result.read().strip())

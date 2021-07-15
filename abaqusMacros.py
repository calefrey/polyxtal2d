# -*- coding: mbcs -*-
# Do not delete the following import lines
# Save in your working directory or in your home directory
from abaqus import *
from abaqusConstants import *
import __main__


def frame2imgs():
    """
    Steps through the frames and saves them as images
    Need to create the images dir first
    """
    odb = session.odbs.values()[0]
    viewport = session.viewports["Viewport: 1"]
    num_frames = len(odb.steps["Step-1"].frames)
    for frame in range(num_frames):
        viewport.odbDisplay.setFrame(step=0, frame=frame)
        filename = "images/frame{}.png".format(frame)
        session.printToFile(fileName=filename, format=PNG)

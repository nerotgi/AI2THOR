import numpy as np
import time
from matplotlib import pyplot as plt
import pandas as pd
import random
import openpyxl
import conToObs
import obsToPath
import pathToNav

def robo_thor_controller(pack, controller, reachablePositions, home_pos):
    iTime = 30
    iDist = 0
    start_time = time.time()
    nObsNewClass = [0 for i in range(len(pack[3]))]
    moveHist = []
    path1 = [] # previous path
    path2 = [] # current path
    fig, ac = plt.subplots()
    if pack[7] == 'grocery':
        xTrainWeights = [-20 for i in range(81)]
    elif pack[7] == 'cifar':
        xTrainWeights = [-20 for i in range(100)]
    else:
        print("pDataName not recognized.")
    homeFlag = 0
    while True:
        # Time check
        current_time = time.time()
        elapsed_time = current_time - start_time
        if elapsed_time > iTime:
            print("Finished iterating in: " + str(int(elapsed_time)) + " seconds")
            break

        # position = [controller.last_event.metadata["agent"]["position"]['x'],
        #             controller.last_event.metadata["agent"]["position"]['z'],
        #             controller.last_event.metadata["agent"]["rotation"]["y"]]

        # Looking around
        controller, step, blockMatrix, objects = conToObs.con_to_obs(controller)
        # Creating potential field and getting path
        controller, path, homeFlag, obs, trainClass = obsToPath.obs_to_path(controller, blockMatrix, home_pos,
                                                                           xTrainWeights, (0, 0), homeFlag,
                                                                           pack[7], moveHist, reachablePositions)
        for i in range(len(xTrainWeights)):
            if trainClass == i:
                nObsNewClass[i] += 1
                break

        # Randomizing the next step if previous path is the same as the new path

        path1 = path2
        path2 = path
        if path2 == path1:
            # Same two paths in a row detected...randomizing the next step.
            randDir = random.randint(0,4)
            if randDir == 0:
                controller.step(
                    action="MoveAhead",
                    moveMagnitude=step*5
                )
            elif randDir == 1:
                controller.step(
                    action="RotateLeft",
                    degrees=90
                )
                controller.step(
                    action="MoveAhead",
                    moveMagnitude=step*5
                )
            elif randDir == 2:
                controller.step(
                    action="RotateLeft",
                    degrees=180
                )
                controller.step(
                    action="MoveAhead",
                    moveMagnitude=step*5
                )
            elif randDir == 3:
                controller.step(
                    action="RotateLeft",
                    degrees=270
                )
                controller.step(
                    action="MoveAhead",
                    moveMagnitude=step*5
                )
        print(step)

        # Moving the agent according to the potential field
        controller = pathToNav.path_to_nav(controller, step, path, moveHist)
        path = 0
        df1 = pd.DataFrame(moveHist)
        df1.to_excel(excel_writer="~/Desktop/temp/moveHist.xlsx")
        iDist = iDist + step

    return [controller.last_event.metadata["agent"]["position"]['x'],
            controller.last_event.metadata["agent"]["position"]['y'],
            controller.last_event.metadata["agent"]["position"]['z']], iTime, iDist, iTime, nObsNewClass
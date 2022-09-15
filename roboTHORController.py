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
    iTime = 120
    iDist = 0
    nObsNewClass = [0 for i in range(81)]
    start_time = time.time()
    moveHist = []
    print(controller.last_event.metadata["agent"]["position"]["x"])
    fig, ac = plt.subplots()
    while True:
        current_time = time.time()
        elapsed_time = current_time - start_time
        if elapsed_time > iTime:
            print("Finished iterating in: " + str(int(elapsed_time)) + " seconds")
            break

        position = [controller.last_event.metadata["agent"]["position"]['x'],
                    controller.last_event.metadata["agent"]["position"]['z'],
                    controller.last_event.metadata["agent"]["rotation"]["y"]]

        if pack[3] == 'grocery':
            xTrainWeights = [-20 for i in range(81)]
        else:
            xTrainWeights = [-20 for i in range(100)]
        homeFlag = 0

        path1 = []
        path2 = []
        controller, step, blockMatrix, objects = conToObs.con_to_obs(controller)
        controller, path, homeFlag, obs, trainClass = obsToPath.obs_to_path(controller, blockMatrix, home_pos,
                                                                           xTrainWeights, (0, 0), homeFlag,
                                                                           pack[7], moveHist, reachablePositions)
        path2 = path1
        path1 = path
        if path2 == path1:
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
        for i in range(81):
            if trainClass == i:
                nObsNewClass[i] += 1
                trainClass = -1
                break

        controller, circle = pathToNav.path_to_nav(controller, step, path, moveHist)
        df1 = pd.DataFrame(moveHist)
        df1.to_excel(excel_writer="~/Desktop/temp/moveHist.xlsx")
        iDist = iDist + step

    return [controller.last_event.metadata["agent"]["position"]['x'],
            controller.last_event.metadata["agent"]["position"]['y'],
            controller.last_event.metadata["agent"]["position"]['z']], iTime, iDist, iTime, nObsNewClass
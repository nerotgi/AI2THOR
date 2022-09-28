import getBlock
from matplotlib import pyplot as plt
import pandas as pd

def con_to_obs(controller):

    objects = []
    # Getting all objects in view
    i = 0
    while i in range(4):
        # seg_frame = controller.last_event.frame
        # dist_frame = controller.last_event.depth_frame
        # plt.imshow(seg_frame, interpolation='nearest')
        # plt.show()
        # plt.imshow(dist_frame, interpolation='nearest')
        # plt.show()
        for obj in controller.last_event.metadata["objects"]:
            if obj["visible"] == 1:
                objects.append(obj)

        controller.step(action="RotateRight")
        i = i + 1

    # Sorting the dictionary of all objects in view
    obj = []
    for item in objects:
        if item not in obj:
            obj.append([item['name'], item['objectType'], item['position']['x'], item['position']['z']])


    # Finding max and min values of X and Z
    maxX = 0
    minX = 0
    maxZ = 0
    minZ = 0

    for item in obj:
        if item[2] > maxX:
            maxX = item[2]
        if item[2] < minX:
            minX = item[2]
        if item[3] > maxZ:
            maxZ = item[3]
        if item[3] < minZ:
            minZ = item[3]

    xRange = abs(maxX - minX)
    zRange = abs(maxZ - minZ)

    xStep = xRange / 20
    zStep = zRange / 20

    objectMatrix = []
    tempKObj = []
    tempIObj = []

    # Creating the object matrix sorted in X and Z
    for k in range(21):
        for x in range(len(obj)):
            if (k * zStep + minZ) < obj[x][3] < ((k + 1) * zStep + minZ):
                tempKObj.append(obj[x])
        for i in range(21):
            for y in range(len(tempKObj)):
                if (i * xStep + minX) < tempKObj[y][2] < ((i + 1) * xStep + minX):
                    tempIObj.append(tempKObj[y])
                else:
                    break
            tempIObj.append('')
        objectMatrix.append(tempIObj)
        tempKObj = []
        tempIObj = []

    blockMatrix = [[''] * 21 for i in range(21)]
    for i in range(21):
        for j in range(21):
            if objectMatrix[i][j] != '':
                blockMatrix[i][j] = (getBlock.get_block(objectMatrix[i][j][0], objectMatrix[i][j][1]))
            else:
                blockMatrix[i][j] = 'NA'

    return controller, xStep, blockMatrix, objects

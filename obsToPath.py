import pandas as pd
import numpy as np
import seaborn as sns
import random
import math
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

# Function to generate a velocity field and get path from the observation data collected from con_to_obs
def obs_to_path(controller, iObs, iPos, xTrainWts, scatFlag, homeFlag,
                pDataName, moveHist, reachablePositions):
    trainClass = -1
    trainFlag = (-1, -1)
    fRepeat = 0

    # read the mapping from observation to dataset
    src = 'data/robothor_to_' + pDataName + '.xlsx'
    mapping = pd.read_excel(src)
    blocks = list(mapping.block)

    classno = list(mapping.classNo)
    # df1 = pd.DataFrame(blocks)
    # df1.to_excel(excel_writer="/Users/personal/Desktop/temp/blocks.xlsx")

    # Creating a matrix of objects in a 2-D grid near the robot.
    # make a matrix of classno per x-z location
    obs = [[] for x in range(21)]
    for i in range(len(iObs)):
        for k in range(len(iObs[0])):
            temp = iObs[k][i]
            if temp in blocks:
                temp = classno[blocks.index(temp)]
                temp = int(temp)
                obs[i].append(temp)
            else:
                obs[i].append(-1)
    obs = np.matrix(obs)

    # make an orientation arrow for plotting
    x0 = int(np.round(len(obs) / 2, 0)) - 1
    z0 = int(np.round(len(obs) / 2, 0)) - 1
    yaw = iPos[2]
    if yaw >= 45 and yaw <= 135:  # N
        dx = 0
        dz = 1
    elif (yaw > 135 and yaw <= 225):  # W
        dx = -1
        dz = 0
    elif (yaw > 225 and yaw <= 315):  # S
        dx = 0
        dz = -1
    else:  # E
        dx = 1
        dz = 0

    # make dots for plotting
    xdots = np.arange(0, 21, 3)
    zdots = np.arange(0, 21, 3)
    x1 = []
    z1 = []
    for i in xdots:
        for k in zdots:
            x1.append(i)
            z1.append(k)

    # process points of attraction
    nskip = 1
    obsFilt = obs[::nskip, ::nskip]
    x = np.arange(-10, 11, nskip)
    z = np.arange(-10, 11, nskip)
    X, Z = np.meshgrid(x, z)
    u = np.zeros_like(X)
    v = np.zeros_like(Z)
    xvec = []
    zvec = []
    avec = []
    considered = []
    for i in range(len(obsFilt)):
        for j in range(len(obsFilt)):
            if obsFilt[i, j] > -1:
                if obsFilt[i, j] not in considered:
                    xvec.append(X[i, j])
                    zvec.append(Z[i, j])
                    avec.append(xTrainWts[obsFilt[i, j]])
                    considered.append(obsFilt[i, j])

    # flag if in position to learn
    objectsNearby = []
    for i in range(7, 12):
        for k in range(5, 10):
            if obsFilt.item((i, k)) != -1:
                objectsNearby.append(obsFilt.item((i, k)))
    itemNo = len(objectsNearby)
    if itemNo % 2 == 0:
        itemNo = itemNo / 2
    else:
        itemNo = math.floor(itemNo / 2)
    itemNo = math.floor(itemNo)

    if len(objectsNearby) > 0 and not scatFlag[0] and not homeFlag:
        trainClass = objectsNearby[itemNo]
        print('learning class {}'.format(trainClass))
        trainFlag = (trainClass, 1)

    # create velocity field
    for k in range(len(xvec)):
        xi = xvec[k]
        zi = zvec[k]
        ai = avec[k]
        for i in range(len(x)):
            for j in range(len(z)):
                d = np.sqrt((X[i, j] - xi) ** 2 + (Z[i, j] - zi) ** 2)
                theta = np.arctan2((Z[i, j] - zi), (X[i, j] - xi))
                if d < 1:
                    u[i][j] = 0
                    v[i][j] = 0
                else:
                    u[i][j] += ai * np.cos(theta) / d
                    v[i][j] += ai * np.sin(theta) / d

    # plot 1
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 3))
    plt.style.use('seaborn-whitegrid')
    sns.heatmap(obs, vmin=0, vmax=100, xticklabels=False, yticklabels=False, ax=ax1, cbar=False)
    ax1.arrow(x0, z0, dx, dz, width=0.1, head_width=0.5, fc='white', ec='white', zorder=3)
    ax1.scatter(x1, z1, c='white', s=2)

    # check if any attraction
    ubar = u[10, 10]
    vbar = v[10, 10]
    fMove = (np.abs(ubar) > 0) or (np.abs(vbar) > 0)
    fHome = homeFlag
    fScat = scatFlag[0]
    fTrain = (trainFlag[0] != -1)

    # if not fMove and not fTrain and not fScat: fHome = True

    # plot 2
    ax2.quiver(X, Z, u, v)
    ax2.xaxis.set_ticks([])
    ax2.yaxis.set_ticks([])
    ax2.invert_yaxis()
    stream = ax2.streamplot(X, z, u, v, start_points=np.array([[0, 0]]), integration_direction='forward')
    segments = stream.lines.get_segments()

    ubar = u[10, 10]
    vbar = v[10, 10]

    if len(segments) == 0:  # manually make a segment
        if np.abs(vbar) > np.abs(ubar):
            if vbar > 0: segments = [[tuple([0, 0]), tuple([0, 1])], [tuple([0, 1]), tuple([0, 2])]]
            if vbar < 0: segments = [[tuple([0, 0]), tuple([0, -1])], [tuple([0, -1]), tuple([0, -2])]]
        else:
            if ubar > 0: segments = [[tuple([0, 0]), tuple([1, 0])], [tuple([1, 0]), tuple([2, 0])]]
            if ubar < 0: segments = [[tuple([0, 0]), tuple([-1, 0])], [tuple([-1, 0]), tuple([-2, 0])]]

    # make discretized path
    path = [tuple([0, 0])]
    for i in range(len(segments)):
        temp = tuple(np.round(segments[i][1], 0))
        temp = tuple([int(x) for x in temp])
        if temp[0] != path[-1][0] or temp[1] != path[-1][1]:
            path.append(temp)

    # overlay the path on plot 2
    if fMove:
        xPath = []
        yPath = []
        for i in range(len(path)):
            xPath.append(path[i][0])
            yPath.append(path[i][1])
        ax2.plot(xPath, yPath, 'purple')
        ax2.add_patch(plt.Circle((0, 0), 0.5))

        # plot points of attraction
        if not fHome and not fScat:
            xPos = []
            zPos = []
            xNeg = []
            zNeg = []
            for i in range(len(avec)):
                ai = avec[i]
                if ai > 0:
                    xPos.append(xvec[i])
                    zPos.append(zvec[i])
                else:
                    xNeg.append(xvec[i])
                    zNeg.append(zvec[i])
            ax2.scatter(xPos, zPos, s=10, c='red')
            ax2.scatter(xNeg, zNeg, s=10, c='green')

    # plt.subplots_adjust(wspace=0.025, hspace=0)
    # plt.show()

    # Check different cases of agent status (home, scatter, move, train, repeat)

    # ---------------------------------------------------------------------
    if fScat:  # update the velocity field with scatter direction
        print('SCATTER')
        x = np.arange(-10, 11, nskip)
        z = np.arange(-10, 11, nskip)
        X, Z = np.meshgrid(x, z)
        currDir = scatFlag[2]
        if currDir == 'N':
            uS = 0
            vS = 1
        elif currDir == 'S':
            uS = 0
            vS = -1
        elif currDir == 'E':
            uS = 1
            vS = 0
        elif currDir == 'W':
            uS = -1
            vS = 0

        u = uS * np.ones_like(X)
        v = vS * np.ones_like(Z)

    # ---------------------------------------------------------------------
    elif fHome:  # update velocity field with home direction
        print('HOME')
        controller.step(
            action="Teleport",
            position=dict(x=iPos[0], y=0.9, z=iPos[1]),
            rotation=dict(x=0, y=iPos[2], z=0),
            standing=True
        )
        u = np.zeros_like(X)
        v = np.zeros_like(Z)
        x0 = iPos[0]
        z0 = iPos[1]
        dz = -0.5 - z0
        dx = -0.5 - x0
        if np.abs(x0) > np.abs(z0):  # E/W buildings (center Z, then X)
            if np.abs(dz) > 1:
                for i in range(len(x)):
                    for j in range(len(z)):
                        u[i][j] += 0
                        v[i][j] += dz / np.abs(dz)
            else:
                for i in range(len(x)):
                    for j in range(len(z)):
                        u[i][j] += dx / np.abs(dx)
                        v[i][j] += 0

        else:  # N/S buildings (center X, then Z)
            if np.abs(dx) > 1:
                for i in range(len(x)):
                    for j in range(len(z)):
                        u[i][j] += dx / np.abs(dx)
                        v[i][j] += 0

            else:
                for i in range(len(x)):
                    for j in range(len(z)):
                        u[i][j] += 0
                        v[i][j] += dz / np.abs(dz)
    elif fTrain:
        print('TRAIN')

    # ---------------------------------------------------------------------
    elif not fMove and not fRepeat:  # try to get out of the minima
        print('SCRAMBLE')
        u[10, 10] = random.choice([-1, 1])
        v[10, 10] = random.choice([-1, 1])

    else:
        print('MOVE')
    # ---------------------------------------------------------------------

    homeFlag = fHome
    plt.close()

    return controller, path, homeFlag, obs, trainClass

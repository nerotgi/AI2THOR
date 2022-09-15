import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random


def obs_to_path(agent_host, state, iObs, iPos, xTrainWts, scatFlag, homeFlag, pDataName):
    trainFlag = (-1, -1)

    # send Chris a list of objects in RoboThor
    # read the mapping from observation to dataset
    src = 'data/block_to_' + pDataName + '.xlsx'
    mapping = pd.read_excel(src)
    blocks = list(mapping.block)
    classno = list(mapping.classNo)

    #Creating a matrix of objects in a 2-D grid near the robot.
    # make a matrix of classno per x-z location
    obs = [[] for x in range(31)]
    for i in range(len(collect)):
        for k in range(len(collect[0])):
            temp = collect[k][i]
            temp = [x for x in temp if x in blocks]
            temp = [classno[blocks.index(x)] for x in temp]
            if len(temp) > 0:
                temp2 = int(temp[0])
            else:
                temp2 = -1
            obs[i].append(temp2)
    obs = np.matrix(obs)

    # make an orientation arrow for plotting
    x0 = int(np.round(len(obs) / 2, 0)) - 1
    z0 = int(np.round(len(obs) / 2, 0)) - 1
    yaw = iPos[2]
    # print(yaw)
    if yaw >= 45 and yaw <= 135:  # W (90)
        dx = -1
        dz = 0
    elif (yaw >= 135 and yaw <= 180) or yaw < -135:  # N (180)
        dx = 0
        dz = -1
    elif (yaw <= -45 and yaw >= -135) or (yaw >= 225 and yaw <= 315):  # E (-90 or 270)
        dx = 1
        dz = 0
    else:  # S (0)
        dx = 0
        dz = 1

    # make dots for plotting
    xdots = np.arange(0, 31, 3)
    zdots = np.arange(0, 31, 3)
    x1 = []
    z1 = []
    for i in xdots:
        for k in zdots:
            x1.append(i)
            z1.append(k)

    # process points of attraction
    nskip = 1
    obsFilt = obs[::nskip, ::nskip]
    x = np.arange(-15, 16, nskip)
    z = np.arange(-15, 16, nskip)
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
    # print(obsFilt[15,15])
    arrayInFront = [[0 for i in range(5)] for j in range(12, 15)]
    for i in range(5):
        for j in range(3):
            if arrayInFront[i][j] != 0 and scatFlag[0] and not homeFlag:
                trainClass = obsFilt[i, j]
                # print('learning class {}'.format(trainClass))
                nTrain = 0
                for i in range(-2, 3):
                    for j in range(-1, 2):
                        temp = obsFilt[15 + i, 15 + j]
                        if temp == trainClass: nTrain += 1
                trainFlag = (trainClass, nTrain)

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
    ubar = u[15, 15]
    vbar = v[15, 15]
    fMove = (np.abs(ubar) > 0) or (np.abs(vbar) > 0)
    fHome = homeFlag
    fScat = scatFlag[0]
    fTrain = (trainFlag[0] != -1)
    # print(ubar, vbar, fMove)

    # if not fMove and not fTrain and not fScat: fHome = True

    # Check different cases of agent status (home, scatter, move, train)
    # ---------------------------------------------------------------------
    if fScat:  # update the velocity field with scatter direction
        print('SCATTER')
        x = np.arange(-15, 16, nskip)
        z = np.arange(-15, 16, nskip)
        X, Z = np.meshgrid(x, z)
        currDir = scatFlag[2]
        if currDir == 'N':
            uS = 0
            vS = -1
        elif currDir == 'S':
            uS = 0
            vS = 1
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
    elif not fMove:  # try to get out of the minima
        print('SCRAMBLE')
        u[15, 15] = random.choice([-1, 1])
        v[15, 15] = random.choice([-1, 1])

    else:
        print('MOVE')
    # ---------------------------------------------------------------------

    # plot 2
    ax2.quiver(X, Z, u, v)
    ax2.xaxis.set_ticks([])
    ax2.yaxis.set_ticks([])
    ax2.invert_yaxis()
    stream = ax2.streamplot(X, z, u, v, start_points=np.array([[0, 0]]), integration_direction='forward')
    segments = stream.lines.get_segments()

    ubar = u[15, 15]
    vbar = v[15, 15]
    print(ubar, vbar)

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
        if temp[0] != path[-1][0] or temp[1] != path[-1][1]: path.append(temp)

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

    homeFlag = fHome
    return path, trainFlag, homeFlag


def path_to_move(agent_host, state, path, iPos, prevPos):
    if state.is_mission_running:
        if len(path) > 1:
            x0 = path[0][0]
            z0 = path[0][1]
            x1 = path[1][0]
            z1 = path[1][1]

        else:
            x0 = prevPos[0]
            z0 = prevPos[1]
            x1 = iPos[0]
            z1 = iPos[1]

        dx = x1 - x0
        dz = z1 - z0
        yaw0 = iPos[2]

        if dz > 0:
            if yaw0 == 90:
                agent_host.sendCommand("turn -1")
            elif yaw0 == 180:
                agent_host.sendCommand("turn -1")
                agent_host.sendCommand("turn -1")
            elif yaw0 == -90 or yaw0 == 270:
                agent_host.sendCommand("turn 1")

        elif dz < 0:
            if yaw0 == -90 or yaw0 == 270:
                agent_host.sendCommand("turn -1")
            elif yaw0 == 0:
                agent_host.sendCommand("turn -1")
                agent_host.sendCommand("turn -1")
            elif yaw0 == 90:
                agent_host.sendCommand("turn 1")

        elif dx > 0:
            if yaw0 == 0:
                agent_host.sendCommand("turn -1")
            elif yaw0 == 90:
                agent_host.sendCommand("turn -1")
                agent_host.sendCommand("turn -1")
            elif yaw0 == 180:
                agent_host.sendCommand("turn 1")

        elif dx < 0:
            if yaw0 == 180:
                agent_host.sendCommand("turn -1")
            elif yaw0 == -90 or yaw0 == 270:
                agent_host.sendCommand("turn -1")
                agent_host.sendCommand("turn -1")
            elif yaw0 == 0:
                agent_host.sendCommand("turn 1")

        if dz > 0:
            agent_host.sendCommand("jumpsouth 1")
        elif dz < 0:
            agent_host.sendCommand("jumpnorth 1")
        elif dx > 0:
            agent_host.sendCommand("jumpeast 1")
        elif dx < 0:
            agent_host.sendCommand("jumpwest 1")

        prevPos = (iPos[0], iPos[1], iPos[2])

    return prevPos
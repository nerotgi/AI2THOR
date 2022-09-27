import numpy as np
import math
import random

def path_to_nav(controller, step, path, moveHist):
    print('Path: ' + str(path))
    angle = 0
    arctanCheck = 0
    finalAngle = 0  # Angle robot faces before moving

    # Direction robot is facing initially wrt x-axis
    faceAngle = 90

    # Calculating angle robot has to turn
    if len(path) > 1:
        # Selecting two adjacent segments to find the angle between them
        for i in range(1):
            # print("Segment " + str(i + 1))
            dx = path[i + 1][0] - path[i][0]
            dz = path[i + 1][1] - path[i][1]
            dz = dz * -1
            # Defining angle in cases where arctan is infinity
            if dz == 0:
                if dx == 1:
                    angle = 0
                    arctanCheck = 1
                elif dx == -1:
                    angle = 180
                    arctanCheck = 1

            # If arctan is not infinity, solving for the angle
            if arctanCheck == 0:
                angle = np.arctan(np.abs(dx) / np.abs(dz))
                angle = angle * 180 / np.pi
                if dx > 0:
                    if dz < 0:
                        angle = angle + 270
                else:
                    if dz > 0:
                        angle = angle + 90
                    else:
                        angle = angle + 180

            # Resetting arctan infinity check for the next iteration of the for loop
            arctanCheck = 0
            # Angle robot has to turn
            moveAngle = angle - faceAngle
            if 0 < abs(moveAngle) <= 180:
                if moveAngle < 0:
                    # print("Rotating right by " + str(moveAngle * -1) + " degrees")
                    finalAngle = moveAngle * -1
                    controller.step(
                        action="RotateRight",
                        degrees=finalAngle
                    )
                else:
                    finalAngle = moveAngle
                    # print("Rotating left by " + str(moveAngle) + " degrees")
                    controller.step(
                        action="RotateLeft",
                        degrees=finalAngle
                    )
            if 180 < abs(moveAngle) <= 360:
                if moveAngle < 0:
                    finalAngle = 360 + moveAngle
                    # print("Rotating left by " + str(360 + moveAngle) + " degrees")
                    controller.step(
                        action="RotateLeft",
                        degrees=finalAngle
                    )
                else:
                    finalAngle = 360 - moveAngle
                    # print("Rotating right by " + str(360 - moveAngle) + " degrees")
                    controller.step(
                        action="RotateRight",
                        degrees=finalAngle
                    )

            # Randomizing angle slightly in case bot is stuck in a loop. The randomization increases with every time
            # bot gets stuck in the same location.
            currPos = [controller.last_event.metadata["agent"]["position"]['x'],
                       controller.last_event.metadata["agent"]["position"]['z']]
            nextPos = [math.sin(finalAngle * math.pi / 180) * step + currPos[0], math.cos(finalAngle * math.pi / 180)
                       * step + currPos[1]]
            randomAng = 0
            angleMult = 1
            i = 1  # sanity check for the while loop
            while nextPos in moveHist:
                print('Randomizing angle: ')
                if i != 1:
                    finalAngle = finalAngle - randomAng  # removing the outdated randomAng from the sum
                if i > 50:
                    break
                randomAng = random.randint(-10 * angleMult, 10 * angleMult)
                print(randomAng)
                finalAngle = finalAngle + randomAng
                nextPos = [math.sin(finalAngle * math.pi / 180) * step + currPos[0], math.cos(finalAngle * math.pi / 180)
                           * step + currPos[1]]
                i += 1
                angleMult = angleMult * 1.05
            controller.step(
                action="RotateLeft",
                degrees=randomAng
            )
            # Resetting face angle to equal the segment angle after end of rotation
            controller.step(
                action="MoveAhead",
                moveMagnitude=step
            )
            moveHist.append([controller.last_event.metadata["agent"]["position"]['x'],
                             controller.last_event.metadata["agent"]["position"]['z']])
            # print("Stepping forward")
    return controller

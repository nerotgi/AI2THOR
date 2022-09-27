from ai2thor.controller import Controller
from matplotlib import pyplot as plt
import pandas as pd
from openpyxl import load_workbook
import openpyxl

# Script used to extract information about the controller and scenes to debug the project if necessary
controller = Controller(
    agentMode="locobot",
    visibilityDistance=100,
    scene="FloorPlan_Train1_1",
    gridSize=0.25,
    movementGaussianSigma=0.005,
    rotateStepDegrees=90,
    rotateGaussianSigma=0.5,
    renderInstanceSegmentation=True,
    renderDepthImage=True,
    width=300,
    height=300,
    fieldOfView=60
)

objects = []

scene_name = "FloorPlan_Train"
sheet_name = 0

for x in range(1, 13):
    for y in range(1, 6):
        scene_name = scene_name + str(x) + "_" + str(y)
        sheet_name = scene_name
        controller.reset(scene=scene_name)
        for obj in controller.last_event.metadata["objects"]:
            objects.append(obj)
        for i in range(len(objects)):
            objects[i] = [objects[i]['name'], objects[i]['objectType']]

        df = pd.DataFrame(objects)
        with pd.ExcelWriter('~/Desktop/objects/test.xlsx', engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=scene_name)
            writer.save()
        scene_name = "FloorPlan_Train"
        objects = []
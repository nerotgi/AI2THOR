from ai2thor.controller import Controller
from matplotlib import pyplot as plt
import pandas as pd
import openpyxl

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
for x in range(1, 12):
    for y in range(1, 5):
        scene_name = scene_name + str(x) + "_" + str(y)
        controller.reset(scene=scene_name)
        for obj in controller.last_event.metadata["objects"]:
            objects.append(obj)
        scene_name = "FloorPlan_Train"


scene_name = "FloorPlan_Val"
for x in range(1, 3):
    for y in range(1, 5):
        scene_name = scene_name + str(x) + "_" + str(y)
        controller.reset(scene=scene_name)
        for obj in controller.last_event.metadata["objects"]:
            objects.append(obj)
        scene_name = "FloorPlan_Val"

df = pd.DataFrame(objects)
df.to_excel(excel_writer="/Users/personal/Desktop/test.xlsx")

# objects = controller.last_event.metadata["objects"]
# print(objects)
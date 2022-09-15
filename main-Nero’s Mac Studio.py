from ai2thor.controller import Controller
from ai2thor.platform import CloudRendering

controller = Controller(
    agentMode="locobot",
    massThreshold=None,
    scene="FloorPlan209",
    visibilityDistance=1.5,
    snapToGrid=True,
    gridSize=0.25,
    renderDepthImage=True,
    renderInstaceSegmentation=True,
    width=1000,
    height=1000,
    fieldOfView=60
)

for obj in controller.last_event.metadata["objects"]:
    print(obj["objectType"])

    controller = Controller(platform=CloudRendering)
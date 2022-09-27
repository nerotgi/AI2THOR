# ========================================================
# Incremental Learning (CBCL) with Active Class Selection
# in AI2THOR
#
# C McClurg, A Ayub, AR Wagner, S Rajtmajer, N Tyagi
# ========================================================
**************************
Python 3.6+ required
**************************

About: 

AI2THOR is a tool that allows you to test your AI models and agents in a realistic simulation environment. There are three different kinds of API's available currently, including iTHOR, RoboTHOR, and ManipulaTHOR. For this project, we used the RoboTHOR API because the scenes available for that API were developed from real-life setups. Their latest API is called ProcTHOR that allows users to create new scenes procedurally. After completing the current project, we might look into using ProcTHOR to create more populated environments to test our agents in a more robust surrounding.


Dependencies:

1. Multiprocess
2. SkLearn
3. Pandas
4. Numpy
5. MatPlotLib
6. AI2THOR

There are two important configurations in this project: 
1. Test
2. Plot

The function call structure of Test configuration is as follows:

- __main__ (Test.py)
  - trial (Test.py)
    - robo_thor_controller (roboTHORController.py)
      - con_to_obs (conToObs.py)
      - obs_to_path (obsToPath.py)
      - path_to_nav (pathToNav.py)
      
The __main__ function creates several processes using multiprocess to tackle multiple test runs at the same time. Each test run has several initial arguments, for example, "pDataName", "pSeed", etc., that are contained in "pack". These arguments are passed on to the trial function where they are unpacked and manipulated to run our agent in AI2THOR, generate observation data, and then use that observation data to create models using SVM and WVS.

Six sets of 10 RoboTHOR scenes are created in the function trial. These sets are used to observe various scenes in RoboTHOR over multiple iterations. The RoboTHOR agent starts in one of these scenes, observes its surroundings, and generates a list of objects that it sees in a 2*2 matrix (in the X-Z plane) using con_to_obs function. This matrix is used to create a velocity field using obs_to_path function. This path is passed on to the path_to_nav function, where the agent takes appropriate steps to follow this path. 

Once the agent is in the vicinity of the object it was trying to get to when it created the velocity field, the object is collected in an array. That array of training objects and several other attributes gathered from the scene are passed on back to the trial function to generate a model.

Two datasets are used: CIFAR-100 and Grocery. Each iteration is run for 30 seconds and there are 120 iterations for the Grocery dataset, and 240 iterations for CIFAR-100.

At the end of each iteration, the RoboTHOR controller is reset and the next scene in the set is initialized, until the end of set is reached, which is when the next set is utilized. The index of the next set to be used is generated randomly. Quantities like increment time (incTime), increment accuracy (accInc), scene name (sceneName), etc., are stored in an Excel file under */results/{mmdd}/{filename}.xlsx for each dataset with each training model for several random seeds.

The other configuration, Plot, is then used to combine all these different iterations together to find the average accuracy and standard deviation of each model for each dataset.

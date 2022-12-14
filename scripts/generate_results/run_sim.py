# =============================================================================
# Incremental Learning (CBCL) with Active Class Selection
#
# C McClurg, A Ayub, AR Wagner, S Rajtmajer, N Tyagi
# =============================================================================

from multiprocess import Process, Queue
from sklearn.model_selection import train_test_split
# from utils import functions
from utilities.functions import CBCL_WVS, CBCL_SVM, CBCL_PR, SVM_redistrict, SVM_simple
from utilities.functions import update_centroids, aff_simple, aff_redistrict
from utilities.get_incremental import incrementalData
from datetime import datetime
import pandas as pd
import numpy as np
import random, pickle, time, os
from scripts.robothor import roboTHORController
from ai2thor.controller import Controller


def trial(q, pack):
    # unpack
    pFileNo = pack[0]
    pMod = pack[1]
    pSeed = pack[2]
    pDataName = pack[3]
    pLearner = pack[4]
    pBias = pack[5]

    # model parameters
    pNetType = 'resnet34'  # CNN type
    pNetFit = 'imagenet'  # dataset for CNN training
    pDistMetric = 'euclidean'  # distance metric
    pCentroidPred = 1  # no. centroids used in ranked voting scheme

    # model random
    np.random.seed(pSeed)
    random.seed(pSeed)
    # read visual features
    readFile = './utilities/features/' + pDataName + '_' + pNetType + '_' + pNetFit + '_'
    with open(readFile + 'train_features.data', 'rb') as fh:
        trainFeatRGB = pickle.load(fh)
    with open(readFile + 'test_features.data', 'rb') as fh:
        testFeatRGB = pickle.load(fh)
    with open(readFile + 'train_labels.data', 'rb') as fh:
        trainLabelRGB = pickle.load(fh)
    with open(readFile + 'test_labels.data', 'rb') as fh:
        testLabelRGB = pickle.load(fh)

    nClassTotal = len(set(testLabelRGB))
    pShotStart = nClassTotal
    if pDataName == 'grocery':
        pDistLim = 13
    elif pDataName == 'cifar':
        pDistLim = 17
    else:
        pDistLim = 15

    # model discretized data
    incData = incrementalData(trainFeatRGB, trainLabelRGB, testFeatRGB, testLabelRGB, pSeed)
    incData.incFormat(1)
    incTrainFeatures = incData.incTrainFeatures
    incTrainLabels = incData.incTrainLabels
    incTestFeatures = incData.incTestFeatures
    incTestLabels = incData.incTestLabels
    nClassTotal = len(set(trainLabelRGB))

    # shuffle by class
    xTrainTot = [[] for i in range(nClassTotal)]
    yTrainTot = [[] for i in range(nClassTotal)]
    xTestTot = [[] for i in range(nClassTotal)]
    yTestTot = [[] for i in range(nClassTotal)]

    for iInc in range(len(incTrainLabels)):
        xTrainKeep, xTrainDel, yTrainKeep, yTrainDel = train_test_split(incTrainFeatures[iInc], incTrainLabels[iInc],
                                                                        random_state=pSeed, test_size=1)
        xTestKeep, xTestDel, yTestKeep, yTestDel = train_test_split(incTestFeatures[iInc], incTestLabels[iInc],
                                                                    random_state=pSeed, test_size=1)
        iClass = yTrainKeep[0]
        xTrainTot[iClass].extend(xTrainKeep)
        yTrainTot[iClass].extend(yTrainKeep)
        xTestTot[iClass].extend(xTestKeep)
        yTestTot[iClass].extend(yTestKeep)
    del xTrainKeep, yTrainKeep, xTestDel, yTestDel

    # pull together all training and test instances for a dataset
    for i in range(len(yTrainTot)):
        xTrainTot[i].extend(xTestTot[i])
        yTrainTot[i].extend(yTestTot[i])
    del xTestTot, yTestTot

    # prepare dataset for 90/10 train/test split
    xTestTot = []
    yTestTot = []
    for iClass in range(nClassTotal):
        xTrainTot[iClass], xTestTemp, yTrainTot[iClass], yTestTemp = train_test_split(xTrainTot[iClass],
                                                                                      yTrainTot[iClass],
                                                                                      random_state=pSeed,
                                                                                      test_size=0.10)
        xTestTot.extend(xTestTemp)
        yTestTot.extend(yTestTemp)
    del xTestTemp, yTestTemp

    # initialize
    centClass = [[] for x in range(nClassTotal)]  # centroids per class
    centWtClass = [[] for x in range(nClassTotal)]  # centroid wt per class
    centStdClass = [[] for x in range(nClassTotal)]  # centroid std per class
    covaClass = [[] for x in range(nClassTotal)]  # covariance matrices per class
    nShotClass = [0 for x in range(nClassTotal)]  # image count per class
    weightClass = [0 for x in range(nClassTotal)]  # weight per class
    rAccClass = [0 for x in range(nClassTotal)]  # test accuracy per class
    redClass = [0 for x in range(nClassTotal)]  # redistrict by class
    xTrainBatch = []  # features for SVM case
    yTrainBatch = []  # labels for SVM case
    prevSplit = []  # only for redistricting

    # initial examples
    biasTemp = [random.randint(1, 10) for x in range(nClassTotal)]
    biasClass = [int(np.rint(x / np.sum(biasTemp) * pShotStart)) for x in biasTemp]
    needs_corrected = True
    while needs_corrected:
        if np.sum(biasClass) > pShotStart:
            ix = random.randint(0, nClassTotal - 1)
            if biasClass[ix] > 1: biasClass[ix] -= 1
        elif np.sum(biasClass) < pShotStart:
            ix = random.randint(0, nClassTotal - 1)
            biasClass[ix] += 1
        else:
            needs_corrected = False

    if pLearner != 'SVM':  # CBCL
        xTrainCurr = []
        yTrainCurr = []
        for iClass in range(len(biasClass)):
            for j in range(biasClass[iClass]):
                if len(xTrainTot[iClass]) > 0:
                    xTrainCurr.append(xTrainTot[iClass][0])
                    yTrainCurr.extend([yTrainTot[iClass][0]])
                    nShotClass[iClass] += 1
                    del xTrainTot[iClass][0]
                    del yTrainTot[iClass][0]
                else:
                    fReplace = True  # replace biased class with random
                    while fReplace:
                        randClass = random.randint(0, nClassTotal - 1)
                        if len(xTrainTot[randClass]) > 0:
                            xTrainCurr.append(xTrainTot[randClass][0])
                            yTrainCurr.extend([yTrainTot[randClass][0]])
                            nShotClass[randClass] += 1
                            del xTrainTot[randClass][0]
                            del yTrainTot[randClass][0]
                            fReplace = False

        # create centroids
        pack = [xTrainCurr, yTrainCurr, centClass, centWtClass, pDistLim, pDistMetric, covaClass, centStdClass]
        [centClass, centWtClass, covaClass, centStdClass] = update_centroids(pack)

        # count centroids
        nCentTotal = 0
        for iClass in range(nClassTotal): nCentTotal += len(centClass[iClass])

        # find weights for fighting bias
        for iClass in range(nClassTotal):
            if nShotClass[iClass] != 0:
                weightClass[iClass] = np.divide(1, nShotClass[iClass])
            else:
                weightClass[iClass] = 0
        weightClass = np.divide(weightClass, np.sum(weightClass))

        # make new predictions
        rAccClass0 = rAccClass.copy()
        pack = [xTestTot, yTestTot, centClass, pCentroidPred, nClassTotal, weightClass, pDistMetric, covaClass, centWtClass]
        if pLearner == 'CBCLWVS':
            rAcc, rAccClass = CBCL_WVS(pack)
        elif pLearner == 'CBCLSVM':
            rAcc, rAccClass = CBCL_SVM(pack)
        else:
            rAcc, rAccClass = CBCL_PR(pack)


    else:  # SVM
        xNew = []
        yNew = []
        nObsNew = 0
        for iClass in range(len(biasClass)):
            for j in range(biasClass[iClass]):
                if len(yTrainTot[iClass]) > 0:
                    xTrainObs = xTrainTot[iClass][0]
                    yTrainObs = yTrainTot[iClass][0]
                    xNew.append(xTrainTot[iClass][0])
                    yNew.append(yTrainTot[iClass][0])
                    xTrainBatch.append(xTrainObs)
                    yTrainBatch.append(yTrainObs)
                    del xTrainTot[iClass][0]
                    del yTrainTot[iClass][0]
                    nShotClass[yTrainObs] += 1
                    nObsNew += 1
                else:
                    fReplace = True  # replace biased class with random
                    while fReplace:
                        randClass = random.randint(0, nClassTotal - 1)
                        if len(xTrainTot[randClass]) > 0:
                            xTrainObs = xTrainTot[randClass][0]
                            yTrainObs = yTrainTot[randClass][0]
                            xNew.append(xTrainTot[randClass][0])
                            yNew.append(yTrainTot[randClass][0])
                            xTrainBatch.append(xTrainObs)
                            yTrainBatch.append(yTrainObs)
                            del xTrainTot[randClass][0]
                            del yTrainTot[randClass][0]
                            nShotClass[yTrainObs] += 1
                            nObsNew += 1
                            fReplace = False

        # learn and make predictions
        if pBias == 'redistrict':
            rAccClass0 = rAccClass.copy()
            rAcc, rAccClass, prevSplit, redClass = SVM_redistrict(xTrainBatch, yTrainBatch,
                                                                  xNew, yNew, xTestTot, yTestTot,
                                                                  prevSplit, redClass, 'SVM', pSeed, 0)
        else:
            rAccClass0 = rAccClass.copy()
            rAcc, rAccClass = SVM_simple(xTrainBatch, yTrainBatch, xTestTot, yTestTot, nClassTotal, 'SVM', pSeed)

        yTrainCurr = yTrainBatch.copy()

    del biasClass, biasTemp

    # count observations
    nObsTot = 0
    nObsTotClass = [0 for i in range(nClassTotal)]
    for i in range(len(yTrainCurr)):
        nObsTot += 1
        iClass = yTrainCurr[i]
        nObsTotClass[iClass] += 1
    # -----------------------------------------------------------------------------

    # sim parameters
    if pDataName == 'grocery':
        pInc = 120
    else:
        pInc = 240

    pRestock = True

    # initialize sim variables
    # does not apply to RoboTHOR
    iPos = (0, 0, 0)
    nObsTotClass = [0 for i in range(nClassTotal)]

    # initialize output variables
    final_obs = [nObsTot]
    final_acc = [np.round(rAcc, 3)]
    final_runTime = [0]
    final_runDist = [0]
    final_trainTime = [0]
    runTime = 0
    runDist = 0
    trainTime = 0
    pStatus = 'IP'
    xLeftover = []
    yLeftover = []
    nObsLeftover = 0

    collectionNum = 0
    sceneNum = 0
    sceneNames = []

    for iInc in range(pInc):

        if iInc % 10 == 0:
            collectionNum = random.randint(0, 5)
            sceneNum = 0
        if iInc % 10 != 0:
            sceneNum += 1

        scenes = [["FloorPlan_Train1_1", "FloorPlan_Train2_1", "FloorPlan_Train3_1", "FloorPlan_Train4_1",
                   "FloorPlan_Train5_1", "FloorPlan_Train6_1", "FloorPlan_Train7_1", "FloorPlan_Train8_1",
                   "FloorPlan_Train9_1", "FloorPlan_Train10_1"],
                  ["FloorPlan_Train1_2", "FloorPlan_Train2_2", "FloorPlan_Train3_2", "FloorPlan_Train4_2",
                   "FloorPlan_Train5_2", "FloorPlan_Train6_2", "FloorPlan_Train7_2", "FloorPlan_Train8_2",
                   "FloorPlan_Train9_2", "FloorPlan_Train10_2"],
                  ["FloorPlan_Train1_3", "FloorPlan_Train2_3", "FloorPlan_Train3_3", "FloorPlan_Train4_3",
                   "FloorPlan_Train5_3", "FloorPlan_Train6_3", "FloorPlan_Train7_3", "FloorPlan_Train8_3",
                   "FloorPlan_Train9_3", "FloorPlan_Train10_3"],
                  ["FloorPlan_Train1_4", "FloorPlan_Train2_4", "FloorPlan_Train3_4", "FloorPlan_Train4_4",
                   "FloorPlan_Train5_4", "FloorPlan_Train6_4", "FloorPlan_Train7_4", "FloorPlan_Train8_4",
                   "FloorPlan_Train9_4", "FloorPlan_Train10_4"],
                  ["FloorPlan_Train1_5", "FloorPlan_Train2_5", "FloorPlan_Train3_5", "FloorPlan_Train4_5",
                   "FloorPlan_Train5_1", "FloorPlan_Train6_5", "FloorPlan_Train7_5", "FloorPlan_Train8_5",
                   "FloorPlan_Train9_5", "FloorPlan_Train10_5"],
                  ["FloorPlan_Train11_1", "FloorPlan_Train11_2", "FloorPlan_Train11_3", "FloorPlan_Train11_4",
                   "FloorPlan_Train11_5", "FloorPlan_Train12_1", "FloorPlan_Train12_2", "FloorPlan_Train12_3",
                   "FloorPlan_Train12_4", "FloorPlan_Train12_5"]
                  ]

        # print(scenes[collectionNum][sceneNum])

        controller = Controller(
            agentMode="locobot",
            quality='Very Low',
            visibilityDistance=5.0,
            scene=scenes[collectionNum][sceneNum],
            gridSize=0.01,
            movementGaussianSigma=0.01,
            rotateStepDegrees=90,
            rotateGaussianSigma=0.1,
            renderInstanceSegmentation=True,
            renderDepthImage=True,
            width=100,
            height=100,
            fieldOfView=60
        )
        # topDown = topDownView.get_top_down_frame(controller)
        # plt.imshow(topDown, interpolation='nearest')
        # plt.show()

        reachablePositions = controller.step(
            action="GetReachablePositions"
        ).metadata["actionReturn"]
        for i in range(len(reachablePositions)):
            reachablePositions[i] = [round(reachablePositions[i]['x'], 2), round(reachablePositions[i]['z'], 2)]
        x = controller.last_event.metadata["agent"]["position"]["x"]
        z = controller.last_event.metadata["agent"]["position"]["z"]
        yaw = np.round(controller.last_event.metadata["agent"]["rotation"]["y"], 0)
        home_pos = [x, z, yaw]

        print(str(iInc + 1) + ' of ' + str(pInc))

        # count available
        nTrainSimClass = [len(x) for x in xTrainTot]
        nClassEmpty = 0
        for iClass in range(len(nTrainSimClass)):
            nTempClass = nTrainSimClass[iClass]
            if nTempClass == 0: nClassEmpty += 1

        # affinity for searching
        if pBias == 'redistrict':
            aClass = aff_redistrict(nShotClass, redClass, iInc, pMod)
        else:
            aClass = aff_simple(pBias, centWtClass, centStdClass, rAccClass, rAccClass0, pMod)

        # collect images in RoboTHOR simulation
        pack = [pSeed, iPos, aClass, nObsTotClass, nTrainSimClass, 0, pRestock, pDataName, pFileNo, iInc]
        # mcTicks is a leftover artifact from Malmo test. Its value is irrelevant.
        iPos, mcTicks, iDist, iTime, nObsNewClass, actions = roboTHORController.robo_thor_controller(pack, controller,
                                                                                            reachablePositions,
                                                                                            home_pos)
        print(actions)
        controller.stop()
        controller.stop_unity()
        runDist += iDist
        runTime += iTime

        # count the new images (assume pRestock True)
        nTrainNewClass = nObsNewClass.copy()
        nObsTotClass = np.array(nObsTotClass)
        nObsTotClass = nObsTotClass + np.array(nTrainNewClass)
        nObsTotClass = list(nObsTotClass)

        if pLearner != 'SVM':  # CBCL

            train_t0 = np.round(time.time(), 2)

            # process images
            xTrainCurr = []
            yTrainCurr = []
            nObsNew = 0
            for iClass in range(len(nTrainNewClass)):
                for j in range(nTrainNewClass[iClass]):
                    if len(yTrainTot[iClass]) > 0:
                        xTrainObs = xTrainTot[iClass][0]
                        yTrainObs = yTrainTot[iClass][0]
                        del xTrainTot[iClass][0]
                        del yTrainTot[iClass][0]
                        xTrainCurr.append(xTrainObs)
                        yTrainCurr.append(yTrainObs)
                        nShotClass[yTrainObs] += 1
                        nObsNew += 1

            # update centroids
            pack = [xTrainCurr, yTrainCurr, centClass, centWtClass, pDistLim, pDistMetric, covaClass, centStdClass]
            [centClass, centWtClass, covaClass, centStdClass] = update_centroids(pack)

            # count total centroids
            nCentTotal = 0
            for iClass in range(nClassTotal): nCentTotal += len(centClass[iClass])

            # find weights for fighting bias
            for iClass in range(nClassTotal):
                if nShotClass[iClass] != 0:
                    weightClass[iClass] = np.divide(1, nShotClass[iClass])
                else:
                    weightClass[iClass] = 0
            weightClass = np.divide(weightClass, np.sum(weightClass))

            # make new predictions
            rAccClass0 = rAccClass.copy()
            pack = [xTestTot, yTestTot, centClass, pCentroidPred, nClassTotal, weightClass, pDistMetric, covaClass,
                    centWtClass]
            if pLearner == 'CBCLWVS':
                rAcc, rAccClass = CBCL_WVS(pack)
            elif pLearner == 'CBCLSVM':
                rAcc, rAccClass = CBCL_SVM(pack)
            else:
                rAcc, rAccClass = CBCL_PR(pack)

            train_t1 = np.round(time.time(), 2)
            addTime = (train_t1 - train_t0)
            trainTime += addTime

        else:  # SVM

            train_t0 = np.round(time.time(), 3)

            # process images
            xNew = xLeftover.copy()
            yNew = yLeftover.copy()
            nObsNew = nObsLeftover

            for iClass in range(len(nTrainNewClass)):
                for j in range(nTrainNewClass[iClass]):
                    if len(yTrainTot[iClass]) > 0:
                        xTrainObs = xTrainTot[iClass][0]
                        yTrainObs = yTrainTot[iClass][0]
                        xNew.append(xTrainObs)
                        yNew.append(yTrainObs)
                        xTrainBatch.append(xTrainObs)
                        yTrainBatch.append(yTrainObs)
                        del xTrainTot[iClass][0]
                        del yTrainTot[iClass][0]
                        nShotClass[yTrainObs] += 1
                        nObsNew += 1

            # learn and make predictions
            if pBias == 'redistrict':

                if nObsNew < 10 and nObsLeftover == 0:  # too few observations, save what you have and don't train
                    xLeftover = xNew.copy()
                    yLeftover = yNew.copy()
                    nObsLeftover = nObsNew

                elif nObsNew < 10 and nObsLeftover != 0:  # too few observations (again), save what you have and don't train
                    xLeftover.append(xNew)
                    yLeftover.extend(yNew)
                    nObsLeftover += nObsNew

                else:  # enough observations, train and test
                    rAccClass0 = rAccClass.copy()
                    rAcc, rAccClass, prevSplit, redClass = SVM_redistrict(xTrainBatch, yTrainBatch,
                                                                          xNew, yNew, xTestTot, yTestTot,
                                                                          prevSplit, redClass, 'SVM', pSeed, iInc + 1)
                    xLeftover = []
                    yLeftover = []
                    nObsLeftover = 0

            else:
                rAccClass0 = rAccClass.copy()
                rAcc, rAccClass = SVM_simple(xTrainBatch, yTrainBatch, xTestTot, yTestTot, nClassTotal, 'SVM', pSeed)

            train_t1 = np.round(time.time(), 3)
            addTime = (train_t1 - train_t0)
            trainTime += addTime

        # record results
        if nObsLeftover == 0: nObsTot += nObsNew
        final_obs.append(nObsTot)
        final_acc.append(np.round(rAcc, 3))
        final_runTime.append(np.round(runTime, 2))
        final_runDist.append(runDist)
        final_trainTime.append(np.round(trainTime, 2))

        sceneNames.append(scenes[collectionNum][sceneNum])
        if iInc == (pInc - 1): pStatus = 'complete'
        output = [pStatus, pFileNo, pMod, pSeed, pDataName, pBias, pLearner, sceneNames, final_obs, final_acc, final_runTime,
                  final_runDist, final_trainTime, aClass]
        if q is not None: q.put(output)
        time.sleep(0.1)

    # -----------------------------------------------------------------------------


if __name__ == "__main__":
    # prepare pack for test
    i = 0
    testPack = []

    # for pMod in [1]:
    #     for pSeed in [4,7]:
    #         for pDataName in ['grocery']:
    #             for pLearner in ['CBCLPR']:
    #                 for pBias in ['clusterWt', 'clusterStdLow', 'clusterStdHigh', 'uniform']:
    #                     testPack.append([i, pMod, pSeed, pDataName, pLearner, pBias])
    #                     i += 1
                # for pLearner in ['CBCLPR', 'CBCLSVM']:
                #     for pBias in ['classWt', 'uniform', 'clusterWt', 'clusterStdLow', 'clusterStdHigh']:
                #         testPack.append([i, pMod, 9, pDataName, pLearner, pBias])
                #         i += 1

    # testPack.append([0, 1, 0, 'grocery', 'CBCLPR', 'clusterWt'])
    # testPack.append([1, 1, 1, 'grocery', 'CBCLPR', 'clusterWt'])
    # testPack.append([2, 1, 4, 'grocery', 'CBCLPR', 'clusterStdLow'])
    testPack.append([0, 1, 0, 'cifar', 'CBCLPR', 'clusterStdHigh'])
    testPack.append([1, 1, 7, 'cifar', 'CBCLPR', 'uniform'])
    testPack.append([2, 1, 9, 'cifar', 'CBCLPR', 'clusterWt'])



    totalResult = [[] for j in range(3)]
    # multi-processing params
    nProcs = 3
    q = Queue()
    pHandle = []

    # create write path
    now = datetime.now()
    d0 = now.strftime('%m_%d_%Y')
    d1 = now.strftime('%H_%M_%S')
    FILENAME = './results/data/{}/{}_robothor.xlsx'.format(d0, d1)
    try:
        os.mkdir('./results/data/{}'.format(d0))
    except:
        pass

    # run test and write results
    for i in range(nProcs):
        pHandle.append(Process(target=trial, args=(q, testPack[0])))
        testPack.pop(0)
        pHandle[-1].start()

    while len(pHandle):
        pHandle = [x for x in pHandle if x.is_alive()]
        s = nProcs - len(pHandle)

        for i in range(s):
            if len(testPack):
                pHandle.append(Process(target=trial, args=(q, testPack[0])))
                testPack.pop(0)
                pHandle[-1].start()

        while q.qsize() > 0:
            singleResult = q.get()
            ix = singleResult[1]
            totalResult[ix] = singleResult
            df = pd.DataFrame(totalResult,
                              columns=['status', 'no.', 'mod', 'seed', 'data', 'bias', 'learner', 'sceneName', 'obsInc', 'accInc', 'runTimeInc',
                                       'runDistInc', 'trainTimeInc', 'aClass'])
            df.to_excel(FILENAME)
import pandas as pd
import random
import textwrap

# inputs
pSet = 2
pRan = 0
pInc = 0
iPos = (0, 0)
iTrial = 0


# subfunction of many functions (return coordinates based on map constraints)
def get_xz(sLoc, mapLim, pRan, mapExt):
    # determine amount of random noise
    if pRan == 0.33:
        alist = [1, 0, 0]
    elif pRan == 0.67:
        alist = [1, 1, 0]
    elif pRan == 1.00:
        alist = [1, 1, 1]
    else:
        alist = [0, 0, 0]

    # determine limits of most similar
    xmin = mapLim.loc[sLoc, 'xmin']
    xmax = mapLim.loc[sLoc, 'xmax']
    zmin = mapLim.loc[sLoc, 'zmin']
    zmax = mapLim.loc[sLoc, 'zmax']

    # number of locations in set
    nmap = len(mapLim)

    locSet = list(mapLim.index.values)
    nsim = locSet.index(sLoc)

    # random
    offset = 3  # avoid boundaries
    xsim = random.randint(xmin + offset, xmax - offset)
    zsim = random.randint(zmin + offset, zmax - offset)
    nrand = random.randint(0, nmap - 1)

    # determine limits of random
    xminR = mapLim.iloc[nrand, 0]
    xmaxR = mapLim.iloc[nrand, 1]
    zminR = mapLim.iloc[nrand, 2]
    zmaxR = mapLim.iloc[nrand, 3]

    # random
    xrand = random.randint(xminR + offset, xmaxR - offset)
    zrand = random.randint(zminR + offset, zmaxR - offset)
    arand = random.choice(alist)

    same_as_sim = True
    # assign coordinate values
    if arand == 1:
        if nsim != nrand: same_as_sim = False
        x = xrand
        z = zrand
    else:
        x = xsim
        z = zsim

    return [x, z, same_as_sim]


# subfunction of get_missionXML (return script for placing agent at start)
def write_Placement(xTemp, yGround, zTemp, yawTemp):
    return '\t\t<Placement x="' + str(xTemp) + '" y="' + str(yGround) + '" z="' + str(zTemp) + '" yaw="' + str(
        yawTemp) + '"/>\n'


# subfunction of many functions (return a "good" location, corrected if location is not in maze or map)
def nearest_pos(pos):
    # pos
    x = pos[0]
    z = pos[1]

    # map limits
    mapLim = pd.read_excel('dat/map.xlsx')
    mapLim = mapLim.drop(columns=['set'])
    mapLim = mapLim.set_index('loc')
    xmin = mapLim.iloc[-1, 0]
    xmax = mapLim.iloc[-1, 1]
    zmin = mapLim.iloc[-1, 2]
    zmax = mapLim.iloc[-1, 3]

    # correct pos if not in map limits
    if x > xmax:
        x == xmax
    elif x < xmin:
        x == xmin

    if z > zmax:
        z == zmax
    elif z < zmin:
        z == zmin

    # maze details
    maze = pd.read_excel('dat/maze.xlsx')
    maze = maze.values
    nx_maze = len(maze[0])
    nz_maze = len(maze)
    dx_maze = round((xmax - xmin) / nx_maze, 2)
    dz_maze = round((zmax - zmin) / nz_maze, 2)

    # convert pos to node
    nx0 = int(round((x - xmin) / dx_maze - 0.5, 0))
    nz0 = int(round((z - zmin) / dz_maze - 0.5, 0))

    # correct node if necessary
    if nx0 > 49:
        nx0 = 49
    elif nx0 < 0:
        nx0 = 0

    if nz0 > 49:
        nz0 = 49
    elif nz0 < 0:
        nz0 = 0

    # search for OK node
    if maze[(nz0, nx0)] == 1:
        search = True
        k = 1
        while search:
            for i in range(-k, k + 1):
                for j in range(-k, k + 1):

                    nz_temp = nz0 + j
                    nx_temp = nx0 + i

                    if nx_temp > 49:
                        nx_temp = 49
                    elif nx_temp < 0:
                        nx_temp = 0

                    if nz_temp > 49:
                        nz_temp = 49
                    elif nz_temp < 0:
                        nz_temp = 0

                    node_temp = (nz_temp, nx_temp)
                    if maze[node_temp] == 0:
                        node = node_temp
                        x = round((node[1] + 0.5) * dx_maze + xmin, 0)
                        z = round((node[0] + 0.5) * dz_maze + zmin, 0)
                        search = False
                    if search is False: break
                if search is False: break
            k += 1
    return (x, z)


# subfunction of get_missionXML (return script for agent start location)
def get_Placement(pInc, mapExt, iPos):
    x = iPos[0]
    z = iPos[1]

    xMin = mapExt[0]
    xMax = mapExt[1]
    zMin = mapExt[2]
    zMax = mapExt[3]

    if x != 0 or z != 0:
        xStart = x
        yStart = 5.5
        zStart = z
        yawStart = 90
    else:
        random.seed(pInc)
        xStart = random.randint(xMin, xMax) + 0.5
        zStart = random.randint(zMin, zMax) + 0.5
        yStart = 5.5
        yawStart = 90

    (xStart, zStart) = nearest_pos((xStart, zStart))
    ans = write_Placement(xStart, yStart, zStart, yawStart)
    ans = '\t' + textwrap.dedent(ans)
    return ans


# subfunction of get_missionXML (return script for drawing item)
def write_DrawItem(xTemp, yGround, zTemp, itemTemp):
    return '\t\t\t\t<DrawItem x="' + str(xTemp) + '" y="' + str(yGround) + '" z="' + str(
        zTemp) + '" type="' + itemTemp + '"/>\n'


# subfunction of get_missionXML (return script for drawing item)
def get_DrawItem(id_item, sLoc_item, mapLim, pRan, mapExt):
    xz = get_xz(sLoc_item[0], mapLim, pRan, mapExt)
    xTemp = xz[0]
    yTemp = 4
    zTemp = xz[1]
    ans = write_DrawItem(xTemp, yTemp, zTemp, id_item[0])
    ans = '\t' + textwrap.dedent(ans)

    for i in range(1, len(id_item)):
        itemTemp = id_item[i]
        xz = get_xz(sLoc_item[i], mapLim, pRan, mapExt)
        xTemp = xz[0]
        yTemp = 5
        zTemp = xz[1]
        ans += write_DrawItem(xTemp, yTemp, zTemp, itemTemp)
    return ans


# subfunction of get_missionXML (return script for drawing block)
def write_DrawBlock(xTemp, yGround, zTemp, blockTemp):
    return '\t\t\t\t<DrawBlock x="' + str(xTemp) + '" y="' + str(yGround) + '" z="' + str(
        zTemp) + '" type="' + blockTemp + '"/>\n'


# subfunction of get_missionXML (return script for drawing block)
def get_DrawBlock(id_block, sLoc_block, mapLim, pRan, mapExt, problemList):
    xz = get_xz(sLoc_block[0], mapLim, pRan, mapExt)
    xTemp = xz[0]
    yTemp = 4
    zTemp = xz[1]

    if id_block[0] in problemList: id_block = 'air'

    ans = write_DrawBlock(xTemp, yTemp, zTemp, id_block[0])
    ans = '\t' + textwrap.dedent(ans)

    for i in range(1, len(id_block)):
        blockTemp = id_block[i]
        if blockTemp not in problemList:
            xz = get_xz(sLoc_block[i], mapLim, pRan, mapExt)
            xTemp = xz[0]
            yTemp = 5
            zTemp = xz[1]
            ans += write_DrawBlock(xTemp, yTemp, zTemp, blockTemp)
    return ans


# subfunction of get_missionXML (return script for changing ground within location boundaries, ie stone -> grass)
def change_ground(id_block, sLoc, mapLim, pRan, mapExt, y=3):
    ans = ''
    if sLoc in mapLim.index.values:
        # determine limits of location
        xmin = mapLim.loc[sLoc, 'xmin']
        xmax = mapLim.loc[sLoc, 'xmax']
        zmin = mapLim.loc[sLoc, 'zmin']
        zmax = mapLim.loc[sLoc, 'zmax']
        for i in range(xmin + 3, xmax - 3):
            for k in range(zmin + 3, zmax - 3):
                ans += write_DrawBlock(i, y, k, id_block)
    return ans


# subfunction of get_missionXML (return script for changing specified volume, useful for map re-construction)
def change_section(id_block, xmin, xmax, ymin, ymax, zmin, zmax):
    ans = ''
    for i in range(xmin, xmax + 1):
        for j in range(ymin, ymax + 1):
            for k in range(zmin, zmax + 1):
                ans += write_DrawBlock(i, j, k, id_block)
    return ans


# function (return mission specs for malmo input)
def get_missionXML(pSet, pRan, pInc, iPos, iTrial):
    # item locations
    mapSim = pd.read_excel('dat/truth.xlsx')

    mapSim_item = mapSim[mapSim.type == 'ItemType']
    mapSim_block = mapSim[mapSim.type == 'BlockType']

    id_item = mapSim_item.name.tolist()
    id_block = mapSim_block.name.tolist()

    col = 's' + str(pSet) + '_loc'
    sLoc_item = mapSim_item[col].tolist()
    sLoc_block = mapSim_block[col].tolist()

    # remove duplicates
    id_item2 = list(set(id_item))
    id_item2.sort()
    id_block2 = list(set(id_block))
    id_block2.sort()

    sLoc_item2 = []
    sLoc_block2 = []

    for x in id_item2:
        ix = id_item.index(x)
        temp = sLoc_item[ix]
        sLoc_item2.append(temp)

    for x in id_block2:
        ix = id_block.index(x)
        temp = sLoc_block[ix]
        sLoc_block2.append(temp)

    del mapSim, mapSim_item, mapSim_block

    # map coordinates
    mapLim = pd.read_excel('dat/map.xlsx')
    mapLim = mapLim[mapLim.set < (pSet + 1)]
    mapLim = mapLim.drop(columns=['set'])
    mapLim = mapLim.set_index('loc')
    xmin = mapLim.iloc[-1, 0]
    xmax = mapLim.iloc[-1, 1]
    zmin = mapLim.iloc[-1, 2]
    zmax = mapLim.iloc[-1, 3]
    mapExt = [xmin, xmax, zmin, zmax]
    mapLim = mapLim[:-1]

    # problematic items (agent gets stuck)
    problemList = ['water', 'lava', 'web', 'gray_shulker_box', 'green_shulker_box', 'gray_shulker_box',
                   'light_blue_shulker_box',
                   'lime_shulker_box', 'magenta_shulker_box', 'orange_shulker_box', 'pink_shulker_box',
                   'purple_shulker_box',
                   'red_shulker_box', 'silver_shulker_box', 'white_shulker_box', 'yellow_shulker_box',
                   'blue_shulker_box',
                   'brown_shulker_box', 'cyan_shulker_box']

    random.seed(pInc)

    ans = '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
                <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

                  <About>
                    <Summary>Hello World</Summary>
                  </About>

                <ServerSection>
                  <ServerInitialConditions>
                    <Time>
                        <StartTime>6000</StartTime>
                        <AllowPassageOfTime>false</AllowPassageOfTime>
                    </Time>
                    <Weather>clear</Weather>
                  </ServerInitialConditions>
                  <ServerHandlers>
                      <FileWorldGenerator src="C:/Users/Christopher McClurg/malmo/Minecraft/run/saves/small_town" />                      
                      <DrawingDecorator>     
                          ''' + change_ground('glowstone', 'landfill', mapLim, pRan, mapExt, 3) + '''    
                          ''' + change_ground('dirt', 'garden', mapLim, pRan, mapExt, 3) + '''                           
                          ''' + change_ground('red_flower', 'garden', mapLim, pRan, mapExt, 4) + '''    
                          ''' + change_ground('dirt', 'farm', mapLim, pRan, mapExt, 3) + ''' 
                          ''' + change_section('fence', 109, 112, 4, 4, 781, 781) + '''  
                          ''' + change_section('iron_bars', 166, 169, 4, 6, 719, 719) + '''  
                          ''' + change_section('iron_bars', 183, 183, 4, 6, 732, 736) + '''  
                          ''' + change_section('iron_bars', 107, 110, 4, 5, 721, 721) + '''  
                          ''' + change_section('iron_bars', 110, 110, 4, 5, 721, 725) + '''
                          ''' + change_section('dirt', 115, 122, 3, 3, 725, 725) + '''  
                          ''' + change_section('grass', 117, 177, 3, 3, 722, 722) + '''  
                          ''' + change_section('stone', 115, 115, 3, 3, 727, 740) + '''  
                          ''' + change_section('stone', 116, 122, 3, 3, 726, 726) + '''  
                          ''' + change_section('stone', 111, 114, 3, 3, 734, 734) + '''  
                          ''' + change_section('double_stone_slab', 107, 115, 3, 3, 741, 748) + '''  
                          ''' + change_section('double_stone_slab', 756, 764, 3, 3, 722, 722) + '''  
                          ''' + change_section('stone', 143, 154, 3, 3, 756, 764) + '''  
                          ''' + change_section('air', 107, 114, 4, 4, 742, 747) + '''  
                          ''' + change_section('red_flower', 115, 122, 4, 4, 725, 725) + '''  
                          ''' + change_section('air', 115, 127, 4, 4, 717, 723) + '''  
                          ''' + change_section('air', 115, 125, 4, 5, 722, 722) + '''  
                          ''' + change_section('air', 125, 125, 4, 5, 723, 723) + '''  
                          ''' + change_section('air', 126, 126, 4, 5, 724, 724) + ''' 
                          ''' + change_section('air', 127, 127, 4, 5, 725, 725) + '''  
                          ''' + change_section('iron_bars', 124, 127, 4, 5, 726, 726) + '''  
                          ''' + change_section('fence', 107, 109, 4, 4, 741, 741) + '''  
                          ''' + change_section('fence', 115, 115, 4, 4, 742, 747) + '''  
                          ''' + change_section('lime_shulker_box', 119, 119, 4, 5, 741, 741) + '''  
                          ''' + change_section('lime_shulker_box', 123, 123, 4, 5, 735, 735) + '''  
                          ''' + change_section('iron_bars', 103, 103, 4, 5, 721, 725) + '''  
                          ''' + change_section('iron_bars', 96, 96, 4, 5, 722, 724) + '''  
                          ''' + change_section('fence', 65, 67, 4, 4, 733, 733) + '''  
                          ''' + change_section('fence', 65, 67, 4, 4, 740, 740) + '''  
                          ''' + change_section('fence', 64, 70, 4, 4, 770, 770) + '''  
                          ''' + change_section('fence', 64, 70, 4, 4, 767, 767) + '''  
                          ''' + change_section('fence_gate', 98, 99, 4, 4, 781, 781) + '''  
                          ''' + change_section('fence_gate', 119, 122, 4, 4, 781, 781) + '''  
                          ''' + change_section('iron_bars', 152, 154, 4, 5, 764, 764) + '''  
                          ''' + change_section('iron_bars', 143, 143, 4, 5, 761, 763) + '''  
                          ''' + change_section('iron_bars', 137, 140, 4, 5, 696, 696) + '''  
                          ''' + change_section('air', 167, 167, 4, 7, 700, 700) + '''  
                          ''' + change_section('air', 170, 170, 4, 7, 700, 700) + '''  
                          ''' + change_section('sandstone', 170, 170, 4, 6, 699, 703) + '''  
                          ''' + change_section('air', 170, 170, 6, 6, 702, 703) + '''                            
                          ''' + change_section('sandstone', 167, 167, 4, 6, 699, 703) + '''  
                          ''' + change_section('air', 167, 167, 6, 6, 702, 703) + '''                            
                          ''' + change_section('fence', 131, 147, 4, 4, 658, 658) + '''  
                          ''' + change_section('fence_gate', 142, 144, 4, 4, 658, 658) + '''  
                          ''' + change_section('fence_gate', 134, 135, 4, 4, 658, 658) + '''  
                          ''' + change_section('fence', 131, 140, 4, 4, 654, 654) + '''  
                          ''' + change_section('fence', 140, 140, 4, 4, 652, 654) + '''        
                          ''' + change_section('planks', 90, 102, 3, 3, 725, 735) + ''' 
                          ''' + change_section('air', 133, 133, 4, 5, 720, 726) + '''                              
                          ''' + change_section('iron_bars', 133, 135, 4, 5, 727, 727) + '''        
                          ''' + change_section('iron_bars', 153, 155, 4, 5, 728, 728) + '''                                      
                          ''' + change_section('air', 141, 142, 4, 5, 651, 651) + '''                              
                          ''' + change_section('stone', 99, 99, 3, 3, 723, 723) + '''    
                          ''' + change_section('fence_gate', 171, 171, 4, 4, 670, 670) + '''
                          ''' + change_section('planks', 168, 173, 4, 5, 674, 674) + '''    
                          ''' + change_section('planks', 177, 177, 4, 5, 670, 670) + '''    
                          ''' + change_section('stone', 168, 173, 3, 3, 671, 673) + '''                              
                          ''' + change_section('air', 138, 139, 4, 5, 692, 692) + '''    
                          ''' + change_section('air', 69, 69, 5, 6, 661, 661) + '''    
                          ''' + change_section('air', 71, 71, 5, 6, 736, 737) + '''    
                          ''' + change_section('air', 71, 71, 4, 5, 768, 769) + '''    
                          ''' + change_section('air', 141, 142, 4, 5, 651, 651) + '''    
                          ''' + change_section('air', 148, 148, 4, 6, 646, 650) + '''    
                          ''' + change_section('air', 149, 154, 4, 6, 646, 646) + '''    
                          ''' + change_section('air', 149, 154, 4, 7, 657, 657) + '''    
                          ''' + change_section('air', 97, 98, 4, 6, 726, 734) + '''         
                          ''' + change_section('brick_block', 98, 102, 4, 10, 725, 725) + '''       
                          ''' + change_section('brick_block', 102, 102, 4, 10, 726, 734) + '''       
                          ''' + change_section('wooden_slab', 99, 102, 11, 11, 724, 736) + '''      
                          ''' + change_section('air', 99, 101, 4, 5, 725, 725) + '''        
                          ''' + change_section('air', 99, 101, 4, 6, 733, 733) + '''      
                          ''' + change_section('air', 99, 101, 6, 6, 728, 732) + '''                                                                                                                                                                                                                                                                                                                                                                                                                              
                          ''' + change_section('air', 29, 31, 5, 7, 752, 754) + '''    
                          ''' + change_section('air', 45, 45, 5, 7, 755, 757) + '''    
                          ''' + change_section('brick_block', 19, 24, 5, 9, 750, 750) + '''    
                          ''' + change_section('brick_block', 98, 102, 4, 10, 735, 735) + '''  
                          ''' + change_section('fence', 200, 225, 4, 4, 745, 745) + '''  
                          ''' + change_section('fence', 225, 225, 4, 4, 745, 775) + '''    
                          ''' + change_section('fence', 200, 225, 4, 4, 775, 775) + '''    
                          ''' + change_section('fence', 200, 200, 4, 4, 765, 775) + '''    
                          ''' + change_section('fence', 200, 200, 4, 4, 745, 755) + '''    
                          ''' + change_section('sandstone', 28, 28, 5, 6, 752, 753) + '''     
                          ''' + change_section('planks', 25, 42, 3, 3, 679, 696) + '''   
                          ''' + change_section('yellow_flower', 10, 44, 4, 4, 660, 665) + ''' 
                          ''' + change_section('yellow_flower', 10, 44, 4, 4, 650, 655) + '''  
                          ''' + change_section('yellow_flower', 10, 44, 4, 4, 640, 645) + '''   
                          ''' + change_section('red_flower', 10, 44, 4, 4, 655, 660) + '''   
                          ''' + change_section('red_flower', 10, 44, 4, 4, 645, 650) + '''   
                          ''' + change_section('red_flower', 10, 44, 4, 4, 635, 640) + '''        
                          ''' + change_section('air', 71, 71, 5, 7, 734, 739) + '''   
                          ''' + change_section('air', 68, 70, 5, 7, 739, 739) + '''   
                          ''' + change_section('air', 68, 70, 5, 7, 734, 734) + '''   
                          ''' + change_section('brick_block', 68, 68, 5, 7, 734, 739) + '''   
                          ''' + change_section('air', 68, 68, 5, 6, 736, 737) + '''   
                          ''' + change_section('wooden_slab', 68, 70, 8, 8, 735, 738) + '''                         
                          ''' + change_section('blue_shulker_box', 155, 155, 3, 3, 615, 615) + '''    
                          ''' + change_section('blue_shulker_box', 159, 159, 3, 3, 613, 613) + '''    
                          ''' + change_section('blue_shulker_box', 159, 159, 3, 3, 615, 615) + '''                             
                          ''' + change_section('blue_shulker_box', 147, 147, 3, 3, 609, 610) + '''    
                          ''' + change_section('blue_shulker_box', 147, 147, 3, 3, 615, 615) + '''    
                          ''' + change_section('blue_shulker_box', 147, 147, 3, 3, 617, 619) + '''    
                          ''' + change_section('blue_shulker_box', 148, 148, 3, 3, 609, 619) + '''    
                          ''' + change_section('blue_shulker_box', 149, 149, 3, 3, 608, 611) + '''    
                          ''' + change_section('blue_shulker_box', 149, 149, 3, 3, 613, 620) + '''                             
                          ''' + change_section('blue_shulker_box', 150, 154, 3, 3, 608, 621) + '''    
                          ''' + change_section('blue_shulker_box', 157, 162, 3, 3, 624, 624) + '''    
                          ''' + change_section('blue_shulker_box', 157, 164, 3, 3, 623, 623) + '''    
                          ''' + change_section('blue_shulker_box', 156, 164, 3, 3, 622, 622) + '''    
                          ''' + change_section('blue_shulker_box', 153, 154, 3, 3, 622, 622) + '''    
                          ''' + change_section('blue_shulker_box', 155, 165, 3, 3, 621, 621) + '''    
                          ''' + change_section('blue_shulker_box', 150, 159, 3, 3, 608, 608) + '''    
                          ''' + change_section('blue_shulker_box', 161, 165, 3, 3, 608, 608) + '''    
                          ''' + change_section('blue_shulker_box', 161, 165, 3, 3, 607, 607) + '''    
                          ''' + change_section('blue_shulker_box', 163, 165, 3, 3, 606, 606) + '''    
                          ''' + change_section('blue_shulker_box', 156, 159, 3, 3, 607, 607) + '''    
                          ''' + change_section('blue_shulker_box', 151, 154, 3, 3, 607, 607) + '''    
                          ''' + change_section('blue_shulker_box', 166, 166, 3, 3, 613, 619) + '''    
                          ''' + change_section('blue_shulker_box', 160, 165, 3, 3, 609, 620) + '''    
                          ''' + change_section('blue_shulker_box', 155, 159, 3, 3, 609, 612) + '''    
                          ''' + change_section('blue_shulker_box', 155, 159, 3, 3, 616, 620) + '''    
                          ''' + change_section('air', 72, 80, 5, 8, 724, 749) + '''    
                          ''' + change_section('air', 72, 74, 4, 6, 764, 768) + '''    
                          ''' + change_section('air', 163, 175, 5, 8, 682, 697) + '''    
                          ''' + change_section('air', 168, 169, 5, 6, 698, 698) + '''    
                          ''' + change_section('green_shulker_box', 110, 110, 4, 7, 726, 733) + '''    
                          ''' + change_section('green_shulker_box', 111, 111, 4, 8, 726, 726) + '''    
                          ''' + change_section('air', 115, 115, 4, 6, 727, 740) + '''    
                          ''' + change_section('air', 112, 114, 4, 6, 741, 741) + '''    
                          ''' + change_section('air', 111, 114, 4, 6, 734, 734) + '''    
                          ''' + change_section('air', 144, 154, 4, 5, 756, 760) + '''    
                          ''' + change_section('air', 137, 150, 4, 6, 730, 737) + '''    
                          ''' + change_section('air', 146, 149, 5, 7, 764, 764) + '''    
                          ''' + change_section('air', 144, 144, 5, 8, 765, 769) + '''   
                          ''' + change_section('air', 139, 139, 5, 8, 765, 769) + '''    
                          ''' + change_section('air', 139, 144, 5, 8, 770, 770) + '''    
                          ''' + change_section('planks', 139, 144, 4, 4, 765, 770) + '''    
                          ''' + change_section('brick_block', 140, 143, 4, 8, 764, 764) + '''  
                          ''' + change_section('brick_block', 140, 143, 4, 8, 764, 764) + '''  
                          ''' + change_section('glass_pane', 148, 149, 4, 5, 738, 738) + '''  
                          ''' + change_section('glass_pane', 138, 139, 4, 5, 738, 738) + '''  
                          ''' + change_section('glass_pane', 145, 150, 4, 6, 729, 729) + '''  
                          ''' + change_section('grass', 146, 149, 3, 3, 724, 728) + ''' 
                          ''' + change_section('air', 25, 29, 5, 9, 752, 754) + '''   
                          ''' + change_section('glass_pane', 26, 27, 5, 7, 761, 761) + '''  
                          ''' + change_section('glass_pane', 137, 143, 8, 10, 728, 728) + '''  
                          ''' + change_section('glass_pane', 137, 150, 4, 6, 738, 738) + '''  
                          ''' + change_section('air', 136, 143, 7, 7, 726, 726) + '''  
                          ''' + change_section('fence', 185, 185, 4, 4, 656, 656) + '''  
                          ''' + change_section('air', 115, 115, 7, 11, 727, 740) + '''  
                          ''' + change_section('air', 111, 114, 7, 8, 734, 734) + '''  
                          ''' + change_section('air', 112, 114, 9, 9, 734, 734) + '''  
                          ''' + change_section('glass_pane', 116, 122, 4, 7, 726, 726) + '''  
                          ''' + change_section('green_shulker_box', 111, 114, 7, 8, 726, 726) + '''  
                          ''' + change_section('green_shulker_box', 112, 114, 9, 9, 726, 726) + ''' 
                          ''' + change_section('glass_pane', 116, 122, 4, 7, 741, 741) + '''   
                          ''' + change_section('air', 63, 63, 4, 4, 766, 771) + '''     
                          ''' + change_section('air', 64, 64, 4, 5, 771, 780) + '''
                          ''' + change_section('fence', 64, 64, 4, 4, 771, 780) + '''
                          ''' + change_section('air', 64, 64, 4, 5, 757, 766) + '''
                          ''' + change_section('fence', 64, 64, 4, 4, 757, 766) + '''
                          ''' + change_section('planks', 140, 143, 9, 9, 760, 769) + '''
                          ''' + change_section('planks', 132, 144, 9, 9, 760, 763) + '''
                          ''' + change_section('fence', 132, 144, 10, 10, 760, 760) + '''
                          ''' + change_section('fence', 144, 144, 10, 10, 760, 763) + '''
                          ''' + change_section('fence', 132, 132, 10, 10, 760, 763) + '''
                          ''' + change_section('grass', 87, 89, 3, 3, 757, 783) + '''
                          ''' + change_section('planks', 87, 89, 4, 5, 756, 756) + '''
                          ''' + change_section('planks', 87, 89, 4, 5, 781, 781) + '''
                          ''' + change_section('air', 86, 86, 4, 5, 757, 780) + '''
                          ''' + change_section('air', 69, 83, 10, 12, 762, 775) + '''
                          ''' + change_section('air', 91, 92, 4, 6, 728, 730) + '''
                          ''' + change_section('air', 149, 150, 5, 8, 768, 772) + '''
                          ''' + change_section('air', 71, 81, 7, 7, 763, 773) + '''
                          ''' + change_section('air', 81, 86, 4, 11, 763, 773) + '''
                          ''' + change_section('planks', 82, 88, 3, 3, 763, 773) + '''
                          ''' + change_section('sandstone', 81, 88, 4, 8, 763, 763) + '''
                          ''' + change_section('sandstone', 81, 88, 4, 8, 774, 774) + '''
                          ''' + change_section('sandstone', 71, 71, 7, 8, 764, 773) + '''
                          ''' + change_section('sandstone', 72, 80, 7, 8, 763, 763) + '''
                          ''' + change_section('sandstone', 70, 70, 7, 7, 767, 770) + '''
                          ''' + change_section('air', 70, 71, 6, 6, 768, 769) + '''
                          ''' + change_section('stone', 69, 88, 9, 9, 761, 776) + '''
                          ''' + change_section('glass_pane', 88, 88, 4, 8, 764, 773) + '''
                          ''' + change_section('sandstone', 69, 69, 8, 8, 762, 775) + '''
                          ''' + change_section('red_shulker_box', 85, 87, 3, 3, 764, 773) + '''
                          ''' + change_section('red_shulker_box', 71, 84, 3, 3, 768, 769) + '''
                          ''' + change_section('fence', 143, 143, 4, 4, 652, 656) + '''
                          ''' + change_section('fence', 144, 144, 4, 4, 656, 656) + '''
                          ''' + change_section('fence', 144, 144, 4, 4, 657, 657) + '''
                          ''' + change_section('air', 139, 140, 4, 6, 648, 648) + '''
                          ''' + change_section('oak_stairs', 139, 139, 4, 4, 648, 648) + '''
                          ''' + change_section('glass', 138, 138, 5, 6, 648, 648) + '''
                          ''' + change_section('air', 138, 141, 4, 6, 728, 728) + '''
                          ''' + change_section('stonebrick', 138, 141, 3, 3, 727, 727) + '''
                          ''' + change_section('stonebrick', 137, 150, 3, 3, 728, 738) + '''
                          ''' + change_section('grass', 63, 65, 3, 3, 632, 634) + '''
                          ''' + change_section('air', 67, 69, 5, 8, 659, 663) + '''
                          ''' + change_section('glass', 66, 66, 5, 7, 637, 696) + '''
                          ''' + change_section('stone', 66, 66, 8, 8, 637, 696) + '''
                          ''' + change_section('stone', 66, 66, 5, 7, 659, 663) + '''
                          ''' + change_section('air', 66, 66, 5, 7, 660, 662) + '''
                          ''' + change_section('stone', 66, 66, 5, 7, 636, 636) + '''
                          ''' + change_section('stone', 67, 110, 8, 8, 636, 636) + '''
                          ''' + change_section('stone', 110, 110, 5, 7, 636, 636) + '''
                          ''' + change_section('glass', 67, 109, 5, 7, 636, 636) + '''
                          ''' + change_section('glass', 103, 103, 5, 7, 637, 693) + '''
                          ''' + change_section('stone', 103, 103, 8, 8, 637, 693) + '''
                          ''' + change_section('stone', 103, 103, 5, 8, 636, 636) + '''
                          ''' + change_section('stone', 103, 103, 5, 8, 649, 649) + '''

                          ''' + get_DrawItem(id_item2, sLoc_item2, mapLim, pRan, mapExt) + '''
                          ''' + get_DrawBlock(id_block2, sLoc_block2, mapLim, pRan, mapExt, problemList) + '''
                      </DrawingDecorator>
                      <ServerQuitFromTimeUp timeLimitMs="600000"/>
                      <ServerQuitWhenAnyAgentFinishes/>
                    </ServerHandlers>
                  </ServerSection>
                  <AgentSection mode="Creative">
                    <Name>ROBOT</Name>
                    <AgentStart>
                        ''' + get_Placement(pInc, mapExt, iPos) + '''
                    </AgentStart>
                    <AgentHandlers>
                      <ObservationFromFullStats/>
                      <ObservationFromNearbyEntities>
                          <Range name="item_obs" xrange="3" yrange="1" zrange="3"/>
                      </ObservationFromNearbyEntities> 
                      <ObservationFromGrid>
                          <Grid name="block_obs">
                              <min x="-3" y="-1" z="-3"/>
                              <max x="3" y="1" z="3"/>
                          </Grid>
                      </ObservationFromGrid>                      
                      <ContinuousMovementCommands turnSpeedDegs="480"/>
                      <AgentQuitFromReachingPosition>
                          <Marker tolerance="5" x="0"   y="4" z="620"/>      
                          <Marker tolerance="5" x="0"   y="4" z="710"/>   
                          <Marker tolerance="5" x="50"  y="4" z="595"/>                      
                          <Marker tolerance="5" x="50"  y="4" z="790"/>    
                          <Marker tolerance="5" x="120" y="4" z="595"/>      
                          <Marker tolerance="5" x="190" y="4" z="595"/>      
                          <Marker tolerance="5" x="200" y="4" z="790"/>   
                          <Marker tolerance="5" x="220" y="4" z="635"/>                      
                          <Marker tolerance="5" x="220" y="4" z="710"/>  
                      </AgentQuitFromReachingPosition>
                    </AgentHandlers>
                  </AgentSection>
                </Mission>'''
    return ans
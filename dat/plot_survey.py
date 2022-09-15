import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

unique_only = True

#similar locations
df = pd.read_excel('truth.xlsx')
id_item = df.name.tolist()
s0 = df['s0_loc'].tolist()
s1 = df['s1_loc'].tolist()
s2 = df['s2_loc'].tolist()

if unique_only:
    
    s0_new = []
    s1_new = []
    s2_new = []
    
    #remove duplicates
    id_item2 = list(set(id_item))
    id_item2.sort()
    simLoc2 = []
    
    for x in id_item2:
        ix = id_item.index(x)
        temp0 = s0[ix]
        s0_new.append(temp0)
        temp1 = s1[ix]
        s1_new.append(temp1)
        temp2 = s2[ix]
        s2_new.append(temp2)

    s0 = s0_new.copy()
    s1 = s1_new.copy()
    s2 = s2_new.copy()

def get_frequency(my_list):
    freq = {}
    for item in my_list:
        if (item in freq):
            freq[item] += 1
        else:
            freq[item] = 1
    ans = {k: v for k, v in sorted(freq.items(), key=lambda item: item[1])}
    return ans

f0 = get_frequency(s0)
f0['farm'] = 0
f0['bedroom'] = 0
f0['gas station'] = 0
f0['store'] = 0
f0['office'] = 0
f0['school'] = 0
f0['garden'] = 0
f0['kitchen'] = 0
f0['museum'] = 0
f0['post office'] = 0
f0['library'] = 0
f0['hospital'] = 0


f1 = get_frequency(s1)
f1['garden'] = 0
f1['kitchen'] = 0
f1['museum'] = 0
f1['post office'] = 0
f1['library'] = 0
f1['hospital'] = 0
f1['brewery'] = 0


f2 = get_frequency(s2)
f2['brewery'] = 0
f2['post office'] = 0


pLoc = ['brewery', 'lake', 'house', 'landfill', 'church','restaurant','farm','bedroom',
        'gas station','store','office','school','garden','kitchen','museum','post office',
        'library', 'hospital']

pLoc_label = ['1 landfill','2 lake','3 restaurant','4 brewery','5 house','6 church','7 farm','8 gas station',
             '9 store','10 school','11 office','12 bedroom','13 museum','14 garden','15 hospital',
             '16 library','17 kitchen','18 post office']

pLoc_sort = ['landfill','lake','restaurant','brewery','house','church','farm','gas station',
             'store','school','office','bedroom','museum','garden','hospital',
             'library','kitchen','post office']
pLoc.sort()

index_map = {v: i for i, v in enumerate(pLoc_sort)}

#plot frequencies
fig = plt.figure()
ax = fig.add_subplot(111)
plt.style.use('classic')
plt.rc('font',family='Times New Roman')   
fig.patch.set_facecolor('white')


#t2 = sorted(f2.items())
t2 = sorted(f2.items(), key=lambda pair: index_map[pair[0]])
[x2, y2] = zip(*t2)
y2 = list(y2)
y2 = [x/len(id_item2) for x in y2]

#t1 = sorted(f1.items())
t1 = sorted(f1.items(), key=lambda pair: index_map[pair[0]])
[x1, y1] = zip(*t1)
y1 = list(y1)
y1 = [x/len(id_item2) for x in y1]


#t0 = sorted(f0.items())
t0 = sorted(f0.items(), key=lambda pair: index_map[pair[0]])
[x0, y0] = zip(*t0)
y0 = list(y0)
y0 = [x/len(id_item2) for x in y0]

N = 18
ind = np.arange(18)*2 - 1
width = 0.5  

plt.title('Item Distribution (Portion of Total Count)')
plt.barh(ind-width, y0, width, label = 'set 0')
plt.barh(ind, y1, width, label = 'set 1')
plt.barh(ind+width, y2, width, label = 'set 2')
plt.yticks(ind, pLoc_label)
#plt.legend(loc='lower right')
plt.gca().invert_yaxis()
Xmajor_ticks = np.arange(0, 1, 0.1)
Xminor_ticks = np.arange(0, 1, 0.05)
ax.set_xticks(Xmajor_ticks)
ax.set_xticks(Xminor_ticks, minor=True)
ax.grid(which='minor', alpha=0.6, color ='black')
ax.grid(which='major', alpha=0.6, color ='black')
plt.xlim(0, 0.5)
#.zlim(-1, 35)
plt.show()




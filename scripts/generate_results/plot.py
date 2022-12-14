import matplotlib.pyplot as plt
import seaborn as sns;

sns.set()
import pandas as pd
import numpy as np
from ast import literal_eval
from datetime import datetime
import matplotlib
import os
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

now = datetime.now()
d0 = now.strftime('%m_%d_%Y')
d1 = now.strftime('%H_%M_%S')

plt.rcParams.update(plt.rcParamsDefault)
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'serif'

df = pd.read_excel('./results/data/11_02_2022/final_result.xlsx')
df = df[df['status'] == 'complete']
df = df[df['mod'] == 1]
df = df.iloc[:, 5:-1]

df.obsInc = df.obsInc.apply(literal_eval)
df.accInc = df.accInc.apply(literal_eval)
df.runTimeInc = df.runTimeInc.apply(literal_eval)
df.runDistInc = df.runDistInc.apply(literal_eval)

dList = list(set(df['data']))
pList = list(set(df['bias']))
bList = list(set(df['learner']))

avg_acc = []
avg_obs = []
avg_tRun = []
avg_tTrain = []
avg_tTrainIt = []

std_acc = []
std_obs = []
std_tRun = []
std_tTrain = []
std_tTrainIt = []

labels = []
x0 = []
datum = []

for d in dList:
    for p in pList:
        for b in bList:

            temp = df[(df['data'] == d) & (df['bias'] == p) & (df['learner'] == b)]

            if len(temp) > 0:
                x = np.array(list(temp.obsInc))
                avg = np.mean(x, axis=0)
                std = np.std(x, axis=0)
                avg_obs.append(avg)
                std_obs.append(std)

                x = np.array(list(temp.accInc))
                avg = np.mean(x, axis=0) * 100
                std = np.std(x, axis=0) * 100
                avg_acc.append(avg)
                std_acc.append(std)

                x = np.array(list(temp.runTimeInc))
                avg = np.mean(x, axis=0) / 60
                std = np.std(x, axis=0) / 60
                avg_tRun.append(avg)
                std_tRun.append(std)

                x = [i for i in range(len(avg))]
                x0.append(x)

                if p == 'random':           p = 'uniform'
                if p == 'classWt':          p = 'low class weight'
                if p == 'clusterWt':        p = 'low cluster weight'

                label = b + ' ' + p
                labels.append(label)

                datum.append(d)

del x, avg, std, label, d, dList, p, pList, b, bList, temp

# -----------------------------------------------------------------------------
# PLOT 1
# fig, ((ax1,ax2), (ax3,ax4)) = plt.subplots(2, 2, sharex = 'col', sharey = 'row', figsize=(10,7))
fig, (ax1, ax2) = plt.subplots(1, 2, sharex='col', sharey='row', figsize=(10, 5))
plt.rcParams.update(plt.rcParamsDefault)
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'serif'

def manual_plot(ax, x, y, e, pProps, pLabel):
    x = np.array(x)
    y = np.array(y)
    e = np.array(e)
    col = pProps[0]
    lin = pProps[1]
    mar = pProps[2]
    marSize = pProps[3]
    if len(x) == 241:
        skipper = 20
    else:
        skipper = 8

    ax.plot(x, y, marker=mar, color=col, linestyle=lin, markersize=marSize, markevery=skipper, linewidth=1.5,
            label=pLabel, zorder=10, clip_on=False)
    ax.fill_between(x, y - e, y + e, color=col, alpha=0.25, zorder=-1, linewidth=0.0)


def get_props(name, d):
    blue = sns.color_palette()[0]
    orange = sns.color_palette()[1]
    green = sns.color_palette()[2]
    red = sns.color_palette()[3]
    purple = sns.color_palette()[4]
    brown = sns.color_palette()[5]
    pink = sns.color_palette()[6]
    grey = sns.color_palette()[7]
    gold = sns.color_palette()[8]
    aqua = sns.color_palette()[9]
    black = 'black'

    if name == 'CBCLPR low class weight':
        ans = [blue, '-.', 's']
    elif name == 'CBCLPR uniform':
        ans = [green, '--', 'o']
    elif name == 'CBCLPR low cluster weight':
        ans = [purple, ':', '^']
    elif name == 'CBCLPR clusterStdLow':
        ans = [orange, '-.', 's']
    elif name == 'CBCLPR clusterStdHigh':
        ans = [red, '--', 'o']
    elif name == 'SVM uniform':
        ans = [grey, ':', '^']
    else:
        ans = []

    if len(ans) > 0:
        if ans[2] == 's':
            ans.append(4)
        elif ans[2] == 'o':
            ans.append(4)
        elif ans[2] == 'x':
            ans.append(6)
        elif ans[2] == '^':
            ans.append(6)

    return ans, name

cifarList_ya = []
grocList_ya = []

for i in range(len(labels)):

    label = labels[i]
    bias = ' '.join(label.split()[1:])
    d = datum[i].split('-')[0]
    d = d.lower()

    if d == 'cifar':
        N = 241
    else:
        N = 121

    x1 = avg_tRun[i][0:N]
    y1 = avg_acc[i][0:N]
    e1 = std_acc[i][0:N]
    ya = np.mean(y1)
    pProps, label = get_props(label, d)
    lab1 = '($\overline{y} =$ ' + str(np.round(ya, 1)) + ') ' + label

    if (d == 'cifar') and len(pProps) > 0:
        manual_plot(ax1, x1, y1, e1, pProps, lab1)
        cifarList_ya.append(ya)
    elif (d == 'grocery') and len(pProps) > 0:
        manual_plot(ax2, x1, y1, e1, pProps, lab1)
        grocList_ya.append(ya)

H1, L1 = ax1.get_legend_handles_labels()
H2, L2 = ax2.get_legend_handles_labels()

ix1 = list(np.argsort(np.array(cifarList_ya)))
ix2 = list(np.argsort(np.array(grocList_ya)))

H1new = [H1[i] for i in ix1]
H2new = [H2[i] for i in ix2]
L1new = [L1[i] for i in ix1]
L2new = [L2[i] for i in ix2]

ax1.yaxis.get_major_ticks()[0].label1.set_visible(False)
ax2.xaxis.get_major_ticks()[0].label1.set_visible(False)
ax1.legend(H1new, L1new, loc=2, prop={'size': 9})
ax2.legend(H2new, L2new, loc=4, prop={'size': 9})

ax1.set_title('CIFAR-100 (100 random initial images) ', fontweight='bold', size=9)
ax2.set_title('GROCERY STORE (81 random initial images)', fontweight='bold', size=9)
ax1.set_ylabel('Test Prediction Accuracy (%)', fontweight='bold', size=9)

ax1.set_xlabel('Search Time (min)', fontweight='bold', size=9)
ax2.set_xlabel('Search Time (min)', fontweight='bold', size=9)

ax1.set_ylim([0, 65])
ax1.set_xlim([0, 125])
ax2.set_xlim([0, 62.5])

fig.align_ylabels()
plt.subplots_adjust(wspace=0.025, hspace=0.05)

FILENAME = './results/charts/{}/{}_robothor.png'.format(d0, d1)
try:
    os.mkdir('./results/charts/{}'.format(d0))
except:
    pass
plt.savefig(FILENAME, bbox_inches='tight')

plt.show()
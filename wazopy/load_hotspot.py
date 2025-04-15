from scipy.signal import convolve
import numpy as np
import matplotlib.pyplot as plt

filepath = '/Users/eartigau/Downloads/ebird_L5914558__1900_2023_1_12_barchart.txt'

lines = []

ps = []
with open(filepath) as fp:
    line = fp.readline()
    cnt = 1
    while line:
        print("Line {}: {}".format(cnt, line.strip()))
        line = fp.readline()
        if '\t' not in line:
            continue
        if 'sp.' in line:
            continue

        tmp = line.split('\t')
        if len(tmp) !=50:
            continue

        if 'Sample Size:' in line:
            nn = np.array(line.split('Sample Size:')[1].split('\t')[1:-1], dtype=float)
            continue

        if '0.' not in line:
            continue

        p = np.array(line.split('\t')[1:-1], dtype = float)
        ps.append(p)

        cnt += 1
        lines.append(line.strip())

ps = np.array(ps)
col = 10



p2d = np.zeros([50,48])

for ii in range(48):
    pp = ps[:, ii]

    dist = [1]
    for i in range(len(pp)):
        tmp = [1-pp[i],pp[i]]
        dist = convolve(dist,tmp)
    p2d[:,ii] = dist[0:50]


# get a greyscale colormap
cmap = plt.get_cmap('Greys')

plt.imshow(p2d,origin = 'lower',aspect = 'auto', cmap = cmap)
plt.xlabel('Week of the year')
plt.ylabel('Number of species')
#plt.grid(color='b', linestyle='-', linewidth=1)
for i in range(1,12):
    plt.axvline(i*4-.5, color='k', linestyle='-', linewidth=1)

plt.xticks(np.arange(1.5, 48, step=4), ['Jan','Fév','Mar','Avr','Mai','Juin','Juil','Août','Sep','Oct','Nov','Déc'])
plt.show()

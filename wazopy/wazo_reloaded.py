from wazo import get_ebird, exif2csv
from astropy.table import Table, vstack
import numpy as np
from tqdm import tqdm
import os
from urllib.request import urlopen
from imageio import imread
import glob
import shutil
from drag import drag

def bin_image(jpg_file):
    jpg_file = os.path.abspath(jpg_file)
    base = os.path.basename(jpg_file)
    dir =  os.path.dirname(jpg_file)

    outname = dir+'/.'+base.replace('.jpg','.npy')

    try:
        if not os.path.isfile(outname):
            img2 = np.zeros([10,10,3])
            im = np.array(imread(jpg_file))
            sz = im.shape
            binx = sz[0]/10
            biny = sz[1]/10

            for i in range(10):
                for j in range(10):
                    img2[i,j] = np.mean(im[int(i*binx):int( (i+1)*binx),int(j*biny):int((j+1)*biny)])

            print(outname)
            np.save(outname, img2, allow_pickle=True, fix_imports=True)

        return np.load(outname, allow_pickle=True, fix_imports=True)
    except:
        return -1

photodir = '/Users/eartigau/oiseaux3/photodir/320/'
exifdir = '/Users/eartigau/oiseaux3/exifdir/'

if not os.path.isdir(photodir):
    os.mkdir(photodir)

if not os.path.isdir(exifdir):
    os.mkdir(exifdir)


eb = get_ebird(force = False)


# only with catalog numbers
tbl = eb[np.array(eb['ML_CATALOG_NUMBERS'],dtype = str) != 'nan']


for i in tqdm(range(len(tbl)),leave = False):
    ML_CATALOG_NUMBERS = tbl['ML_CATALOG_NUMBERS'][i].split(' ')
    if len(ML_CATALOG_NUMBERS) == 1:
        continue
    for j in range(len(ML_CATALOG_NUMBERS)):
        if j ==0:
            tbl[i]['ML_CATALOG_NUMBERS'] = ML_CATALOG_NUMBERS[j]
        else:
            line = Table(tbl[i])
            line['ML_CATALOG_NUMBERS'] = ML_CATALOG_NUMBERS[j]
            tbl = vstack([tbl,line])


for i in tqdm(range(len(tbl))):
    exiffile = exifdir+tbl['ML_CATALOG_NUMBERS'][i]+'.csv'

    if not os.path.isfile(exiffile):
        tmp = str(urlopen('https://macaulaylibrary.org/asset/'+tbl['ML_CATALOG_NUMBERS'][i]).read())
        tmp = np.array(tmp.split('exifTagCode'))
        tmp =  tmp[[len(t)<500 for t in tmp]]

        tmp = [t.replace(':','') for t in tmp]
        tmp = [t.replace('"','') for t in tmp]
        tmp = [t.replace('},{','') for t in tmp]
        tmp = [t.replace('sec','s') for t in tmp]

        tmp = [t.replace(',description','&&') for t in tmp]
        tmp = [t.replace('\\\\u002F','/') for t in tmp]
        tbl2 = Table()
        for t in tmp:
            if '&&' in t:
                tbl2[t.split('&&')[0]]=[t.split('&&')[1]]

        tbl2.write(exiffile,format = 'ascii.csv')
    else:
        tbl2 = Table.read(exiffile,format = 'ascii.csv')

    for key in tbl2.keys():
        if key not in tbl.keys():
            tbl[key] = np.zeros(len(tbl),dtype = 'U99')
        tbl[key][i] = tbl2[key][0]


full_res_files = np.array(glob.glob('/Users/eartigau/oiseaux3/oiseaux_originaux/full_resolution/*.jpg'))

full_res_files = full_res_files[[os.path.basename(f).split('.')[0] not in tbl['ML_CATALOG_NUMBERS'] for f in \
        full_res_files]]
full_res_files = full_res_files[np.argsort(np.random.rand(len(full_res_files)))]

rgb = np.zeros([len(tbl), 3])
for i in tqdm(range(len(tbl)), leave=False):
    url = 'https://cdn.download.ams.birds.cornell.edu/api/v1/asset/{}/320'.format(tbl['ML_CATALOG_NUMBERS'][i])
    out = photodir + tbl['ML_CATALOG_NUMBERS'][i] + '.jpg'
    if not os.path.isfile(out):
        cmd = 'wget {} -O {}'.format(url, out)
        os.system(cmd)
    tmp = bin_image(out)
    if np.sum(tmp == -1) != 0:
        continue
    rgb[i] = np.mean(tmp, axis=(0, 1))

for ifull in range(len(full_res_files)):

    tmp2 = bin_image(full_res_files[ifull])
    rgb2 = np.mean(tmp2, axis=(0, 1))
    cc = np.zeros(len(tbl))

    for i in tqdm(range(len(tbl)),leave = False):
        if np.sum(np.abs(rgb[i]-rgb2)) >2:
            continue

        out = photodir+tbl['ML_CATALOG_NUMBERS'][i]+'.jpg'
        tmp = bin_image(out)
        try:
            cc[i] = np.corrcoef(tmp.ravel(),tmp2.ravel())[0,1]
        except:
            cc[i] = -1

    print(cc[np.argsort(-cc)][0:3])

    if np.sum(cc>0.995) == 1:
        if np.max(cc)>0.995:
            print( tbl[np.argmax(cc)]['COMMON_NAME'])
            ML_CATALOG_NUMBERS = tbl[np.argmax(cc)]['ML_CATALOG_NUMBERS']
            dir =  os.path.dirname(full_res_files[ifull])
            outname = dir+'/{}.jpg'.format(ML_CATALOG_NUMBERS)
            os.rename(full_res_files[ifull],outname)

            path_loc = '/Users/eartigau/oiseaux3/peli/.'
            tag = full_res_files[ifull].split('wazo_')[1].split('.')[0]

            file_tag = path_loc+tag+'.tbl'
            if os.path.isfile(file_tag):
                os.rename(file_tag,path_loc+ML_CATALOG_NUMBERS+'.tbl')


drag()
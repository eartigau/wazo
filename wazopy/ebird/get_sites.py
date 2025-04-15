# import libraries
import os
import pickle
import subprocess

import numpy as np
from astropy.table import Table


def save_pickle(filename, variable):
    with open(filename, 'wb') as handle:
        pickle.dump(variable, handle)


def read_pickle(filename):
    with open(filename, 'rb') as handle:
        b = pickle.load(handle)
    return b


def get_all_hotspots(location, nmin=10):
    # location = 'FR-ARA-38'
    api = 'kufcmarf8fl3'

    url = " curl --location -g 'https://api.ebird.org/v2/ref/hotspot/{}' --header 'X-eBirdApiToken: {}' > tmp001".format(
        location,
        api)

    os.system(url)
    hdr = 'siteID,LOC1,LOC2,LOC3,latitude,longitude,name,date0,nlists'

    # dump header in file
    cmd = 'echo {} > tmp002'.format(hdr)
    os.system(cmd)
    # contactenate the two files
    cmd = 'cat tmp002 tmp001 > tmp003'
    os.system(cmd)

    tbl = Table.read('tmp003', format='ascii.csv', delimiter=',')

    return tbl[tbl['nlists'] > nmin]


def downloadhisto(tbl):
    ii = 0
    for siteID in tbl['siteID']:
        print('Downloading siteID {} {}/{}'.format(siteID, ii, len(tbl)))
        ii += 1
        outname = '/Users/eartigau/.ebird_sites/ebird_{}.tsv'.format(siteID)

        if os.path.exists(outname):
            # we check if file is more than 1year old
            cmd = 'find {} -mtime +365 -print'.format(outname)
            res = subprocess.check_output(cmd, shell=True)
            if len(res) > 0:
                cmd = 'rm {}'.format(outname)
                os.system(cmd)

        if not os.path.exists(outname):
            script_name = 'tmp_{}'.format(siteID)
            with open(script_name, 'w') as tmp:
                cmd = 'open https://ebird.org/barchartData\?r\={}\&bmo=1\&emo=12\&byr=1900\&eyr=2099\&fmt=tsv'.format(
                    siteID)
                # print to tile
                tmp.write(cmd + '\n')
                cmd = 'sleep 3'
                tmp.write(cmd + '\n')
                cmd = 'mv /Users/eartigau/Downloads/ebird_{}__1900_2099_1_12_barchart.txt {}'.format(siteID, outname)
                tmp.write(cmd + '\n')
            os.system('chmod +x {}'.format(script_name))
            cmd = './{} '.format(script_name)
            os.system(cmd)
            #os.system(cmd)
            #cmd = 'sleep 0.5'
            os.system(cmd)
            #os.system(cmd)
            print(siteID)
        else:
            print(siteID, 'already downloaded')

        name_pickle = outname.replace('tsv', 'pkl')

        if not os.path.exists(name_pickle):
            try:
                # read entire file as an ascii string
                with open(outname, 'r') as myfile:
                    data = myfile.read()
                #    data = myfile.read()

                data = data.split('\n')

                # only lines where there is a '<em class="sci">' are kept
                data2 = [x for x in data if '<em class="sci">' in x]

                names = []
                abundances = []
                for i in range(len(data2)):
                    tmp = data2[i].split('\t')
                    names.append(tmp[0])
                    abundances.append(tmp[1:-1])
                abundances = np.array(abundances, dtype=float)
                name_latin = [name.split('>')[1].split('<')[0] for name in names]
                name_fr = [name.split(' (')[0] for name in names]
                sample = np.array(np.array(data[np.where([('Sample Size' in d) for d in data])[0][0]].split('\t')[1:-1],
                                           dtype=float), dtype=int)

                is_a_species = np.array([(len(name.split('/')) == 1) and ('sp.' not in name) for name in names])

                siteinfo = dict()
                siteinfo['name_fr'] = name_fr
                siteinfo['name_latin'] = name_latin
                siteinfo['abundances'] = abundances
                siteinfo['sample'] = sample
                siteinfo['is_a_species'] = is_a_species
                siteinfo['siteID'] = siteID

                print('Saving pickle file {}'.format(name_pickle))
                save_pickle(name_pickle, siteinfo)
            except:
                print('Error with {}'.format(siteID))
                continue

tbl = get_all_hotspots('CA-QC-MR', nmin=10)

#tbl = get_all_hotspots('FR-ARA', nmin=10)
#tbl = get_all_hotspots('PT-08', nmin=10)
downloadhisto(tbl)


lifelist = Table.read('/Users/eartigau/oiseaux3/ebird/MyEBirdData.csv')
lifelist = lifelist[lifelist['Common Name'] != '']
lifelist_species = np.array(np.unique(lifelist['Common Name']), dtype=str)
# remove where 'sp.' is in the name
lifelist_species = np.array([x for x in lifelist_species if 'sp.' not in x])

weeks = 24,28

not_a_species=['sp.','hybrid',' x ','/',' ou ']

for i in range(len(tbl)):
    sideID = tbl['siteID'][i]
    name_pickle = '/Users/eartigau/.ebird_sites/ebird_{}.pkl'.format(sideID)
    site_info = read_pickle(name_pickle)

    if np.sum(site_info['sample'][weeks[0]:weeks[1]]) < 10:
        continue

    site_info['lifer'] = np.zeros_like(site_info['name_fr'], dtype=bool)
    for ii in range(len(site_info['name_fr'])):
        if site_info['name_fr'][ii] not in lifelist_species:

            # check in not_a_species in name
            if np.sum([x in site_info['name_fr'][ii] for x in not_a_species]) > 0:
                continue

            site_info['lifer'][ii] = True

    pobs = np.zeros(len(site_info['name_fr']), dtype=float)
    for j in range(len(site_info['name_fr'])):
        pobs[j] = np.sum(site_info['abundances'][j, weeks[0]:weeks[1]] * site_info['sample'][weeks[0]:weeks[1]]) / np.sum(
            site_info['sample'][weeks[0]:weeks[1]])

    if True in site_info['lifer']:
        plifer = pobs[site_info['lifer']]

        plifer_global = 1-np.product(1-plifer)

        if plifer_global>0.05:
            lifers = np.array(site_info['name_fr'])[site_info['lifer']]
            print('siteID : {}'.format(sideID))
            for iname, name in enumerate(lifers):
                if plifer[iname] > 0.02:
                    print('\t{}, p = {:.2f}'.format(name, plifer[iname]))
            print('p = {:.2f}'.format(plifer_global))


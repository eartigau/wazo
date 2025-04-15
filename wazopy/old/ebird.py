import numpy as np
from astropy.table import Table
#from astropy.table import Column 
import pandas as pd
#from PIL.ExifTags import TAGS
import glob
#import datetime
from astropy.time import Time
#from PIL import Image
import dateutil.parser
#from datetime import datetime 
import os
#from astropy.io import ascii
from tqdm import tqdm
#import numpy as np
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
#from matplotlib import pyplot as plt
#from jinja2 import Environment, PackageLoader, select_autoescape,FileSystemLoader
import random 
#from drag import *
#import webget
from wazo import get_ebird    

def wrap_hotspot():
    p = 'CA'
    outname = '/Users/eartigau/oiseaux/ebird/coordinates/' + p + '_all_hotspots.csv'

    if os.path.isfile(outname):
        os.system('rm '+outname)
    os.system('wget https://api.ebird.org/v2/ref/hotspot/' + p)
    os.system('cat /Users/eartigau/oiseaux/ebird/coordinates/hdr '+p+' > '+outname)

    print(outname)

    tbl = Table.read(outname)

    for i in range(len(tbl['LOC_ID'])):
        loc = tbl['LOC_ID'][i]
        tbl2 = get_stats(loc)

        print(loc, i)
        if 'WEEK30' not in tbl2.keys():
            continue

        if len(tbl2) == 0:
            continue

        if tbl2['WEEK30'][0] > 10:

            print(len(tbl['LOC_ID']),tbl2['WEEK30'][0])
            print(np.sum(tbl2['WEEK30'][1:]),tbl['NOM'][i],tbl['REGION'][i]     )
            plt.plot(tbl['LONGITUDE'][i],tbl['LATITUDE'][i],'o')
            #stop
    plt.show()

    return


def xmatch_hotspots(csv_file = 'MyEBirdData.csv'):
    
    ll = get_ebird(csv_file = csv_file)  

    provinces = np.unique(np.array(ll['STATE_PROVINCE']))     
    
    for p in provinces:
        outname = '/Users/eartigau/oiseaux/ebird/coordinates/'+p+'.csv'
        if os.path.isfile(outname) == False:
            os.system('wget https://api.ebird.org/v2/ref/hotspot/'+p)
            os.system('mv '+p+' '+outname)
            print(outname)
    #os.system('rm /Users/eartigau/oiseaux/ebird/all_hotspots.csv')
    #os.system('cat ebird/header_hotspots.csv ebird/coordinates/*csv > ebird/all_hotspots.csv')

    tbl = Table.read('ebird/all_hotspots.csv')
    
    lat_ll = np.array(ll['LATITUDE'],dtype=float)
    lon_ll = np.array(ll['LONGITUDE'],dtype=float)

    lat_tbl = np.array(tbl['LATITUDE'],dtype=float)
    lon_tbl = np.array(tbl['LONGITUDE'],dtype=float)

    deg_scale = 40000/360.0 # km per deg of latitude or longitude
    
    matched_list_id = []
    matched_dmin = []
    matched_current_name = []
    matched_hotspot_name = []
    matched_state =[]
    
    for i in range(len(ll)):
        dd = (  lat_ll[i]-lat_tbl )**2 + (  lon_ll[i]-lon_tbl )**2/np.cos(lat_ll[i]/(180/np.pi ))**2
        idmin = np.argmin(dd)
        dmin = np.sqrt(dd[idmin])*deg_scale
        if dmin <= 1e-3:
            continue
        if dmin> 0.3:
            continue
        
        matched_list_id.append(ll['SUBMISSION_ID'][i])
        matched_dmin.append(dmin)
        matched_current_name.append(ll['LOCATION'][i])
        matched_hotspot_name.append(tbl[idmin]['NAME'])
        matched_state.append(ll['STATE_PROVINCE'][i])
        
        print(dmin,ll['SUBMISSION_ID'][i],ll['LOCATION'][i],tbl[idmin]['NAME'] )
        lat_ll[lat_ll == lat_ll[i]] = 1e9

    matched_list_id = np.array(matched_list_id)
    matched_dmin = np.array(matched_dmin)
    matched_current_name = np.array(matched_current_name)
    matched_hotspot_name = np.array(matched_hotspot_name)
    matched_state = np.array(matched_state)

    order = np.argsort(matched_dmin)

    matched_list_id = matched_list_id[order]
    matched_dmin = matched_dmin[order]
    matched_current_name = matched_current_name[order]
    matched_hotspot_name = matched_hotspot_name[order]
    matched_state = matched_state[order]

    tbl = Table()
    tbl['DISTANCE_KM'] = matched_dmin
    tbl['PROVINCE'] = matched_state
    tbl['LIST_ID'] = matched_list_id
    tbl['LIFELIST_NAME'] = matched_current_name
    tbl['HOTSPOT_NAME'] = matched_hotspot_name

    tbl.write('xmatch_'+csv_file)


def get_properties_site(siteID = 'L5173873'):
    
    outdir = '/Users/eartigau/oiseaux/ebird/coordinates/'
    
    outname = outdir+siteID+'.csv'
    
    if os.path.isfile(outname) == False:
        url = 'https://ebird.org/canada/hotspot/'+siteID
        os.system('wget --no-check-certificate '+url+' > tmp')
        f = open(siteID,"r")
        tmp = f.read()
        f.close()    
        os.system('rm '+siteID)
        tmp = np.array( ''.join(tmp.split('\t')).split('\n') )
    
        for i in range(len(tmp)):
            if '<title>' in tmp[i]:
                name = tmp[i].split('>')[1].split('|')[0]
            
            if 'http://maps.google.com' in tmp[i]:
                lat = tmp[i].split('q=')[1].split(',')[0]
                lon =  tmp[i].split('q=')[1].split(',')[1].split('&')[0]
                region_id = tmp[i].split('region/')[1].split('?')[0]  
                region_name = tmp[i].split('region/')[1].split('>')[1].split('<')[0]
        
        tbl = Table()
        tbl['SITE_ID'] = [siteID]
        tbl['SITE_NAME'] = [name]
        tbl['LATITUDE'] = np.array(lat,dtype = float)
        tbl['LONGITUDE'] = np.array(lon,dtype = float)
        tbl['REGION_ID'] = [region_id]
        tbl['REGION_NAME'] = [region_name]
        tbl.write(outname)
            

def wrap_stats():
    loc = 'CA-QC'
    
    #species = 'Tree Swallow'
    #species = 'Eastern Screech-Owl'
    species = 'Bobolink'
    #species = 'Canada Warbler'
    #species = "Loggerhead Shrike"
    #species = "Tufted Titmouse"
    #species = "Red-winged Blackbird"
    #species = 'Bald Eagle'
    #species = "Cooper's Hawk"
    #species = "Common Nighthawk"
    #species= "American Black Duck"
    yrs = np.arange(1980,2020)
    
    Nmap = np.zeros([len(yrs),48])
    Smap = np.zeros([len(yrs),48])
    
    j = 0
    for yr1 in yrs:
        if yr1 <2000:
            dt = 5
        else:
            dt = 0
        
        tbl = get_stats(loc = loc,yr1 = yr1-dt//2,yr2 = yr1+dt//2)
        tbl0 = tbl[0]

        for i in range(1,49):
                Smap[j,i-1] = tbl0['WEEK'+str(i)]
                
        g = (tbl['SPECIES'] == species)
        if np.sum(g) == 1:
            tbl = tbl[g]
            for i in range(1,49):
                Nmap[j,i-1] = tbl['WEEK'+str(i)]*tbl0['WEEK'+str(i)]
        j+=1
        
    plt.imshow(Nmap/Smap,origin = 'lower')
    plt.xticks(np.arange(24)*2,[' ','J',' ','F',' ','M',' ','A',' ','M',' ','J',' ','J',' ','A',' ','S',' ','O',' ','N',' ','D',' '])
    
    
    if len(yrs) > 20:
        keep = (yrs % 5) ==0
    
    plt.yticks(np.arange(len(yrs))[keep],yrs[keep])
    plt.show()

    yearly = np.nanmean(Nmap/Smap,axis=0)
    peak = np.where(yearly/np.max(yearly) > .1)[0]
    
    fig,ax = plt.subplots(nrows = 1, ncols = 2)
    ax[0].plot(yearly)
#    plt.plot([peak[0],peak[-1]],[np.max(yearly)*1.05,np.max(yearly)*1.05],'ro')
    ax[0].plot([peak[0],peak[-1]],[np.max(yearly)*1.05,np.max(yearly)*1.05],'r-|')
    ax[0].set_xticks( np.arange(24)*2)
    ax[0].set_xticklabels( [' ','J',' ','F',' ','M',' ','A',' ','M',' ','J',' ','J',' ','A',' ','S',' ','O',' ','N',' ','D',' '])
    ax[0].set(xlim = [0,47])
    ax[0].set(ylim = [0,np.nanmax(yearly)*1.1])

    abundance = np.nanmean(Nmap[:,peak[0]:peak[-1]]/Smap[:,peak[0]:peak[-1]],axis=1)
    ax[1].plot(abundance)   
    ax[1].set(ylim = [0,np.nanmax(abundance)*1.1])
    ax[1].set_xticks(np.arange(len(yrs))[keep])
    ax[1].set_xticklabels(yrs[keep],rotation=90)
    ax[1].tick_params()
    plt.show()


def lifelist():
    tbl = Table.read('ebird/MyEBirdData.csv')
    plt.plot(tbl['LONGITUDE'], tbl['LATITUDE'], 'g.', alpha=0.05)


def get_stats(loc = 'CA-QC-MR',yr1 = 1900,yr2 = 2099):
    
    outname = '/Users/eartigau/oiseaux/ebird/locations/'+loc+'_'+str(yr1)+'_'+str(yr2)+'.csv'
    
    #https://ebird.org/barchartData?r=CA-QC-MR&bmo=1&emo=12&byr=1900&eyr=2019&fmt=tsv
    
    if os.path.isfile(outname)  == False:
        
        os.system('wget -q --output-document='+loc+' --no-check-certificate http://ebird.org/ebird/barchartData\?r='+loc+'\&bmo=1\&emo=12\&byr='+str(yr1)+'\&eyr='+str(yr2)+'\&fmt=tsv')
        
        tbl = Table()
        
        f = open(loc,"r")
        tmp = f.read()
        f.close()
        os.system('rm '+loc)
        
        tmp = np.array(tmp.split('\n'))    
        esps = []
        for i in range(len(tmp)): 
            v = np.array(tmp[i].split('\t'))
            if len(v) == 50:
                esp = v[0]
                if '/' in esp:
                    continue
                if '(' in esp:
                    continue
                if ' sp' in esp:
                    continue
                if 'hybrid' in esp:
                    continue
                if len(esp) ==0:
                    continue
                esps.append(v[0])
                #print(v[0])
        esps = np.array(esps)
        tbl['SPECIES'] = esps 
    
        for i in range(1,49):
            tbl['WEEK'+str(i)] = np.zeros_like(esps,dtype = float)
    
        for i in range(len(tmp)): 
            v = np.array(tmp[i].split('\t'))
            if len(v) == 50:
                esp = v[0]
                if esp not in esps:
                    continue
                #print(esp)
                g = esp == esps
                
                for j in range(1,49):
                    tbl['WEEK'+str(j)][g] = v[j]
        #if len(tbl) == 0:
        #    stop
        #    #continue
        tbl.write(outname)
        print('WE WRITE :',outname)
    #else:
    #    print('FILE EXISTS :'+outname)
    

    return Table.read(outname)


def get_best_sites(region = 'FR-V'):
    # FR-N toulouse
    # FR-B Aquitaine
    
    ll = get_ebird()  
    ll_names = np.array((np.unique(ll['ENGLISH_NAME'])))
    
    
    os.system("wget -q https://ebird.org/region/"+region+"/hotspots ")
    os.system('grep "/hotspot/" hotspots > tmp')
    os.system('rm hotspots')


    f = open('tmp',"r")
    hotspots = f.read()
    f.close()
    hotspots = np.array(hotspots.split('\n')) 
    
    for i in range(len(hotspots)): 
        try: 
            hotspots[i] = hotspots[i].split('/hotspot/')[1].split('?')[0] 
        except: 
            hotspots[i] = ''
    hotspots = hotspots[hotspots != '']


    for iloc in range(len(hotspots)):
        loc = hotspots[iloc]
        outname = 'ebird/locations/'+loc+'.csv'
        
        if os.path.isfile(outname)  == False:
            
            os.system('wget -q --output-document='+loc+' --no-check-certificate http://ebird.org/ebird/barchartData\?r='+loc+'\&bmo=1\&emo=12\&byr=1900\&eyr=2099\&fmt=tsv')
            
            tbl = Table()
            
            f = open(loc,"r")
            tmp = f.read()
            f.close()
            
            tmp = np.array(tmp.split('\n'))    
            esps = []
            for i in range(len(tmp)): 
                v = np.array(tmp[i].split('\t'))
                if len(v) == 50:
                    esp = v[0]
                    if '/' in esp:
                        continue
                    if '(' in esp:
                        continue
                    if 'sp' in esp:
                        continue
                    if 'hybrid' in esp:
                        continue
                    if len(esp) ==0:
                        continue
                    esps.append(v[0])
                    #print(v[0])
            esps = np.array(esps)
            tbl['SPECIES'] = esps 
        
            for i in range(1,49):
                tbl['WEEK'+str(i)] = np.zeros_like(esps,dtype = float)
        
            for i in range(len(tmp)): 
                v = np.array(tmp[i].split('\t'))
                if len(v) == 50:
                    esp = v[0]
                    if esp not in esps:
                        continue
                    #print(esp)
                    g = esp == esps
                    
                    for j in range(1,49):
                        tbl['WEEK'+str(j)][g] = v[j]
            if len(tbl) == 0:
                stop
                continue
            tbl.write(outname)
            print('WE WRITE :',outname)
        else:
            print('FILE EXISTS :'+outname)

    week = 25
    for iloc in range(len(hotspots)):
        loc = hotspots[iloc]
        outname = 'ebird/locations/'+loc+'.csv'
        tbl = Table.read(outname)
        
        nobs = tbl['WEEK'+str(week-1)][0]+tbl['WEEK'+str(week)][0]+tbl['WEEK'+str(week+1)][0]
        
        if nobs>3:
            p = (tbl['WEEK'+str(week-1)]*tbl['WEEK'+str(week-1)][0]+tbl['WEEK'+str(week)]*tbl['WEEK'+str(week)][0]+tbl['WEEK'+str(week+1)]*tbl['WEEK'+str(week+1)][0])/nobs
            
            tbl = tbl[p != 0]
            p = p[p != 0]
            
            for i in range(len(tbl)):
                 if tbl['SPECIES'][i] in ll_names:
                     tbl['SPECIES'][i] = ''

            p = p[tbl['SPECIES'] != '']
            tbl = tbl[tbl['SPECIES'] != '']
            
            if len(tbl) == 1:
                continue
            print()
            print(hotspots[iloc],np.sum(p[1:])  )
            for i in range(1,len(tbl)):   
                print(tbl['SPECIES'][i],p[i])
            
    
    
def rebound_html():
    tbl = master_photo_table()
    
    l1 = np.array(tbl['FILE_NAME'])
    for i in range(len(l1)):
        l1[i] = (l1[i].split('_'))[1]           
    l2= np.array(tbl['TAG_SPECIES'])
    
    
    
    for i in range(len(l1)):
        if i !=0:
            if l1[i] == l1[i-1]:
                continue

        html = """<!DOCTYPE html>
        <html>
        <head>
            <title>HTML Meta Tag</title>
            <meta http-equiv = "refresh" content = "2; url = {0}" />
        </head>
        <body>
        <p>Renvoi vers la page mise à jour</p>
        <p>Forward to updated page</p>
        </body>
        </html>
        """
        
        for lang in range(2):
            html2 = html.format((['wazo','bird'])[lang]+'_'+l2[i]+'.html')
        
            f = open('wazo/'+(['wazo','bird'])[lang]+'_'+l1[i]+'.html',"w+")
            f.write(html2)
            f.close()
        
    

def clean_originaux():
    fics = glob.glob('oiseaux_originaux/*.jpg')
    for fic in fics:
        if '/wazo' in fic:
            continue
        os.system('open nfom.txt')
        os.system('open '+fic)
        val = input('Quel identifiant d''espece utiliser? ')
        
        tmp = glob.glob('oiseaux_originaux/wazo_'+val+'_*.jpg')
        n = str(len(tmp)+1)  
        n=(3-len(n))*'0'+n  
        new_name = 'oiseaux_originaux/wazo_'+val+'_'+n+'.jpg'
        if os.path.isfile(new_name) == False:
            cmd = 'mv '+fic+' '+new_name
            print(cmd)
            os.system(cmd)
        else:
            stop

    os.system('rm oiseaux_originaux/*original')
            
    return []
    
def image_reset(fic):
    
    # delete the csv files for the jpg
    os.system('rm '+fic.split('.')[0]+'*.csv')
    # delete comment
    os.system('exiftool -comment="" '+fic)
    clean_originaux()
    
    return []
    


def mkjson(tbl,outname,lang='FR', zoom = 6, latitude_center = 0,longitude_center = 0):
    
    # creates js and json from the table
    # and saves under the name src/src_OUTNAME.js and src/(wazo/bird)_outname.json
    
    
    if lang == 'EN':
        prefix = 'bird'
    else:
        prefix = 'wazo'
    
    env = Environment(
        loader=FileSystemLoader( '/Users/eartigau/oiseaux/templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    
    out_str = ['var data = { "count": 1,',' "photos": [']
       
    for LOCSTR in np.unique(tbl['LOCSTR']):
        tbl2 = tbl[ tbl['LOCSTR'] == LOCSTR ]
        
        TAG_SPECIES = tbl2['TAG_SPECIES']
        TAG_FULL = tbl2['TAG_FULL']
        
        long_str = '{"photo_title": "<h7><a href='+"'../wazo/"+prefix+"_"+LOCSTR+".html'>"+tbl2['LOCATION'][0]+"</a>"+'</h7>",'
        
        
        long_str = long_str+'"photo_url": "'
        for i in range(len(TAG_FULL)):
            long_str+="<a href='../wazo/"+prefix+"_"+TAG_SPECIES[i]+".html'><img height='48' width='48'  src='../peli/c_wazo_"+TAG_FULL[i]+".png' >"+'</a>  '
        
        long_str +='", "longitude": '+tbl2['LONGITUDE'][0]+', "latitude": '+tbl2['LATITUDE'][0]+'}'
    
        out_str.append(long_str)
        out_str.append(',')
    out_str.append(']}')
    
    
    fic = open('src/'+prefix+'_'+outname+'.json','w')
    for out in out_str:
        fic.write(out+'\n')
    fic.close()
    
    template = env.get_template('template_speed.js')
    fic = open('src/src_'+outname+'.js','w')
    
    if (latitude_center == 0) and (longitude_center ==0):
        latitude_center = (np.max(np.array(tbl['LATITUDE'],dtype = float))+np.min(np.array(tbl['LATITUDE'],dtype = float)))/2
        longitude_center = (np.max(np.array(tbl['LONGITUDE'],dtype = float))+np.min(np.array(tbl['LONGITUDE'],dtype = float)))/2
  
  
    fic.write(template.render(number_markers = len(np.unique(tbl['LOCSTR'])), latitude = latitude_center,longitude = longitude_center, zoom = zoom ))
    fic.close()
    
    return []



def clean_table(tbl1):
    keys = np.array(tbl1.keys())
    
    keys2 = np.zeros(len(keys),dtype = '<U99')
    for i in range(len(keys)):
        keys2[i] = ('_'.join(keys[i].split(' '))).upper()
        keys2[i] = ''.join(keys2[i].split('('))
        keys2[i] = ''.join(keys2[i].split(')'))
        keys2[i] = '_'.join(keys2[i].split('/'))
        
    tbl2 = Table()
    for i in range(len(keys)):
        tbl2[keys2[i]] = tbl1[keys[i]]
        
    return tbl2

def mk_web():
    
    clean_originaux()
    create_med_pictures()
    drag()
    
    env = Environment(
        loader=FileSystemLoader( '/Users/eartigau/oiseaux/templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    voyage = Table.read('voyages.csv')

    
    tbl = master_photo_table()
    if len(tbl)<1:
        tbl = master_photo_table()
        

    tbl_ini = Table(tbl)



    
    for lang in ['FR','EN']:
        tbl = Table(tbl_ini)

        

        
        if lang == 'FR':
            tbl['NAME'] = tbl['COMMON_NAME']
            tbl_ini['NAME'] = tbl_ini['COMMON_NAME']
            prefix = 'wazo'
        if lang == 'EN':
            tbl['NAME'] = tbl['ENGLISH_NAME']
            tbl_ini['NAME'] = tbl_ini['ENGLISH_NAME']
            prefix = 'bird'

            
        template = env.get_template('template_index.html')
        
        fic = open('index.html','w')
        fic.write(template.render(tbl = tbl))
        fic.close()
        
        tbl = tbl[np.argsort(np.array(tbl['SORT'],dtype=float))]
    
        tbl_recent = (Table(tbl[np.argsort(-tbl['SORT_MJD_ESP'])]   ))[0:99]
        tbl_recent2 = (Table(tbl[np.argsort(-tbl['SORT_MJD_ESP'])]    ))[0:99]
        tbl_recent3 = (Table(tbl[np.argsort(-tbl['SORT_MJD_ESP'])]    ))[0:99]
        
        keep = np.ones_like(tbl_recent2,dtype = bool)
        for i in range(len(tbl_recent2)-1): 
            keep[i] = tbl_recent2['NAME'][i] != tbl_recent2['NAME'][i+1]
        tbl_recent2 = tbl_recent2[keep]
        tbl_recent2 = tbl_recent2[0:10]
    
    
        keep = np.ones_like(tbl_recent3,dtype = bool)
        for i in range(len(tbl_recent3)-1): 
            keep[i] = tbl_recent3['LOCATION'][i] != tbl_recent3['LOCATION'][i+1]
        tbl_recent3 = tbl_recent3[keep]
        tbl_recent3 = tbl_recent3[0:8]
    
        
        new_location = np.zeros_like(tbl_recent3,dtype=bool)
        
        tmp = np.unique(tbl['EBIRD_CODE'])  
        tbl['KEEP'] = np.zeros(len(tbl),dtype=bool) 
        for i in range(len(tmp)):
            g=(np.where(tmp[i] == tbl['EBIRD_CODE']))[0][0] 
            tbl['KEEP'][g] = True
            
        num_photo = str(len(tbl))
        tbl = tbl[tbl['KEEP'] ]
        num_esp = str(len(tbl))
    
        tbl['NEW_FAMILY'] =  np.zeros(len(tbl),dtype=bool) 
        for i in range(len(tmp)):
            if i == 0:
                tbl['NEW_FAMILY'][i] = True
            else:
                if tbl['FAMILY'][i] != tbl['FAMILY'][i-1]:
                    tbl['NEW_FAMILY'][i] = True
                    
    
        template = env.get_template('template_album_especes.html')
        
        if lang == 'FR':
            fic = open('album_especes.html','w')
        if lang == 'EN':
            fic = open('album_species.html','w')
        
        
        fic.write(template.render(tbl = tbl,
                                  lang = lang,
                                  tbl_recent = tbl_recent,
                                  tbl_recent2 = tbl_recent2,
                                  tbl_recent3 = tbl_recent3,
                                  num_photo = num_photo,
                                  num_esp = num_esp,
                                  voyage = voyage  ))
        fic.close()



        template = env.get_template('template_apropos.html')
        fic = open('apropos/apropos.html','w')
        fic.write(template.render(tbl = tbl,
                                  lang = 'FR',
                                  tbl_recent = tbl_recent,
                                  tbl_recent2 = tbl_recent2,
                                  tbl_recent3 = tbl_recent3,
                                  num_photo = num_photo,
                                  num_esp = num_esp,
                                  age = 43,
                                  voyage = voyage  ))
        fic.close()
        print('apropos')
        mkjson(tbl_ini,'full',lang = lang,zoom = 2,latitude_center = 5, longitude_center = -45)

        template = env.get_template('template_wazo.html')
        
    
    
        if True:
            tags = np.array(tbl['TAG_SPECIES'])
            tags = tags[np.argsort(np.array(tbl['TAXONOMIC_ORDER'],dtype=int))]
            for i in range(len(tags)):
                print('wazo/'+prefix+'_'+tags[i]+'.html')
                keep = tbl_ini['TAG_SPECIES'] == tags[i]
                tbl2 = tbl_ini[tbl_ini['TAG_SPECIES'] == tags[i]]
                tbl2 = tbl2[np.argsort(-np.array(tbl2['SORT_MJD_ESP']))] 
        
                if i != (len(tags)-1):
                    next_tag = tags[i+1]
                else:
                    next_tag = tags[i]
                    
                if i != 0:
                    prev_tag = tags[i-1]
                else:
                    prev_tag = tags[i]
        
                fic = open('wazo/'+prefix+'_'+tags[i]+'.html','w')
                print(tbl2['BGND'][0])
                fic.write(template.render(tbl = tbl,
                                          lang = lang,
                                          COMMON_NAME = tbl2['NAME'][0],
                                          SCIENTIFIC_NAME = tbl2['SCIENTIFIC_NAME'][0],
                                          tbl2 = tbl2,
                                          voyage = voyage,
                                          next_tag = next_tag,
                                          prev_tag = prev_tag,
                                          page_type = 'wazo',
                                          BGND = tbl2['BGND'][0],
                                          tag_id = tags[i]
                                          ))
                fic.close()
            
            
            
        if True:
            for tb in voyage:
                if lang == 'FR':
                    print(tb['VOYAGE_FR'])
                    keep = (tbl_ini['VOYAGE_FR'] == tb['VOYAGE_FR'])
                    voyages_lang = tb['VOYAGE_FR']
                if lang == 'EN':
                    print(tb['VOYAGE_EN'])
                    keep = (tbl_ini['VOYAGE_EN'] == tb['VOYAGE_EN'])
                    voyages_lang = tb['VOYAGE_EN']
               
     
                tbl2 = tbl_ini[keep]
                mkjson(tbl2,str(tb['VOYAGE_TAG']),lang = lang,zoom = 7)
                
                tbl2 = tbl2[np.argsort(-np.array(tbl2['SORT_MJD_ESP']))] 
        
        
                fic = open('wazo/'+prefix+'_'+str(tb['VOYAGE_TAG'])+'.html','w')
                
                fic.write(template.render(tbl = tbl,
                                          tbl2 = tbl2,
                                          lang = lang,
                                          voyage = voyage,
                                          page_type = 'trip',
                                          tag_id = str(tb['VOYAGE_TAG']),
                                          BGND = 'bgnd_others.png',
                                          TRIP_NAME = voyages_lang
                                          ))
                fic.close()
        
        if True:
            for LOCSTR in np.unique(np.array(tbl_ini['LOCSTR'])):
                print(lang,LOCSTR)
                keep = (tbl_ini['LOCSTR'] == LOCSTR)
                tbl2 = tbl_ini[keep]
                tbl2 = tbl2[np.argsort(-np.array(tbl2['SORT_MJD_ESP']))] 
                
                mkjson(tbl2,str(LOCSTR),lang = lang,zoom = 8)

                fic = open('wazo/'+prefix+'_'+LOCSTR+'.html','w')
                fic.write(template.render(tbl = tbl,
                                          tbl2 = tbl2,
                                          lang = lang,
                                          voyage = voyage,
                                          page_type = 'trip',
                                          tag_id = LOCSTR,
                                          BGND = 'bgnd_others.png',
                                          TRIP_NAME = tbl2['LOCATION'][0]
                                          ))
                fic.close()
        
        


    

def create_med_pictures():
    fics = glob.glob('oiseaux_originaux/wazo_*_*.jpg')

    for fic in fics:
        outname = 'meds/med_'+((fic.split('/'))[1].split('wazo_'))[1]       

        if os.path.exists(outname) == False:
        
            #exif = get_exif(fic)
            im = mpimg.imread(fic) 
            sz = im.shape     
            
            #stop
            ratio = sz[0]/1200
            dim1 = str(np.round(sz[0]/ratio))
            dim2 = str(np.round(sz[1]/ratio))
        
            print('~~~> '+outname)
            os.system('convert -resize '+dim1+'x'+dim2+' -bordercolor black '+
                      '-border 5 -bordercolor white -border 2 -quality 85 '+
                      '-unsharp 1 '+fic+' tmp.jpg')
            os.system('mv -f tmp.jpg '+outname)    
        #else:
        #    #print(outname+'~~~> existe')
            
    return []

def exif2csv(fic,force=False):
    csv_name = (fic.split('.jpg'))[0]+'.exif.csv'
    refresh = True
    
    if (os.path.exists(csv_name)) and (force == False):
        
        if os.path.getmtime(csv_name)>os.path.getmtime(fic):
            # the csv file is more recent than the jpg file, we can use
            # it
            refresh = False
            print('reading recent csv file for exif')
            
            
    
    if refresh == True:
        print('using exiftool as '+csv_name+' needs an update')
        os.system('exiftool '+fic+' > '+csv_name)

    ff=open(csv_name,'r')
    hdr = []
    for l in ff:
        #print(l)
        hdr.append(l)
    ff.close()
    
    # replace ".0" with ""
    for i in range(len(hdr)):
        hdr[i] = hdr[i].replace('.0','')

    # replace "NIKON" with "Nikon"
    for i in range(len(hdr)):
        hdr[i] = hdr[i].replace('NIKON','Nikon')

    
    return hdr    

def ini_set_comment(skip=True):  
 
    fics = glob.glob('oiseaux_originaux/wazo_*_*.jpg')
    tbl = Table.read('/Users/eartigau/oiseaux/nfom.txt',delimiter='#',format='ascii')
    ebird = get_ebird()
    ific =0
    for fic in fics:    
        print('['+str(ific)+']')
        ific+=1
        #fic = 'oiseaux_originaux/wazo_0505_009.jpg'
        done = False
     
        hdr = exif2csv(fic)


        for l in hdr:
            #print(l)
            if 'Create Date' in l:
                date = (l.split(': '))[1]
                date = date.strip(' ')
                date = (date.split(' '))[0]
                date = date.split(':')
                date = date[0].strip(' ')+'-'+date[1].strip(' ')+'-'+date[2].strip(' ')
            if 'COMMENT' in l:
                if '_' in l:
                    done = True
                    print(l)
                
        if done == False:
            id_wazo = (fic.split('wazo_'))[1].split('_')[0]  +'0'
            
            
            ids = []
            for i in tbl['ID']:
                tmp_id = str(i)
                if len(tmp_id) <5:
                    tmp_id = ('0'*(5-len(tmp_id)))+tmp_id
                ids.append(tmp_id)
            g = (np.where(np.array(ids) == np.array(id_wazo)))[0]
            
            if len(g)==1:
                g=g[0]
                latin = tbl['NOM_LA'][g] 
                
                record = np.where( (ebird['DATE'] == date) & (ebird['SCIENTIFIC_NAME'] == latin) )[0]
                print(len(record))
                if len(record) ==0:
                    print('aucune date+espèce ne correspond au fichier :'+fic)
                    continue
                if len(record)==1:
                    comment = (np.array(ebird['SUBMISSION_ID']))[record[0]]+'_'+(np.array(ebird['EBIRD_CODE']))[record[0]]
                    print(comment)
                    os.system('exiftool -comment="'+comment+'" '+fic)
                else:
                    if skip==False:
                        get_exif(fic)
                    print('probleme #2 avec :'+fic)
                    
            else:
                if skip==False:
                    get_exif(fic)
                print('probleme #1 avec :'+fic)
    
                 
def wazo_params():
    wps = dict()
    wps['EBIRD_PATH'] = '/Users/eartigau/oiseaux/ebird/'
    wps['KEYS'] = ['FILE_NAME',
             'SUBMISSION_ID',
             'LENS_F_STOPS',
             'F_NUMBER',
             'DIRECTORY',
             'FILE_SIZE',
             'FILE_MODIFICATION_DATE_TIME',
             'EXPOSURE_PROGRAM',
             'FOCAL_LENGTH',
             'FOCAL_LENGTH_IN_35MM_FORMAT',
             'DATE_TIME_ORIGINAL',
             'CAMERA_MODEL_NAME',
             'CREATE_DATE',
             'FOCAL_LENGTH',
             'CAMERA_MODEL_NAME',
             'ISO_SETTING',
             'COMMENT',
             'FIELD_OF_VIEW',
             'SHUTTER_SPEED',
             'COMMON_NAME',
             'SCIENTIFIC_NAME',
             'SCIENTIFIC_NAME_NOSSP',
             'TAXONOMIC_ORDER',
             'COUNT',
             'LENS',
             'STATE_PROVINCE',
             'APPROXIMATE_FOCUS_DISTANCE',
             'LENS_ID',
             'COUNTY',
             'LOCATION',
             'LATITUDE',
             'LONGITUDE',
             'DATE',
             'TIME',
             'PROTOCOL',
             'DURATION_MIN',
             'ALL_OBS_REPORTED',
             'DISTANCE_TRAVELED_KM',
             'AREA_COVERED_HA',
             'NUMBER_OF_OBSERVERS',
             'BREEDING_CODE',
             'SPECIES_COMMENTS',
             'CHECKLIST_COMMENTS',
             'PROVINCE_FR',
             'PROVINCE_EN',
             'COUNTRY_FR',
             'COUNTRY_EN',
             'MJD',
             'MJD_END',
             'LOCSTR',
             'ENGLISH_NAME',
             'ORDER',
             'FAMILY',
             'SORT',
             'EBIRD_CODE']
    
    return wps
    


def decdeg2dmstxt(val,sig='NS'):
    pos = val<0 # we know if it is a positive value or not
    val = np.abs(val)
    deg = str(int(np.floor(val)))
    if len(deg) ==1:
        deg = '0'+deg

    val-=np.floor(val)
    val*=60
    arcmin = str(int(np.floor(val)))
    if len(arcmin) ==1:
        arcmin = '0'+arcmin
    val-=np.floor(val)
    val*=60
    arcsec = str(int(np.floor(val)))
    if len(arcsec) ==1:
        arcsec = '0'+arcsec

    return deg+arcmin+arcsec+sig[int(pos)]        

def check_new_ebird():
    if os.path.isfile('/Users/eartigau/Downloads/MyEBirdData.csv'):
        cmd = 'mv -f /Users/eartigau/Downloads/MyEBirdData.csv /Users/eartigau/oiseaux/ebird/'
        print(cmd)
        os.system(cmd)
        print('rm all_exif.csv')
        os.system('rm all_exif.csv')
    return []

def master_photo_table(all_fic = 'oiseaux_originaux/*jpg',force=False,ebird=''):
    check_new_ebird()
    all_fic = glob.glob(all_fic)
    ebird = get_ebird()
   
    for fic in all_fic:
        
        outname = (fic.split('.'))[0]+'.sp.csv' 
        
        if (os.path.exists(outname) == True):
            if os.path.getmtime(outname)<os.path.getmtime(fic):
                print('csv plus vieux que '+fic)
                print('rm '+outname)
                os.system('rm '+outname)
                print('rm all_exif.csv')
                os.system('rm all_exif.csv')
            #else:
            #    #print('csv plus récent que '+fic)
        
        
        if (os.path.exists(outname) == False):
            print('does not exist  : '+outname)
            
            hdr = exif2csv(fic)
            
            # removes 0.0 and replaces with 0
            for i in range(len(hdr)):
                hdr[i] = '0'.join(hdr[i].split('0.0'))          
            
            hdr_out = dict()
            date_kwrd=[]
            for l1 in hdr:
                if ': ' in l1:
                    tmp=l1.split(": ")
                    key = tmp[0]
                    val = tmp[1]
                    key = key.strip(" ")
                    #val = '//'.join( (val.split("/")) )
                    
                    for ite in range(2):
                        val = val.strip(" ")
                        val = val.strip("'")
                        val = val.strip("\n")                                
                    hdr_out[key] = val
                
            date_kwrd = ''
            if date_kwrd =='':
                if 'Create Date' in hdr_out.keys():
                    date_kwrd='Create Date'
            if date_kwrd =='':
                if 'Date/Time Created' in hdr_out.keys():
                    date_kwrd='Date/Time Created'
            if date_kwrd =='':
                if 'Date/Time Original' in hdr_out.keys():
                    date_kwrd='Date/Time Original'
            if date_kwrd =='':
                if 'Modify Date' in hdr_out.keys():
                    date_kwrd = 'Modify Date'
            
        
            
            if date_kwrd ==[]:
                print(hdr_out)
                stop
            hdr_out['DATE'] = hdr_out[date_kwrd]
        
            day = (hdr_out['DATE'].split(' '))[0]
            day = day.split(':')
            day[1] =  (['','janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre'])[int(day[1])]
            if int(day[2])<9:
                day[2]=day[2].strip('0')
            if day[2] ==1:
                day[2] = '1er'
            day[2]+' '+day[1]+' '+day[0] 
            
            hdr_out['DATE_FR'] = day[2]+' '+day[1]+' '+day[0] 
        
            day = (hdr_out['DATE'].split(' '))[0]
            day = day.split(':')
            day[1] =  (['','January','February','March','April','May','June','July','August','September','Octobre','November','December'])[int(day[1])]
            if int(day[2])<9:
                day[2]=day[2].strip('0')
            if day[2] ==1:
                day[2] = '1st'
            
            hdr_out['DATE_EN'] = day[1]+' '+day[2]+', '+day[0] 
        
            yr,da,mo = (hdr_out['DATE'].split(' '))[0].split(':')  
            
            if len(ebird) ==1:
                ebird = get_ebird()

            # must be in the same format as in the EXIF, no capital here
            if ('Comment' in hdr_out.keys()) == False:
                same_date = (np.where( (ebird['DATE'] == yr+'-'+da+'-'+mo)))[0]
                os.system('open '+fic)  
                print('Espèces observées le : '+yr+'-'+da+'-'+mo+'\n')
                nn=1
                if len(same_date) !=1:
                    for i in same_date:
                        print('['+str(nn)+'] '+np.array(ebird['LOCATION'])[i]+', '+np.array(ebird['COMMON_NAME'])[i])
                        nn+=1
                        
                    val = input('Quelle lieu+espèce attibuer à la photo : ')
                    val = int(val)
                else:
                    val = 1
                    i=same_date[val-1]
                    print('Une seule espèce pour cette date')
                    print(' '+np.array(ebird['LOCATION'])[i]+', '+np.array(ebird['COMMON_NAME'])[i])
                os.system('exiftool -comment="'+ebird['SUBMISSION_ID'][same_date[val-1]]+'_'+ebird['EBIRD_CODE'][same_date[val-1]]+'" '+fic)
                print('il faut rouler la commande à nouveau')
                return
                #continue
                
            else:
                list_id,ebird_code=hdr_out['Comment'].split('_')
                gg = (np.where( (list_id == ebird['SUBMISSION_ID']) & (ebird_code == ebird['EBIRD_CODE']))  )[0]
                print(gg)
                
                if len(gg) !=0:
    
                    for key in ebird.keys():
                        hdr_out[key] = (np.array(ebird[key])[gg])[0]
                else:
                    print('exiftool -comment="" '+fic)
                    os.system('exiftool -comment="" '+fic)
                    
            tbl=Table() 
            for key in hdr_out.keys(): 
                #print(key) 
                #print(key,hdr_out[key])
                #tmp = (str(hdr_out[key]))
                #if len(tmp) ==0:
                #    tmp = " "
                #vals = np.append(vals,tmp)
                #keys = np.append(keys,key)
                tmp=hdr_out[key]
                if type(tmp) == str:
                    tmp = ''.join(tmp.split('"'))
                tbl[key]=[tmp]  
            #tbl['KEY'] = keys
            #tbl['VAL'] = vals
            
            tbl = clean_table(tbl)
            
            wps = wazo_params()           
            
            tbl2 = Table()
            for key in wps['KEYS']:
                if key in tbl.keys():
                    tbl2[key] = tbl[key]
                else:
                    tbl2[key] = ''
                    
                    
            # we make FOCAL_LENGTH a FLOAT
            tmp = str(tbl2['FOCAL_LENGTH'][0])
            tmp = (tmp.split(' '))[0]
            del tbl2['FOCAL_LENGTH']
            
            print(len(tmp))
            if len(tmp) <=1:
                tmp = '0.0'                
            tbl2['FOCAL_LENGTH'] = np.array(tmp,dtype = float)

            tbl = tbl2


        
            esp = np.zeros(len(tbl),dtype = 'U99')
            for i in range(len(esp)):
                esp[i] = (tbl['FILE_NAME'][i].split('_') )[1]
                
            tag = np.zeros(len(tbl),dtype = 'U99')
            for i in range(len(esp)):
                tmp = (tbl['FILE_NAME'][i].split('_') )[2]
                tag[i] = (tmp.split('.'))[0]
                
            tag_full = np.zeros(len(tbl),dtype = 'U99')
            for i in range(len(esp)):
                tag_full[i] = esp[i]+'_'+tag[i]
        
            url = np.zeros(len(tbl),dtype = 'U99')
            for i in range(len(esp)):
                url[i] = 'wazo/wazo_'+esp[i]+'_'+tag[i]+'.html'
        
            png = np.zeros(len(tbl),dtype = 'U99')
            index = np.zeros(len(tbl),dtype = 'U99')
            
            rand = []
            for i in range(len(esp)):
                png[i] = 'peli/c_wazo_'+esp[i]+'_'+tag[i]+'.png'
                index[i] = str(i)
                rand.append(random.random())
            tbl['TAG_SPECIES'] = tbl['EBIRD_CODE']
            tbl['TAG_NUM'] = tag
            tbl['TAG_FULL'] = tag_full
            tbl['URL'] = url
            tbl['PNG'] = png
            tbl['INDEX'] = index
            tbl['RANDOM_INDEX'] = np.argsort(rand)
        
            tbl['VOYAGE_FR'] = np.zeros(len(tbl),dtype = '<U999')
            tbl['VOYAGE_EN'] = np.zeros(len(tbl),dtype = '<U999')
            tbl['VOYAGE_URL'] = np.zeros(len(tbl),dtype = '<U999')
        
            voyages = Table.read('voyages.csv')
            
            for i in range(len(voyages)):
                g = ((tbl['DATE']>voyages['DATE1'][i]) & (tbl['DATE']<voyages['DATE2'][i]))
                tbl['VOYAGE_FR'][g] = voyages['VOYAGE_FR'][i]
                tbl['VOYAGE_EN'][g] = voyages['VOYAGE_EN'][i]
                tbl['VOYAGE_URL'][g] = 'wazo/wazo_'+''.join(((voyages['DATE1'][i]).split('-')))+'.html'
        
            tbl['DATE_FR'] = np.zeros(len(tbl),dtype = '<U999')
            tbl['DATE_EN'] = np.zeros(len(tbl),dtype = '<U999')
        
            tbl['PHOTO_LABEL_FR'] = np.zeros(len(tbl),dtype = '<U999')
            tbl['PHOTO_LABEL_EN'] = np.zeros(len(tbl),dtype = '<U999')
            
            
            tbl['NOM_FR'] = tbl['COMMON_NAME']
            tbl['NOM_EN'] = tbl['ENGLISH_NAME']
            
            tbl['BGND'] = np.zeros(len(tbl),dtype = '<U99')
            tbl['BGND'][:] = 'bgnd_others.png'
            
            for i in range(len(tbl)):
                print(i)
                bgnd_name =  'oiseaux_originaux/bgnd/bgnd_'+tbl['TAG_SPECIES'][i]+'.jpg'
                if os.path.isfile(bgnd_name):
                    tbl['BGND'][i] = 'bgnd_'+tbl['TAG_SPECIES'][i]+'.jpg'

            SORT_MJD_ESP = np.array(tbl['MJD'],dtype = float)+np.array(tbl['SORT'],dtype = float)/1e9   
            tbl['SORT_MJD_ESP'] = SORT_MJD_ESP
            
            
            date = np.array(tbl['DATE']) 
            for i in range(len(tbl)):
                tmp = date[i].split('-')
            
                if len(tmp) == 3:
                    mois = (['','janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre'])[int(tmp[1])]
                    month = (['','January','February','March','April','May','June','July','August','Septembre','Octobre','Novembre','Decembre'])[int(tmp[1])]
                    tbl['DATE_FR'][i] = tmp[2]+' '+mois+' '+tmp[0]
                    tbl['DATE_EN'][i] = month+' '+ tmp[2]+', '+tmp[0]
                    
                    #
                    #tbl['PHOTO_LABEL_FR'][i] = '<A  STYLE="text-decoration:none" HREF="wazo/wazo_'+tbl['TAG_SPECIES'][i]+'.html">'+tbl['COMMON_NAME'][i]+'</a>, '+'<A  STYLE="text-decoration:none" HREF="wazo/wazo_l.'+tbl['LOCSTR'][i]+'.html">'+tbl['LOCATION'][i]+', '+tbl['PROVINCE_FR'][i]+'</a> - '+tbl['DATE_FR'][i]+', <A  STYLE="text-decoration:none" HREF="https://ebird.org/view/checklist?subID='+tbl['SUBMISSION_ID'][i]+'">ebird<a/>'
                    #tbl['PHOTO_LABEL_EN'][i] = '<A  STYLE="text-decoration:none" HREF="wazo/wazo_'+tbl['TAG_SPECIES'][i]+'.html">'+tbl['ENGLISH_NAME'][i]+'</a> - '+tbl['DATE_EN'][i]
                    
                    
                    # tbl['Common Name'][i] +', '++'; '++', '+tbl['COUNTRY_FR'][i]
                    #tbl['PHOTO_LABEL_EN'][i] = tbl['English name'][i]+', '+tbl['DATE_EN'][i]+'; '+tbl['Location'][i]+', '+tbl['PROVINCE_EN'][i]+', '+tbl['COUNTRY_EN'][i]
        
        
            
            tbl.write(outname,overwrite=True,format='csv')
            

    print(os.system('cat oiseaux_originaux/*sp.csv  > all_exif.csv'))
    tbl = Table.read('all_exif.csv')
    tbl = tbl[tbl['FAMILY'] != 'FAMILY']
    
    # now defined as a float
    SORT_MJD_ESP = np.array(tbl['SORT_MJD_ESP'],dtype = float)        
    del tbl['SORT_MJD_ESP'] 
    tbl['SORT_MJD_ESP']  = SORT_MJD_ESP

    tbl['RANDOM_INDEX'] = np.argsort(np.random.rand(len(tbl)))          
        
    return tbl

def master_photo_table_old(force=False):
    
    
    print(os.system('cat oiseaux_originaux/*sp.csv  > all_exif.csv'))
    tbl = Table.read('all_exif.csv')
    tbl = tbl[tbl['FAMILY'] != 'FAMILY']
    
    ebird = get_ebird() 
    
    #
    stop        
    """
        i=0
        for f in all_jpgs:
            print(i,f)
            exif = get_exif(f,ebird=ebird)
            
            tbl_keys = exif.keys()
            for key in wparams['KEYS']:
                if key in tbl_keys:
                    tbl[key][i] = exif[key][0]
            i+=1
    
           
        tbl = clean_table(tbl)
    """
                
                
                
    return tbl


def get_hdr(fic):
    # get header from a given wazo file
    hdr=open(fic,'r')
    
    hdr_out = dict()
    for l1 in hdr:
        if '=' in l1:
            key,val=l1.split("=")
            key = key.strip(" ")
            val = (val.split("/"))[0]
            for ite in range(2):
                val = val.strip(" ")
                val = val.strip("'")
                
            if key in ['MJDATE','ICOINTRO','NAXIS1','NAXIS2']:
                val = int(val)
            if key in ['FMJDATE','LATITUDE','LONGITUD','XCENTRE','YCENTRE','RINT','FCAM','FNUM']:
                val = float(val)
                
            hdr_out[key] = val
    hdr.close()
    return hdr_out

def mkweb():
    tbl = master_photo_table()

    
    return []


import pandas as pd
from astropy.time import Time
import dateutil.parser
from tqdm import tqdm
from jinja2 import Environment, PackageLoader, select_autoescape,FileSystemLoader
import random 
import etienne_tools as et
#import cv2
#from drag import drag
import matplotlib.image as mpimg
from PIL import Image
from astropy.io import fits
import numpy as np
import matplotlib.pyplot as plt
from subprocess import PIPE, run
import glob
import os
from astropy.table import Table
import requests
import requests
from PIL import Image
from io import BytesIO

def os_system(command):
    result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
    return result.stdout

plt.ioff()

def cdn():
    # stats pour cote-des-neiges

    ebird = get_ebird()
    ebird = ebird[ebird['LOCATION'] == 'Côte-des-Neiges']
    uname = np.unique(ebird['COMMON_NAME'])

    mois = np.zeros_like(ebird,dtype = int)
    for i in range(len(ebird)):
        mois[i] = ebird['DATE'][i][5:7]
    ebird['MOIS'] = mois

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

def plot_ll():
    ebird = get_ebird()
    SUBMISSION_ID = np.array(ebird['SUBMISSION_ID'])
    u_SUBMISSION_ID = np.unique(SUBMISSION_ID)

    n = np.zeros_like(u_SUBMISSION_ID,dtype = int)
    date = np.zeros_like(u_SUBMISSION_ID,dtype = float)

    for i in range(len(u_SUBMISSION_ID)):
        g = SUBMISSION_ID == u_SUBMISSION_ID[i]
        n[i] = np.nansum(g)
        date[i] =ebird['MJD'][g][0]

    return []

def get_stats(loc = 'CA-QC-MR',yr1 = 1900,yr2 = 2099):
    
    outname = '/Users/eartigau/oiseaux3/ebird/locations/'+loc+'_'+str(yr1)+'_'+str(yr2)+'.csv'
    
    #https://ebird.org/barchartData?r=CA-QC-MR&bmo=1&emo=12&byr=1900&eyr=2019&fmt=tsv
    
    if os.path.isfile(outname)  == False:
        
        os.system('wget -q --output-document='+loc+' --no-check-certificate http://ebird.org/ebird/barchartData\?r='+loc+'\&bmo=1\&emo=12\&byr='+str(yr1)+'\&eyr='+str(yr2)+'\&fmt=tsv')
        
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

        tbl.write(outname)
        print('WE WRITE :',outname)
    else:
        print('FILE EXISTS :'+outname)
    

    return Table.read(outname)

def get_best_sites(region = 'CA-QC'):
    # FR-N toulouse
    # FR-B Aquitaine
    
    ll = get_ebird()  
    ll_names = np.array((np.unique(ll['ENGLISH_NAME'])))
    
    
    os.system("wget -q https://ebird.org/region/"+region+"/hotspots ")
    os.system('grep "/hotspot/" hotspots > tmpx')
    os.remove('hotspots')


    f = open('tmpx',"r")
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
    
    l1 = np.array(tbl['ML_CATALOG_NUMBERS'])
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

def xmatch_videos():

    video1 = np.array(glob.glob('/Users/eartigau/wazo/oiseaux_originaux/*mp4'))[1]

    cap = cv2.VideoCapture(video1)
    ret, ref_image = cap.read()
    ref_image = np.array(Image.fromarray(ref_image).resize((30,30)),dtype = float)
    for i in range(3):
        ref_image[:,:,i] -= np.mean(ref_image[:,:,i])
        ref_image[:, :, i] /= np.std(ref_image[:, :, i])
    cap.release()



    comparison_set = np.array(glob.glob('/Users/eartigau/photo/ref_mov/*.fits'))
    mini_rms = np.zeros_like(comparison_set, dtype = float)

    for i_movie in tqdm(range(len(comparison_set))):
        cube = fits.getdata(comparison_set[i_movie])
        rms = np.zeros(cube.shape[0])
        for i in range(cube.shape[0]):
            rms[i] = np.std(cube[i] - ref_image)
        mini_rms[i_movie] = np.min(rms)

def get_image(fic):

    if '.jpg' == fic[-4:]:
        return Image.open(fic)

    if '.mp4' == fic[-4:]:
        cap = cv2.VideoCapture(fic)
        ret, frame = cap.read()
        cap.release()
        return Image.fromarray(frame[:,:,::-1])

    return -1

def image_reset(fics):

    for fic in fics:
        # delete the csv files for the jpg
        if os.path.isfile(fic.split('.')[0]+'*.csv'):
            os.remove(fic.split('.')[0]+'*.csv')
        # delete comment
        os.system('exiftool -comment="" '+fic)
    clean_originaux()
    
    return []

def mkjson(tbl,outname = 'full',lang='FR', zoom = 6, latitude_center = 0,longitude_center = 0):

    # creates js and json from the table
    # and saves under the name src/src_OUTNAME.js and src/(wazo/bird)_outname.json

    if lang == 'EN':
        prefix = 'bird'
    else:
        prefix = 'wazo'
    
    env = Environment(
        loader=FileSystemLoader( '/Users/eartigau/wazo/templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    
    out_str = ['var data = { "count": 1,',' "photos": [']
       
    for LOCSTR in np.unique(tbl['LOCSTR']):
        tbl2 = tbl[ tbl['LOCSTR'] == LOCSTR ]
        
        TAG_SPECIES = tbl2['TAG_SPECIES']
        TAG_FULL = tbl2['TAG_FULL']
        
        long_str = '{"photo_title": "'+tbl2['LOCATION'][0]+'",'
        
        
        long_str = long_str+'"photo_url": "'
        for i in range(len(TAG_FULL)):
            bin_group = tbl2[i]['BIN_KEYWORD']
            index = tbl2[i]['INDEX_BIN_KEYWORD']
            link = 'gallerie_{0}.html#lg=1&slide={1}'.format(bin_group,index)
            long_str+="<a href="+link+"><img height='80' width='80' style='border:5px solid white' src='peli/c_square_"+TAG_FULL[i]+".jpg' >"+'</a>  '
        
        long_str +='", "longitude": '+tbl2['LONGITUDE'][0]+', "latitude": '+tbl2['LATITUDE'][0]+'}'
    
        out_str.append(long_str)
        out_str.append(',')
    out_str.append(']}')
    
    
    fic = open('/Users/eartigau/wazo/src/'+prefix+'_'+outname+'.json','w')
    for out in out_str:
        fic.write(out+'\n')
    fic.close()
    
    template = env.get_template('template_speed.js')
    fic = open('/Users/eartigau/wazo/src/src_'+outname+'.js','w')
    
    if (latitude_center == 0) and (longitude_center ==0):
        latitude_center = (np.max(np.array(tbl['LATITUDE'],dtype = float))+np.min(np.array(tbl['LATITUDE'],dtype = float)))/2
        longitude_center = (np.max(np.array(tbl['LONGITUDE'],dtype = float))+np.min(np.array(tbl['LONGITUDE'],dtype = float)))/2

    fic.write(template.render(number_markers = len(np.unique(tbl['LOCSTR'])), latitude = latitude_center,longitude = longitude_center, zoom = zoom ))
    fic.close()
    
    return []

def mk_menu():

    menu = """
    <a href="apropos.html">À propos</a>  &#8226;
    <a href="familles.html">Phylogénétique</a>  &#8226;
    <a href="voyages.html">Voyages</a>  &#8226;
    <a href="recent.html">Récentes</a>  &#8226;
    <a href="liste.html">Liste</a >  &#8226;
    <a href="map.html">Carte</a >  
    """

    # &#8226;
    #     <a href="jophoto.html">Photos de Joséphine</a>

    #menu.append('<li><a href="jophoto.html">Photos de Joséphine</a></li>')
    return menu

def mk_voyage_gal(tbl1):

    voyage = Table.read('/Users/eartigau/wazo/voyages.csv')

    text = []
    text.append('<div class="container-fluid" data-aos="fade" data-aos-delay="500">')
    text.append('   <div class="row">')
    prev_bin = ''


    print('... par voyage ')
    for i in tqdm(range(len(voyage))):
        tbl2 = Table(tbl1[np.array(tbl1['VOYAGE_FR']) == np.array(voyage['VOYAGE_FR'][i])])

        tt = tbl2['MJD'] + tbl2['QUALITE'] * 1e9

        tbl2 = tbl2[np.argsort(-tt)]

        tx = voyage['VOYAGE_FR'][i]
        tx = '<br>'.join(tx.split(' ('))
        tx = ''.join(tx.split(')'))


        tag = tbl2['ML_CATALOG_NUMBERS'][np.argmax(tbl2['QUALITE'])]

        text.append('   <div class="col-6 col-md-4 col-lg-3 col-xxl-2">')
        text.append('       <div class="image-wrap-2">')
        text.append('           <div class="image-info">')
        text.append('               <h2 class="mb-3">{0}</h2>'.format(tx ))
        text.append('               <a href="voyage_{0}.html" class="btn btn-outline-white py-2 px-4">{1} Photos</a>'.format(voyage['VOYAGE_TAG'][i], len(tbl2)))
        text.append('           </div>')
        text.append('           <img src="https://cdn.download.ams.birds.cornell.edu/api/v2/asset/{}/1200" alt="Image" class="img-fluid">'.format(tag))
        text.append('       </div>')
        text.append('   </div>')
        text.append('')
    text.append('   </div>')
    text.append('</div>')

    return '\n'.join(text)

def mk_family_gal(tbl1):
    text = []
    text.append('<div class="container-fluid" data-aos="fade" data-aos-delay="500">')
    text.append('   <div class="row">')
    prev_bin = ''
    print('Table des familles')

    done = []
    for i in tqdm(range(len(tbl1))):
        if tbl1['BIN_KEYWORD'][i] not in done:
            done.append(tbl1['BIN_KEYWORD'][i])

            g = tbl1['BIN_KEYWORD'][i] ==  tbl1['BIN_KEYWORD']
            tbl2 = tbl1[g]

            tt = tbl2['MJD'] + tbl2['QUALITE'] * 1e9

            tbl2 = tbl2[np.argsort(-tt)]

            tx = '<br>'.join(tbl2['MENU_FR'][0].split(':'))

            index =  tbl2['ML_CATALOG_NUMBERS'][0]
            tag = f'https://cdn.download.ams.birds.cornell.edu/api/v2/asset/{index}/1200'

            text.append('   <div class="col-6 col-md-4 col-lg-3 col-xxl-2">')
            text.append('       <div class="image-wrap-2">')
            text.append('           <div class="image-info">')
            text.append('               <h2 class="mb-3">{0}</h2>'.format(tx)   )
            if np.sum(g) !=1:
                suffix = 's'
            else:
                suffix = ''
            text.append('               <a href="{0}" class="btn btn-outline-white py-2 px-4">{1} Photo{2}</a>'.format(tbl2['BIN_KEYWORD'][0], np.sum(g),suffix))
            text.append('           </div>')
            text.append('           <img src="{}" alt="Image" class="img-fluid">'.format(tag))
            text.append('       </div>')
            text.append('   </div>')
            text.append('')
    text.append('   </div>')
    text.append('</div>')

    return '\n'.join(text)

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

def html_clean(html):

    html = html.replace('&lt;','<')
    html = html.replace('&gt;','>')
    html = html.replace('&#34;','"')
    html = html.replace('&#39;',"'")
    html = html.replace('&amp;','&')

    return html

def mk_random_intro(tbl = None):
    if type(tbl) == type(None):
        tbl = master_photo_table()

    tbl2 = tbl[tbl['INTRO']]
    tbl2 = tbl2[np.argsort(np.random.random(len(tbl2)))]

    tbl = []
    tbl.append(    """
    <SCRIPT LANGUAGE="JavaScript" type="text/javascript">
    // Set up the image files to be used.
    var theImages = new Array()
    var thePage = new Array()
        thePage[2054] = "wazo/wazo_blnchl1.html"
        theImages[2003] = "peli/c_wazo_9913_002.png"
    """)

    for i in range(len(tbl2)):
        tbl.append('thePage[{0}] = "wave/wave_{1}.html'.format(i,tbl2['EBIRD_CODE'][i] ))
        tbl.append('theImages[{0}] = "peli/c_wazo_{1}_{2}.html'.format(i,tbl2['SP_ID'][i] ,tbl2['NTH_ID'][i]))

    tbl.append('var j = 0')
    tbl.append('var p = theImages.length;')
    tbl.append('//var whichImage = Math.round(Math.random()*(p-1));')
    tbl.append('var whichImage = Math.round(Math.random()*(p-1));')

    nn = 100
    for i in range(100):
        tbl.append('var whichImage{0} = (whichImage+{1}) % (p-1) ;'.format(i+1,i+2))

    width_im = '6.02'
    for i in range(100):
        tbl.append("function showImage1(){")
        tbl.append('document.write(''<a href="''+thePage[whichImage{0}]+''"><img width={1}% height={1}% border="0" src="''+theImages[whichImage{0}]+''" >'');'.format(i,width_im)+'}')

    tbl.append('</SCRIPT>')
    return tbl


def get_apropos():
    from datetime import date
    today = date.today()
    age =  str(int(np.floor(abs(today - date(1976,6,22)).days/365.24)))

    txt = """
        <div align="center">

    <table>
        <tr><td>
    <h_text_table>Je suis un photographe d'oiseaux amateur de {0} ans bas&eacute; &agrave; Montr&eacute;al. 
    Je suis passionn&eacute; par l'observation des oiseaux depuis l'&acirc;ge de 9 ans et je suis pass&eacute; de 
    l'observation &agrave; la photographie il y a une dizaine d'ann&eacute;es. J'ai eu la chance de vivre et de 
    travailler au Chili de 2006 &agrave; 2009 dans la r&eacute;gion de 
    <a target="_blank"  STYLE="text-decoration:none" href="http://fr.wikipedia.org/wiki/La_Serena">La Serena</a>, 
    ce qui m'a permis de photographier une bonne partie des esp&egrave;ces du 
    <a href="http://en.wikipedia.org/wiki/Norte_Chico,_Chile" target="_blank"  STYLE="text-decoration:none">Norte Chico</a> 
    chilien. Je r&eacute;side depuis 2009 dans la r&eacute;gion de Montr&eacute;al.
    </br>
    </br>
    Je travaille comme <a href="http://www.exoplanetes.umontreal.ca/equipe/chercheurs/etienne-artigau/" STYLE="text-decoration:none">
    astronome</a> &agrave; l'Universit&eacute; de Montr&eacute;al. Mes sujets de recherche tournent autour de l'étude des exoplan&egrave;tes. 
    Je suis aussi impliqu&eacute; dans trois projets de d&eacute;veloppement d'instruments: 
    <a href = "http://www.stsci.edu/jwst/instruments/niriss" target="_blank"  STYLE="text-decoration:none">NIRISS</a> 
    qui sera utilis&eacute; &agrave; bord du t&eacute;lescope spatial JWST en 2022, 
    <a href = "http://craq-astro.ca/actualite2_en.php?num_act=61" target="_blank"  STYLE="text-decoration:none">SPIRou</a> 
    que nous utilisons au t&eacute;lescope CFHT depuis 2018 et <a href="http://www.exoplanetes.umontreal.ca/nirps-lirex-a-la-quete-des-planetes-habitables-autour-des-etoiles-les-plus-proches-du-soleil/">NIRPS</a> qui sera utilisé au Chili à partir de 2022. Dans le cadre de mon travail, je fais 
    beaucoup de programmation et d'analyse de donn&eacute;es astronomiques, et ce sont ces outils que j'utilise pour 
    cr&eacute;er le pr&eacute;sent site web. Toute la structure de ce site est construite &agrave; partir de scripts en python.
    </br>
    </br>
    Si vous voulez utiliser les images de ce site &agrave; des fins non lucratives, n'h&eacute;sitez pas &agrave; 
    me contacter (etienne.artigau@gmail.com). Vous pouvez voir mon profil <a href="https://ebird.org/profile/MTIzNTEw/world">ebird</a> ainsi que les milliers de photos 
    mises en lignes sur la <a href = "https://ebird.org/media/catalog?userId=USER123510">librairie McAulay</a>.
    
    Si vous voulez voir ce que je fais quand je ne photographie pas les oiseaux, voici quelques liens vers mes travaux scientifiques :
    <br>
    &#8226; <a href = "https://www.youtube.com/watch?v=JRYe2_va9OY">Un peu de vulgarisation sur les exoplanètes</a><br>
    &#8226; <a href = "https://phys.org/news/2021-06-brown-dwarf-orbiting-star-toi1278.html">La découverte d'une naine brune autour d'une petite étoile</a><br>
    
    
    <br><br>
     &Eacute;tienne Artigau
    </h_text_table>
    <td><tr></table>
        </div>

    <br><br>
    <img src="081224_0362b.jpg" alt="Photo wazo!">

    <h7>Moi-m&ecirc;me en train de photographier un <a  STYLE="text-decoration:none"  
    href = "espece_dolgul2.html">Go&eacute;land de Scoresby.</a></h7>

    
    """.format(age)

    return txt

def get_intro_table(frac = 6.0):

    nn = 10
    # total width = 0.5
    sz = '{:2.3f}'.format(100./nn*0.5)

    matrix = np.zeros([nn,nn], dtype = 'U999')


    remove = np.random.random(matrix.shape) < .5
    x, y = np.indices(remove.shape)
    remove[ ((x + y) % 3) == 0]=True


    remove[nn//2-2:nn//2+2,nn//2-1:nn//2+1] = True
    remove[nn//2-1:nn//2+1,nn//2-2:nn//2+2] = True


    matrix[remove] =  '<a href = "recent.html"><img src="peli/vide.png" width="{0}%"></a>'.format(frac)


    matrix[nn//2,nn//2] = '<a href = "voyages.html"><img src="peli/voyages.png" width="{0}%"></a>'.format(frac)
    matrix[nn//2-1,nn//2] = '<a href = "liste.html"><img src="peli/liste.png" width="{0}%" ></a>'.format(frac)
    matrix[nn//2,nn//2-1] = '<a href = "apropos.html"><img src="peli/apropos.png" width="{0}%" ></a>'.format(frac)
    matrix[nn//2-1,nn//2-1] = '<a href = "map.html"><img src="peli/map.png" width="{0}%" ></a>'.format(frac)

    n=0
    for i in range(nn):
        for j in range(nn):
            if matrix[i,j] == '':
                matrix[i,j] = '<SCRIPT LANGUAGE="JavaScript" type="text/javascript">showImage{}();</SCRIPT>'.format(n)
                n+=1
    print(n)

    txt = []
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            txt.append('{}'.format(matrix[i,j]))
        txt.append('<br>')

    return ''.join(txt)

def get_lg(tbl):

    text_lg = ['<div class="row" id="lightgallery">']
    for i in range(len(tbl)):
        tmp = """
        <div class="col-4 col-sm-3 col-md-2 col-lg-2 col-xl-2 item" 
        data-aos="fade" data-src="https://cdn.download.ams.birds.cornell.edu/api/v2/asset/{0}/2400" 
        data-sub-html="<h6>{1}, {2}, {3}, {5} <a href='https://ebird.org/checklist/{6}' target ='_frame'>ebird</a></h6></p>">
            <a href="#"><img src="https://cdn.download.ams.birds.cornell.edu/api/v2/asset/{0}/480" alt="IMage" class="img-fluid"></a>
        </div>
        """.format(tbl['ML_CATALOG_NUMBERS'][i],tbl['COMMON_NAME'][i],tbl['DATE_FR'][i], tbl['LOCATION'][i],tbl['PROVINCE_FR'][i],tbl['COUNTRY_FR'][i],tbl['SUBMISSION_ID'][i])
        text_lg = np.append(text_lg,tmp.split('\n'))

    text_lg = np.append(text_lg,'</div>')


    return '\n'.join( text_lg)

def mk_web():
    
    #clean_originaux()
    #verif_jpgs()
    tbl_ini = master_photo_table()
    menu = mk_menu()

    env = Environment(
        loader=FileSystemLoader( '/Users/eartigau/wazo/templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    #mkjson(tbl_ini, outname='full', lang='FR', zoom=2, latitude_center=0, longitude_center=0)

    #template = env.get_template('template_index.html')
    #fic = open('index.html', 'w')
    #tbl = Table(tbl_ini[tbl_ini['INTRO']])
    #tbl['RANDOM_INDEX'] = np.arange(len(tbl))[np.argsort(np.random.random(len(tbl)))]

    #frac = 5.0
    #matrix = get_intro_table(frac = frac)
    #fic.write(html_clean(template.render(tbl = tbl, matrix = matrix, frac =frac)))
    #fic.close()

    # Table des familles
    template = env.get_template('template_single.html')
    fic = open('/Users/eartigau/wazo/familles.html', 'w')
    text = mk_family_gal(tbl_ini)
    fic.write(html_clean(template.render(TEXT_NO_PICTURE = text, MENU = menu)))
    fic.close()

    # Table des voyages
    template = env.get_template('template_single.html')
    fic = open('/Users/eartigau/wazo/voyages.html', 'w')
    text = mk_voyage_gal(tbl_ini)
    fic.write(html_clean(template.render(TEXT_NO_PICTURE = text, MENU = menu)))
    fic.close()

    voyage = Table.read('/Users/eartigau/wazo/voyages.csv')

    tbl0 = tbl_ini[1:][tbl_ini['EBIRD_CODE'][1:] != tbl_ini['EBIRD_CODE'][:-1]]
    tbl0 = tbl0[np.argsort(np.array(tbl0['TAXONOMIC_ORDER'],dtype = float))]

    # table des récents
    nlines =  20
    tbl = tbl_ini[np.argsort(-tbl_ini['MJD'])][0:nlines*6]
    template = env.get_template('template_single.html')
    fic = open('/Users/eartigau/wazo/recent.html', 'w')
    fic.write(html_clean(template.render(tbl=tbl, TEXT_NO_PICTURE = get_lg(tbl), NAME='Photos récentes', MENU = menu)))
    fic.close()

    print('par voyage')
    for ite in tqdm(range(len(voyage))):
        tbl = Table(tbl_ini)
        tbl2 = Table(tbl[np.array(tbl['VOYAGE_FR']) == np.array(voyage['VOYAGE_FR'][ite])])
        tbl = tbl2[np.argsort(np.array(tbl2['TAXONOMIC_ORDER'], dtype=float))]

        template = env.get_template('template_single.html')

        fic = open('/Users/eartigau/wazo/voyage_{}.html'.format(voyage['VOYAGE_TAG'][ite]), 'w')
        tmp = voyage['VOYAGE_FR'][ite]
        NAME = tmp.split('(')[0]
        DATE = tmp.split('(')[1].split(')')[0]
        fic.write(html_clean(template.render(tbl=tbl, NAME = NAME, DATE = DATE, MENU = menu, TEXT_NO_PICTURE = get_lg(tbl) )))
        fic.close()

    print('Table par espèce')
    for EBIRD_CODE in tqdm(np.unique(tbl_ini['EBIRD_CODE'])):
        tbl2 = tbl_ini[tbl_ini['EBIRD_CODE'] == EBIRD_CODE]
        tbl2 = tbl2[np.argsort(-np.array(tbl2['MJD'], dtype=float))]

        template = env.get_template('template_single.html')

        latin = '<div align = "center"><em><h4>{}</h4></em></div>'.format(tbl2['SCIENTIFIC_NAME'][0])

        fic = open('/Users/eartigau/wazo/espece_{}.html'.format(EBIRD_CODE), 'w')
        NAME =  tbl2['COMMON_NAME'][0]
        texte = '<a href = "gallerie_{0}.html">{1}</a>'.format(tbl2['BIN_KEYWORD'][0],tbl2[ 'MENU_FR'][0])+get_lg(tbl2)
        fic.write(html_clean(template.render(tbl=tbl2, NAME = NAME, TEXT_NO_PICTURE = latin+'<br>'+texte, MENU = menu)))
        fic.close()

    print('apropos')
    apropos = get_apropos()
    fic = open('apropos.html', 'w')
    fic.write(html_clean(template.render(TEXT_NO_PICTURE=apropos, MENU = menu)))
    fic.close()

    if True:
        ubin = np.array(np.unique(tbl_ini['BIN_KEYWORD']))

        for ite in range(len(ubin)):
            tbl = Table(tbl_ini)
            g = np.array(tbl_ini['BIN_KEYWORD']) == np.array(ubin[ite])
            tbl2 = Table(tbl[g])
            order = np.argsort(tbl2['INDEX_BIN_KEYWORD'])
            tbl = tbl2[order]

            template = env.get_template('template_single.html')

            for style in range(2):

                if style == 0:
                    suffix = '_date'
                    text = "<a href='gallerie_{0}{1}.html'>Photos triées par espèces...</a></7><br>".format(ubin[ite],'')
                else:
                    text = "<a href='gallerie_{0}{1}.html'>Photos triées date...</a></7><br>".format(ubin[ite],'_date')
                    suffix = ''
                    tbl = tbl[np.argsort(tbl['TAXONOMIC_ORDER'])]

                fic = open('gallerie_{0}{1}.html'.format(ubin[ite],suffix), 'w')

                tmp =  tbl['MENU_FR'][0].split(' : ')
                fic.write(html_clean(template.render(tbl=tbl, NAME =tmp[0], DATE = tmp[1], MENU = menu,
                                                     TEXT_NO_PICTURE = text+get_lg(tbl))))
                fic.close()


    fic = open('liste.html', 'w')
    template = env.get_template('template_single.html')

    current_sp = ''
    current_family = ''
    current_order = ''

    text = []

    text.append('<h7>Espèce en danger critique '+"d'e"+'xtinction </h7a><img src="cr.png" alt="Crititally Endangered" width="20" height="20">')
    text.append('<h7>Espèce en danger '+"d'e"+'xtinction </h7a><img src="en.png" alt="Endangered" width="20" height="20">')
    text.append('<h7>Espèce vulnérable </h7a><img src="vu.png" alt="Vulnerable" width="20" height="20">')
    text.append('<h7>Espèce quasi-menacée </h7a><img src="nt.png" alt="Near threatened" width="20" height="20">')
    text.append('<br>')

    text.append(' <div class="newspaper">')
    print('liste de toutes les espèces')
    for i in tqdm(range(len(tbl_ini))):
        if current_sp != tbl_ini['NOM_FR'][i]:
            current_sp = tbl_ini['NOM_FR'][i]
            tbl2 = tbl_ini[tbl_ini['NOM_FR'] == current_sp]
            gal = tbl2['EBIRD_CODE'][0]

            if current_order != tbl_ini['ORDER'][i]:
                current_order = tbl_ini['ORDER'][i]
                text.append('<br><h7a>'+current_order+'</h7a>')
            if current_family != tbl_ini['FAMILY'][i]:
                current_family = tbl_ini['FAMILY'][i]
                text.append('<h7b>'+current_family+'</h7b>')

            #<img src="img_girl.jpg" alt="Girl in a jacket" width="500" height="600">
            im = ' <img src="peli/vide.png" alt="Least concern" width="20" height="20">'

            if 'CR' in tbl_ini['IUCN'][i]:
                im = '   <img src="cr.png" alt="Crititally Endangered" width="20" height="20">'
            if 'EN' in tbl_ini['IUCN'][i]:
                im = '   <img src="en.png" alt="Endangered" width="20" height="20">'
            if 'VU' in tbl_ini['IUCN'][i]:
                im = '   <img src="vu.png" alt="Vulnerable" width="20" height="20">'
            if 'NT' in tbl_ini['IUCN'][i]:
                im = '   <img src="nt.png" alt="Near threatened" width="20" height="20">'

            if len(tbl2) ==1:
                tag2 = '#lg=1&slide=0'
            else:
                tag2 = ''
            text.append('<h7><a href = "espece_'+gal+'.html'+tag2+'">'+current_sp+'</a>'+im+'</h7>')
    text.append('</div>')

    fic.write(html_clean(template.render(TEXT_NO_PICTURE = '<br>'.join(text), NAME='Toutes les espèces photographiées', MENU = menu)))
    fic.close()


    fic = open('map.html', 'w')
    template = env.get_template('template_map.html')
    fic.write(html_clean(template.render(MENU = menu)))
    fic.close()

def create_med_pictures():
    fics = et.file_search('oiseaux_originaux/wazo_*_*.jpg')

    for fic in fics:
        outname = 'meds/med_'+((fic.split('/'))[1].split('wazo_'))[1]       

        if os.path.exists(outname) == False:
        
            im = mpimg.imread(fic)
            sz = im.shape     
            
            ratio = sz[0]/1200
            dim1 = str(np.round(sz[0]/ratio))
            dim2 = str(np.round(sz[1]/ratio))
        
            print('~~~> '+outname)
            os.system('convert -resize '+dim1+'x'+dim2+' -bordercolor black '+
                      '-border 5 -bordercolor white -border 2 -quality 85 '+
                      '-unsharp 1 '+fic+' tmp.jpg')
            os.rename('tmp.jpg', outname)
        #else:
        #    #print(outname+'~~~> existe')
    return []

def exif2csv(fic,force=False,outtype = 'csv'):

    if '.jpg' in fic:
        csv_name = (fic.split('.jpg'))[0]+'.exif.csv'
    elif '.mp4' in fic:
        csv_name = (fic.split('.mp4'))[0]+'.exif.csv'
    else:
        stop
    refresh = True
    
    if (os.path.exists(csv_name)) and (force == False):
        
        if os.path.getmtime(csv_name)>os.path.getmtime(fic):
            # the csv file is more recent than the jpg file, we can use
            # it
            refresh = False
            #print('reading recent csv file for exif')

    
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

def ini_set_comment(fics=[''],skip=True):

    if type(fics) == str:
        fics = [fics]

    if fics[0] == '':
        fics =et.file_search('oiseaux_originaux/wazo_*_*.jpg')

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
    wps['EBIRD_PATH'] = '/Users/eartigau/wazo/ebird/'
    wps['EBIRD_TAXONOMY_FILE'] = '/Users/eartigau/wazo/ebird/eBird_Taxonomy_v2024.csv'
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
    
def get_ebird(force=True, csv_file = 'MyEBirdData.csv'):
    wps = wazo_params()
    check_new_ebird()
    
    ebird_reports_file = wps['EBIRD_PATH']+csv_file
    ebird_reports =clean_table(pd.read_csv(ebird_reports_file,dtype=str))
    keys = ebird_reports.keys()
    
    if ('EBIRD_CODE' in keys) and (force == False):
        return ebird_reports

    ebird_reports['TEMPERATURE_TXT'] =  np.zeros(len(ebird_reports), dtype = '<U99')
    ebird_reports['TEMPERATURE'] = np.zeros(len(ebird_reports), dtype = float)+np.nan
    ebird_reports['TEMPERATURE_MIN']= np.zeros(len(ebird_reports), dtype = float)+np.nan
    ebird_reports['TEMPERATURE_MAX']= np.zeros(len(ebird_reports), dtype = float)+np.nan
    ebird_reports['WIND']= ''
    ebird_reports['CLOUD_COVER']= ''
    ebird_reports['HUMIDITY'] = -999
    ebird_reports['HUMIDITY_MIN']= -999
    ebird_reports['HUMIDITY_MAX']= -999
    ebird_reports['SUNRISE'] = -999
    ebird_reports['SUNSET'] = -999
    ebird_reports['CLOUDS'] = ''
    for i in range(len(ebird_reports)):
        comment = str(ebird_reports['CHECKLIST_COMMENTS'][i])
        if 'Temperature:' in comment:
            temperature = comment.split('Temperature: ')[1].split(' Wind:')[0]
            Fahr = False
            if '°F' in temperature:
                Fahr = True
            temperature0 = str(temperature.replace('°C','').replace('°F','').replace(' ',''))

            print(temperature)
            neg_min = False
            if temperature0.startswith('-'):
                neg_min = True
                temperature0 = temperature0[1:]
            ebird_reports['TEMPERATURE_MIN'][i] =  temperature0.split('-')[0]
            ebird_reports['TEMPERATURE_MAX'][i] =  temperature0.split('-')[-1]
            if neg_min:
                ebird_reports['TEMPERATURE_MIN'][i] = -ebird_reports['TEMPERATURE_MIN'][i]
            if '--' in temperature0:
                ebird_reports['TEMPERATURE_MAX'][i] = -ebird_reports['TEMPERATURE_MAX'][i]

            ebird_reports['TEMPERATURE'][i] = (ebird_reports['TEMPERATURE_MIN'][i] +ebird_reports[
                'TEMPERATURE_MAX'][i])/2.0
            print(ebird_reports['TEMPERATURE_MIN'][i],ebird_reports['TEMPERATURE_MAX'][i],ebird_reports['TEMPERATURE'][i])

            if Fahr:
                ebird_reports['TEMPERATURE_MAX'][i] = (ebird_reports['TEMPERATURE_MAX'][i]-32)/1.8
                ebird_reports['TEMPERATURE_MIN'][i] = (ebird_reports['TEMPERATURE_MIN'][i]-32)/1.8
                ebird_reports['TEMPERATURE'][i] = (ebird_reports['TEMPERATURE'][i]-32)/1.8
                ebird_reports['TEMPERATURE_TXT'][i] = temperature
            print(i)



    # updating Location
    # -- remove anything in parenthesis
    for i in range(len(ebird_reports)):
        ebird_reports['LOCATION'][i] = ebird_reports['LOCATION'][i].replace('*', ' ')
        ebird_reports['LOCATION'][i] = ebird_reports['LOCATION'][i].split('(')[0]
        ebird_reports['LOCATION'][i] = ebird_reports['LOCATION'][i].split('[')[0]
        ebird_reports['LOCATION'][i] = ebird_reports['LOCATION'][i].split('|')[-1]
        ebird_reports['LOCATION'][i] = ebird_reports['LOCATION'][i].split(', domaine général')[0]
        ebird_reports['LOCATION'][i] = ebird_reports['LOCATION'][i].split(', Site général')[0]
        ebird_reports['LOCATION'][i] = ebird_reports['LOCATION'][i].split(', general')[0]
        ebird_reports['LOCATION'][i] = ebird_reports['LOCATION'][i].strip()

    # remove [] in common name
    for i in range(len(ebird_reports)):
        ebird_reports['COMMON_NAME'][i] = ebird_reports['COMMON_NAME'][i].split('[')[0]
        ebird_reports['COMMON_NAME'][i] = ebird_reports['COMMON_NAME'][i].split('(')[0]
        ebird_reports['COMMON_NAME'][i] = ebird_reports['COMMON_NAME'][i].strip()

    # -- replace "--" with ", "
    for i in range(len(ebird_reports)): 
        ebird_reports['LOCATION'][i] = ebird_reports['LOCATION'][i].replace('--',', ')

    # -- replace "MN " with "" (Monumento Natural)
    for i in range(len(ebird_reports)): 
        ebird_reports['LOCATION'][i] = ebird_reports['LOCATION'][i].replace('MN ','')


    
    taxo_file = wps['EBIRD_TAXONOMY_FILE']
    subnational_file = wps['EBIRD_PATH']+'subnational.csv'
    
    print('loading anciliary CSV files')
    subnational = pd.read_csv(subnational_file)
    
    time=list(ebird_reports['TIME'])
    date=list(ebird_reports['DATE'])
    duration = list(ebird_reports['DURATION_MIN'])
    
    time=list(ebird_reports['TIME'])
    for i in range(len(time)):
        if type(time[i]) == float:
            time[i] = '12:00 PM'
    
    country_code = np.zeros(len(time),dtype='<U2')
    
    print('Matching country+province')
    for i in tqdm(range(len(time)),leave=False):
        country_code[i]=(ebird_reports['STATE_PROVINCE'][i].split('-'))[0]
    
    country_en = np.zeros(len(time),dtype='<U30')
    country_fr = np.zeros(len(time),dtype='<U30')
    province_en = np.zeros(len(time),dtype='<U30')
    province_fr = np.zeros(len(time),dtype='<U30')
    
    
    
    for i in range(len(time)):
        if country_en[i] == '':
            g = (np.where(subnational['SUBNATIONAL1_CODE'] == (ebird_reports['STATE_PROVINCE'][i].split('-'))[0]+'-' ))[0]
            tmp_en = (list(subnational['SUBNATIONAL1_NAME'][g]))[0]
            tmp_fr = (list(subnational['FRENCH_NAME'][g]))[0]
            gg=(np.where(country_code == country_code[i]))
            country_en[gg]=tmp_en
            country_fr[gg]=tmp_fr
    
        if province_fr[i] =='':
            g = (np.where(subnational['SUBNATIONAL1_CODE'] == ebird_reports['STATE_PROVINCE'][i]) )[0]
            if len(g) ==0:
                print('Manquant : ',ebird_reports['STATE_PROVINCE'][i])
                continue
            gg=(np.where(ebird_reports['STATE_PROVINCE'][i] == ebird_reports['STATE_PROVINCE']))
            province_fr[gg] = subnational['FRENCH_NAME'][g]
            province_en[gg] = subnational['SUBNATIONAL1_NAME'][g]
    
    ebird_reports['PROVINCE_FR'] = province_fr
    ebird_reports['PROVINCE_EN'] = province_en
    ebird_reports['COUNTRY_FR'] = country_fr
    ebird_reports['COUNTRY_EN'] = country_en
    
    date_fr=np.zeros(len(time),dtype="<30U")
    date_en=np.zeros(len(time),dtype="<30U")
    
    i=0
    for d in date:
        tmp=d.split("-")
        day=str(tmp[2])
        month=str(tmp[1])
        yr=str(tmp[0])
        
        month_en=(["","Jan","Feb","March","Apr","May","June","July","Aug","Sep","Oct","Nov","Dec"])[int(month)]
        month_fr=(["","jan","fév","mars","avr","mai","juin","jui","août","sep","oct","nov","dec"])[int(month)]
        
        if day == "1":
            day_fr = "1er"
        else:
            day_fr=tmp[1]

        if day == "1":
            day_en = "1st"
            day_fr = "1er"
        elif day =="21":
            day_en = "21st"
        elif day =="31":
            day_en = "31st"
        else:
            day_en = tmp[1]+"th"
    
        if day_en[0] =="0":
            day_en=day_en[1:]
        if day_fr[0] =="0":
            day_fr=day_fr[1]
    
    
    date_fr[i]=day_fr+' '+month_fr+' '+yr
    date_en[i]=month_en+' '+day_en+', '+yr
    i+=1
    
    ebird_reports["DATE_FR"]=date_fr
    ebird_reports["DATE_EN"]=date_en
    
    print('Calculating julian days')
    
    mjd = np.zeros(len(time))
    
    for i in tqdm(range(len(time)),leave=False):
    	mjd[i] = (Time(dateutil.parser.parse(date[i]+' '+time[i]))).mjd
    ebird_reports['MJD']=mjd
    
    mjd_end = np.zeros(len(time))
    for i in range(len(time)):
    	mjd_end[i]=mjd[i]+float(duration[i])/(60.*24.)
    ebird_reports['MJD_END']=mjd_end
    
    
    locstr =np.ndarray(len(mjd),dtype='<U20')
    
    print('Creating location string')
    
    for i in range(len(time)):
    	locstr[i]=decdeg2dmstxt(float(ebird_reports['LATITUDE'][i]),sig='NS')+ decdeg2dmstxt(float(ebird_reports['LONGITUDE'][i]),sig='EW')
    
    ebird_reports['LOCSTR']=locstr

    taxinomy = pd.read_csv(taxo_file)  # ,encoding='ascii')
    taxinomy = clean_table(taxinomy)

    Nreports = len(ebird_reports['SCIENTIFIC_NAME'])

    print('Matching names')

    english_name_taxo = np.array(taxinomy['PRIMARY_COM_NAME'])
    scientific_name_taxo = np.array(taxinomy['SCI_NAME'])
    scientific_name_report = np.array(ebird_reports['SCIENTIFIC_NAME'])
    order_taxo = np.array(taxinomy['ORDER'])
    family_taxo = np.array(taxinomy['FAMILY'])

    for i in tqdm(range(len(family_taxo)), leave=False):
        if type(family_taxo[i]) != str:
            family_taxo[i] = ''
        family_taxo[i] = ((family_taxo[i]).split(' '))[0]

    sort_taxo = np.array(taxinomy['TAXON_ORDER'])
    nesp = 0

    flag = np.zeros(len(scientific_name_report), dtype=bool)

    english_name_report = np.zeros(len(scientific_name_report), dtype='<U99')
    order_report = np.zeros(len(scientific_name_report), dtype='<U99')
    family_report = np.zeros(len(scientific_name_report), dtype='<U99')
    sort_report = np.zeros(len(scientific_name_report), dtype='<U99')
    EBIRD_CODE = np.zeros(len(scientific_name_report), dtype='<U99')

    ebird_code_taxo = np.array(taxinomy['SPECIES_CODE'])

    for i in tqdm(range(Nreports), leave=False):
        if flag[i] == False:
            try:
                gg = (np.where(scientific_name_report[i] == scientific_name_report))[0]
                g = ((np.where(scientific_name_report[i] == scientific_name_taxo))[0])[0]

                english_name_report[gg] = english_name_taxo[g]
                order_report[gg] = order_taxo[g]
                EBIRD_CODE[gg] = ebird_code_taxo[g]
                family_report[gg] = family_taxo[g]
                sort_report[gg] = sort_taxo[g]
                flag[gg] = True
            except:
                print('err')
            nesp += 1
        i += 1
    
    ebird_reports['ENGLISH_NAME'] =english_name_report
    ebird_reports['ORDER'] = order_report
    ebird_reports['FAMILY'] = family_report
    ebird_reports['SORT'] =sort_report
    ebird_reports['EBIRD_CODE'] =EBIRD_CODE
    ebird_reports['SCIENTIFIC_NAME_NOSSP'] =ebird_reports['SCIENTIFIC_NAME']
    
    
    for i in tqdm(range(Nreports),leave=False):
        tmp = ebird_reports['SCIENTIFIC_NAME_NOSSP'][i]
        if ' x ' not in tmp:
            ebird_reports['SCIENTIFIC_NAME_NOSSP'][i] = ' '.join((tmp.split(' '))[0:2])

    ebird_reports = clean_table(ebird_reports)

    ebird_reports['YEAR'] = np.zeros_like( ebird_reports['LOCATION'],dtype = int)
    for i in range(len(ebird_reports)):
        ebird_reports['YEAR'][i] = ebird_reports['DATE'][i][0:4]


    ebird_reports.write(ebird_reports_file,overwrite=True,format='csv')

    # remove [] in common name
    for i in range(len(ebird_reports)):
        ebird_reports['ENGLISH_NAME'][i] = ebird_reports['ENGLISH_NAME'][i].split('[')[0]
        ebird_reports['ENGLISH_NAME'][i] = ebird_reports['ENGLISH_NAME'][i].split('(')[0]



    ebird_reports['IUCN'] = np.zeros_like(ebird_reports, dtype = 'U99')
    ucode =  np.unique(ebird_reports['EBIRD_CODE'])
    for u in tqdm(ucode):
        if len(u) ==0:
            continue
        url = 'https://species.birds.cornell.edu/bow/api/v1/auxspecies/{}?category=conservation_status'.format(u)
        if not os.path.isfile('/Users/eartigau/wazo/iucn/'+u):
            os.system('wget -q -O /Users/eartigau/wazo/iucn/'+u+' '+url)
        f = open('/Users/eartigau/wazo/iucn/'+u, 'r')
        a = f.read()
        f.close()
        a = a.split(',')
        status = ''
        for i in range(len(a)):
            if 'IUCN_' in a[i]:
                status = ''.join(a[i].split(':')[1].split('"'))
        ebird_reports['IUCN'][ebird_reports['EBIRD_CODE'] == u] = status

    ebird_reports.write(ebird_reports_file,overwrite=True,format='csv')
    return ebird_reports

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
        os.rename('/Users/eartigau/Downloads/MyEBirdData.csv','/Users/eartigau/wazo/ebird/MyEBirdData.csv')
    return []

def master_photo_table():

    ebird = get_ebird()

    tbl = Table(ebird)
    tbl = tbl[np.array(tbl['ML_CATALOG_NUMBERS'],dtype = str) != 'nan']
    for i in tqdm(range(len(tbl))):
        keys = tbl['ML_CATALOG_NUMBERS'][i].split(' ')
        for key in keys:
            # add line of ebird to the table
            tbl.add_row(tbl[i])
            tbl['ML_CATALOG_NUMBERS'][-1] = key
    keep = [' ' not in key for key in tbl['ML_CATALOG_NUMBERS']]
    tbl = tbl[keep]

    tbl['NOM_FR'] = tbl['COMMON_NAME']
    tbl['NOM_EN'] = tbl['ENGLISH_NAME']

    tbl['RANDOM_INDEX'] = np.argsort(np.random.rand(len(tbl)))          

    tbl['NOM_FR_PREFIX'] = np.array(tbl['NOM_FR'])
    tbl['NOM_EN_PREFIX'] = np.array(tbl['NOM_EN'])
    tbl['NOM_FR_PREFIX_PLURIEL'] = np.array(tbl['NOM_FR'])
    tbl['NOM_EN_PREFIX_PLURIEL'] = np.array(tbl['NOM_EN'])

    for i in range(len(tbl)):
        if '(' in tbl['NOM_EN_PREFIX'][i]:
            tbl['NOM_EN_PREFIX'][i] = tbl['NOM_EN_PREFIX'][i].split('(')[0]
        tbl['NOM_EN_PREFIX'][i] = tbl['NOM_EN_PREFIX'][i].strip()
        tbl['NOM_EN_PREFIX'][i] = tbl['NOM_EN_PREFIX'][i].split(' ')[-1]

    for i in range(len(tbl)):
        if 'Petit ' in tbl['NOM_FR_PREFIX'][i]:
            tbl['NOM_FR_PREFIX'][i] = tbl['NOM_FR_PREFIX'][i].split(' ')[-1]
        elif 'Petite ' in tbl['NOM_FR_PREFIX'][i]:
            tbl['NOM_FR_PREFIX'][i] = tbl['NOM_FR_PREFIX'][i].split(' ')[-1]
        elif 'Grand ' in tbl['NOM_FR_PREFIX'][i]:
            tbl['NOM_FR_PREFIX'][i] = tbl['NOM_FR_PREFIX'][i].split(' ')[-1]
        elif 'Grande ' in tbl['NOM_FR_PREFIX'][i]:
            tbl['NOM_FR_PREFIX'][i] = tbl['NOM_FR_PREFIX'][i].split(' ')[-1]
        else:
            tbl['NOM_FR_PREFIX'][i] = tbl['NOM_FR_PREFIX'][i].split(' ')[0]

    tbl['NOM_FR_PREFIX_PLURIEL'] = np.array(tbl['NOM_FR_PREFIX'])
    tbl['NOM_EN_PREFIX_PLURIEL'] = np.array(tbl['NOM_EN_PREFIX'])

    for i in range(len(tbl)):
        if tbl['NOM_FR_PREFIX_PLURIEL'][i][-1] == 's':
            continue
        if tbl['NOM_FR_PREFIX_PLURIEL'][i][-1] == 'x':
            continue
        if 'Hibou' in tbl['NOM_FR_PREFIX_PLURIEL'][i]:
            tbl['NOM_FR_PREFIX_PLURIEL'][i]+='x'
            continue
        if tbl['NOM_FR_PREFIX_PLURIEL'][i][-3:] == 'eau':
            tbl['NOM_FR_PREFIX_PLURIEL'][i]+='x'
            continue
        tbl['NOM_FR_PREFIX_PLURIEL'][i] += 's'

    tbl['BIN_KEYWORD'] = np.array(tbl['FAMILY'])
    tbl['BIN_LEVEL_KEYWORD'] = 'FAMILY'

    for uorder in np.unique(tbl['ORDER']):
        g = tbl['ORDER'] == uorder
        print(uorder,np.sum(g))
        if np.sum(g)<200:
            tbl['BIN_KEYWORD'][g] = uorder
            tbl['BIN_LEVEL_KEYWORD'][g] = 'ORDER'

    tbl['MENU_FR'] = np.zeros(len(tbl), dtype = 'U999')
    tbl['MENU_EN'] = np.zeros(len(tbl), dtype = 'U999')
    tbl['MJD'] = np.array(tbl['MJD'], dtype = float)

    tbl['INDEX_BIN_KEYWORD'] = 0
    for ubin in np.unique(tbl['BIN_KEYWORD']):
        g = tbl['BIN_KEYWORD'] == ubin
        tbl[g] = tbl[g][np.argsort(-tbl[g]['MJD'])]

        tbl['INDEX_BIN_KEYWORD'][g] = np.arange(np.sum(g))

        uprefix_fr = np.array(np.unique(tbl['NOM_FR_PREFIX_PLURIEL'][g]))
        nprefix = np.zeros_like(uprefix_fr,dtype = int)
        for i in range(len(uprefix_fr)):
            nprefix[i] = np.sum(uprefix_fr[i] == tbl['NOM_FR_PREFIX_PLURIEL'])

        ord = np.argsort(-nprefix)
        uprefix_fr = uprefix_fr[ord]
        nprefix = nprefix[ord]

        if tbl['BIN_LEVEL_KEYWORD'][g][0] == 'FAMILY':
            tmp = tbl['BIN_KEYWORD'][g][0][:-2] + 'és'
        else:
            tmp = tbl['BIN_KEYWORD'][g][0]

        if len(uprefix_fr) > 3:
            str_out_fr =  tmp+' : '+', '.join( uprefix_fr[0:2] )+', etc'
        else:
            str_out_fr = tmp+' : '+', '.join(uprefix_fr)

        tbl['MENU_FR'][g] = str_out_fr


        uprefix_en = np.array(np.unique(tbl['NOM_EN_PREFIX'][g]))
        nprefix = np.zeros_like(uprefix_en,dtype = int)
        for i in range(len(uprefix_en)):
            nprefix[i] = np.sum(uprefix_en[i] == tbl['NOM_EN_PREFIX'])

        ord = np.argsort(-nprefix)
        uprefix_en = uprefix_en[ord]
        nprefix = nprefix[ord]

        if len(uprefix_en) > 6:
            str_out_en =  tbl['BIN_KEYWORD'][g][0]+' : '+', '.join( uprefix_en[0:5] )+', etc'
        else:
            str_out_en = tbl['BIN_KEYWORD'][g][0]+' : '+', '.join(uprefix_en[0:5])

        tbl['MENU_EN'][g] = str_out_en

    tbl['TAXONOMIC_ORDER'] = np.array(tbl['TAXONOMIC_ORDER'], dtype = float)
    tbl['SORT'] = np.array(tbl['TAXONOMIC_ORDER'], dtype = float)
    tbl = tbl[np.argsort(tbl['SORT'])]

    tbl['IUCN'] = np.zeros_like(tbl, dtype = 'U99')
    ucode =  np.unique(tbl['EBIRD_CODE'])
    for u in tqdm(ucode):
        if u =='':
            continue
        url = 'https://species.birds.cornell.edu/bow/api/v1/auxspecies/{}?category=conservation_status'.format(u)
        if not os.path.isfile('/Users/eartigau/wazo/iucn/'+u):
            os.system('wget -q -O /Users/eartigau/wazo/iucn/'+u+' '+url)
        f = open('/Users/eartigau/wazo/iucn/'+u, 'r')
        a = f.read()
        f.close()
        a = a.split(',')
        status = ''
        for i in range(len(a)):
            if 'IUCN_' in a[i]:
                status = ''.join(a[i].split(':')[1].split('"'))
        tbl['IUCN'][tbl['EBIRD_CODE'] == u] = status

    tbl['IUCN_FR'] =  np.zeros_like(tbl, dtype = 'U99')
    tbl['IUCN_EN'] =  np.zeros_like(tbl, dtype = 'U99')

    g = tbl['IUCN'] == 'IUCN_LC'
    tbl['IUCN_FR'][g] = "Préoccupation mineure"
    tbl['IUCN_EN'][g] = "Least concern"

    g = tbl['IUCN'] == 'IUCN_NT'
    tbl['IUCN_FR'][g] = "Quasi-menacé"
    tbl['IUCN_EN'][g] = "Near threatened"

    g = tbl['IUCN'] == 'IUCN_VU'
    tbl['IUCN_FR'][g] = "Vulnérable"
    tbl['IUCN_EN'][g] = "Vulnerable"

    g = tbl['IUCN'] == 'IUCN_EN'
    tbl['IUCN_FR'][g] = "En danger"
    tbl['IUCN_EN'][g] = "Endangered"

    g = tbl['IUCN'] == 'IUCN_CR'
    tbl['IUCN_FR'][g] = "En danger critique"
    tbl['IUCN_EN'][g] = "Critically endangered"


    tbl['QUALITE'] = 0

    tbl['SP_ID'] = np.zeros_like(tbl,dtype = 'U99')
    tbl['NTH_ID'] = np.zeros_like(tbl,dtype = 'U99')

    val, index = np.unique(tbl['ML_CATALOG_NUMBERS'],return_index=True)
    tbl = tbl[index]



    tbl['DATA_TYPE'] = 'photo'
    tbl['XSIZE'] = 0
    tbl['YSIZE'] = 0

    tbl_data_type = Table.read('/Users/eartigau/wazo/data_type.csv')

    for i in tqdm(range(len(tbl))):
        id_ml = int(tbl['ML_CATALOG_NUMBERS'][i])
        if id_ml in tbl_data_type['ML_CATALOG_NUMBERS']:
            g = (np.where(tbl_data_type['ML_CATALOG_NUMBERS'] == id_ml))[0]
            if len(g) > 0:
                tbl['DATA_TYPE'][i] = tbl_data_type['DATA_TYPE'][g[0]]
                tbl['XSIZE'][i] = tbl_data_type['XSIZE'][g[0]]
                tbl['YSIZE'][i] = tbl_data_type['YSIZE'][g[0]]
                
                continue
        else:
            url = f"https://cdn.download.ams.birds.cornell.edu/api/v2/asset/{id_ml}/1200"

            response = requests.get(url)

            if response.status_code == 200:
                tbl['DATA_TYPE'][i] = 'photo'
                image = Image.open(BytesIO(response.content))
                width, height = image.size
                print(f"Image dimensions: {width} x {height}")
            
            else:
                print(f"Failed to download image. Status code: {response.status_code}")
                tbl['DATA_TYPE'][i] = 'audio'
                width = 0
                height = 0

        
        tbl_data_type.add_row()
        tbl_data_type['ML_CATALOG_NUMBERS'][-1] = id_ml
        tbl_data_type['DATA_TYPE'][-1] = tbl['DATA_TYPE'][i]
        tbl_data_type['XSIZE'][-1] = width
        tbl_data_type['YSIZE'][-1] = height

    tbl_data_type.write('/Users/eartigau/wazo/data_type.csv',overwrite=True,format='csv')

    tbl['AXIS_RATIO'] = tbl['XSIZE']/tbl['YSIZE']
    tbl = tbl[tbl['DATA_TYPE'] == 'photo']
    tbl = tbl[np.argsort(tbl['TAXONOMIC_ORDER'])]

    voyages = Table.read('/Users/eartigau/wazo/voyages.csv',delimiter=',',format='csv')

    tbl['VOYAGE_FR'] = np.zeros(len(tbl),dtype = 'U999')
    tbl['VOYAGE_EN'] =  np.zeros(len(tbl),dtype = 'U999')
    for i_voyage in range(len(voyages)):
        voyage_fr = voyages['VOYAGE_FR'][i_voyage]
        voyage_en = voyages['VOYAGE_EN'][i_voyage]

        g = (tbl['DATE'] >= voyages['DATE1'][i_voyage]) * (tbl['DATE'] <= voyages['DATE2'][i_voyage])
        tbl['VOYAGE_FR'][g] = voyage_fr
        tbl['VOYAGE_EN'][g] = voyage_en

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


#mk_web()

#def mkweb():
#
#    for ite in range(3):
#        tbl = master_photo_table()
#
#
#    return []

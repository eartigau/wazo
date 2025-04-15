import numpy as np
import matplotlib.pyplot as plt
import glob
import matplotlib.image as mpimg
#import matplotlib.patches as pat
from PIL import Image
import os as os
from astropy.table import Table
import matplotlib.image as mpimg 
from scipy import signal    


def drag():
    plt.ioff()

    ids = []
    xy01 = np.zeros([2,2])
    
    fics = np.array(glob.glob('/Users/eartigau/oiseaux3/oiseaux_originaux/wazo_*.jpg'))
    fics = fics[np.argsort(fics)]
    
    for i in range(len(fics)):
        #print(i,len(fics))
        fic = fics[i]
        
        outname1 = '/Users/eartigau/oiseaux3/peli/c_wazo_' + (((fics[i].split('/wazo_'))[1]).split('.'))[0]+'.png'
        outname2 = '/Users/eartigau/oiseaux3/peli/c_circle_' + (((fics[i].split('/wazo_'))[1]).split('.'))[0]+'.png'
        outname3 = '/Users/eartigau/oiseaux3/peli/c_square_' + (((fics[i].split('/wazo_'))[1]).split('.'))[0]+'.png'
        outname_lut = '/Users/eartigau/oiseaux3/peli/.' + (((fics[i].split('/wazo_'))[1]).split('.'))[0]+'.tbl'
        
        
        if  (os.path.isfile(outname2)   == False):
            print(i)
            im =  Image.open(fic)
            
            img = mpimg.imread(fic) 
            if os.path.isfile(outname_lut)   == False:
                #continue
                xy = [0,0]
                w = np.mean(img.shape[0:2])*.2     

                class DraggableRectangle:
                    def __init__(self, rect):
                        self.rect = rect
                        self.press = None
                
                    def connect(self):
                        'connect to all the events we need'
                        self.cidpress = self.rect.figure.canvas.mpl_connect(
                            'button_press_event', self.on_press)
                        self.cidrelease = self.rect.figure.canvas.mpl_connect(
                            'button_release_event', self.on_release)
                        self.cidmotion = self.rect.figure.canvas.mpl_connect(
                            'motion_notify_event', self.on_motion)
                
                    def on_press(self, event):
                        print('x')
                        'on button press we will see if the mouse is over us and store some data'
                        #print(event.x,event.y)
                        if event.inaxes != self.rect.axes:
                            print('y')
                            self.rect.set_width(self.rect.get_width()*1.1)
                            self.rect.set_height(self.rect.get_height()*1.1)
                            return
                
                        contains, attrd = self.rect.contains(event)
                        
                        if not contains:
                            print('z')

                            factor = 1+(event.xdata/img.shape[1]-.5)*.2
                            w=self.rect.get_width()*factor
                            
                            self.rect.set_width(w)
                            self.rect.set_height(w)
                            self.rect.set_x(self.rect.get_x()+w*(1-factor)/2)
                            self.rect.set_y(self.rect.get_y()+w*(1-factor)/2)
                            return
                        x0, y0 = self.rect.xy
                        self.press = x0, y0, event.xdata, event.ydata
                
                        
                        
                        #plt.plot(1000,1000,'o')#, **kwargs)[source]
                    
                
                    def on_motion(self, event):
                        'on motion we will move the rect if the mouse is over us'
                        if self.press is None: return
                        if event.inaxes != self.rect.axes: return
                        x0, y0, xpress, ypress = self.press
                        dx = event.xdata - xpress
                        dy = event.ydata - ypress
                        print('x0=%f, xpress=%f, event.xdata=%f, dx=%f, x0+dx=%f' %
                              (x0, xpress, event.xdata, dx, x0+dx))
                        self.rect.set_x(x0+dx)
                        self.rect.set_y(y0+dy)
                        print('xy :',self.rect.get_xy())
                        print('LW : ',self.rect.get_height()  )
                
                        self.rect.figure.canvas.draw()
                
                
                    def on_release(self, event):
                        'on release we reset the press data'
                        #print()
                        self.press = None
                        print(self.rect.xy)
                        print('width')
                        print(rect.get_width()  )
                        self.rect.figure.canvas.draw()
                
                        print('release :',self.cidrelease)
                        print('ids -=>',ids)
                
                
                
                
                        if self.cidrelease not in ids:
                            ids.append(self.cidrelease)
                 
                
                        if True:#len(ids) ==2:
                            g=  (np.where(self.cidrelease == np.array(ids)))[0]
                            g = g[0]
                            
                            xy01[g,0] = self.rect.xy[0]
                            xy01[g,1] = self.rect.xy[1]
                            
                            #print(xy01)
                            ax.imshow(img)
                            plt.plot([xy01[0,0],xy01[1,0]],[xy01[0,1],xy01[1,1]])
                            #xy01[:,= self.rect.xy
                            #print(xy01)
                            
                        
                        
                    def disconnect(self):
                        'disconnect all the stored connection ids'
                        self.rect.figure.canvas.mpl_disconnect(self.cidpress)
                        self.rect.figure.canvas.mpl_disconnect(self.cidrelease)
                        self.rect.figure.canvas.mpl_disconnect(self.cidmotion)
                
                fig = plt.figure()
                ax = fig.add_subplot(111)
                
                
                
                ax.imshow(img)
                
                rects = ax.bar([img.shape[1]/2.0],height = [w],width=[w],edgecolor = ['red'],facecolor = 'none',lw=[1])
                
                drs = []
                for rect in rects:
                    dr = DraggableRectangle(rect)
                    dr.connect()
                    drs.append(dr)
                plt.show(block=True)
                #stop
                
                x,y = rect.xy
                x=int(x)
                y=int(y)
                width = int(rect.get_width() )
                height = int(rect.get_height() )
                tbl = Table()
                tbl['x'] = [x]
                tbl['y'] = [y]
                tbl['width_x'] = [width]
                tbl['width_y'] = [height]
                stop
                tbl.write(outname_lut,format='csv')
                
                
            if os.path.isfile(outname_lut):
                print(outname_lut)
                tbl = Table.read(outname_lut,format='csv')
                x = (np.array(tbl['x']))[0]
                y = (np.array(tbl['y']))[0]
                width = (np.array(tbl['width_x']))[0]
                height = (np.array(tbl['width_y']))[0]

                imx = im.crop((int(x),int(y),int(x+width),int(y+height)))
            else:
                fic2 = '/Users/eartigau/oiseaux3/sm_wazo/sm_wazo_' + (((fics[i].split('/wazo_'))[1]).split('.'))[
                    0]+'.jpg'
                imx =  Image.open(fic2)
                print('lecture '+fic2)

            width = 120
            imx2 = np.array(imx.resize((width,height))   )
            xx,yy = np.indices([width,width])
            r = np.sqrt(  ((xx-width/2.1)/(width/2.1))**2+ ((yy-width/2.1)/(width/2.1))**2)

            transp = 1/(1+r**100)
            
            img_out = np.zeros([width,width,4])
            for i in range(3):
                img_out[:,:,i] = imx2[:,:,i]/255.0
            img_out[:,:,3] = trans
            stop

            print('we write '+outname2)
            mpimg.imsave(outname2,img_out)    

    return []

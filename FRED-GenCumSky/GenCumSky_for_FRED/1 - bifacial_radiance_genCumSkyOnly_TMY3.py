# -*- coding: utf-8 -*-
"""
Created on Sun Jun 24 14:55:36 2018

@author: Psl
"""

from __future__ import division  # avoid integer division issues.
'''
@author: cdeline

bifacial_radiance.py - module to develop radiance bifacial scenes, including gendaylit and gencumulativesky
7/5/2016 - test script based on G173_journal_height
5/1/2017 - standalone module

Pre-requisites:
    This software is written in Python 2.7 leveraging many Anaconda tools (e.g. pandas, numpy, etc)
    
    *RADIANCE software should be installed from https://github.com/NREL/Radiance/releases

    *If you want to use gencumulativesky, move 'gencumulativesky.exe' from 
    'bifacial_radiance\data' into your RADIANCE source directory.

    *If using a Windows machine you should download the Jaloxa executables at 
    http://www.jaloxa.eu/resources/radiance/radwinexe.shtml#Download

    * Installation of  bifacial_radiance from the repo:
    1. Clone the repo
    2. Navigate to the directory using the command prompt
    3. run `pip install -e . `

Overview:  
    Bifacial_radiance includes several helper functions to make it easier to evaluate
    different PV system orientations for rear bifacial irradiance.
    Note that this is simply an optical model - identifying available rear irradiance under different conditions.
    
    For a detailed demonstration example, look at the .ipnyb notebook in \docs\
    
    There are two solar resource modes in bifacial_radiance: `gendaylit` uses hour-by-hour solar
    resource descriptions using the Perez diffuse tilted plane model.
    `gencumulativesky` is an annual average solar resource that combines hourly
    Perez skies into one single solar source, and computes an annual average.
    
    bifacial_radiance includes five object-oriented classes:
    
    RadianceObj:  top level class to work on radiance objects, keep track of filenames, 
    sky values, PV module type etc.
    
    GroundObj:    details for the ground surface and reflectance
    
    SceneObj:    scene information including array configuration (row spacing, ground height)
    
    MetObj: meteorological data from EPW (energyplus) file.  
        Future work: include other file support including TMY files
    
    AnalysisObj: Analysis class for plotting and reporting
    
'''
'''
Revision history
0.2.1:  Allow tmy3 input files.  Use a different EPW file reader.
0.2.0:  Critical 1-axis tracking update to fix geometry issues that were over-predicting 1-axis results
0.1.1:  Allow southern latitudes
0.1.0:  1-axis bug fix and validation vs PVSyst and ViewFactor model
0.0.5:  1-axis tracking draft
0.0.4:  Include configuration file module.json and custom module configuration
0.0.3:  Arbitrary NxR number of modules and rows for SceneObj 
0.0.2:  Adjustable azimuth angle other than 180
0.0.1:  Initial stable release
'''
import os, datetime
import matplotlib.pyplot as plt  
import pandas as pd
import numpy as np #already imported with above pylab magic
#from IPython.display import Image
from subprocess import Popen, PIPE  # replacement for os.system()
#import shlex
from readepw import readepw # epw file reader from pvlib development forums

import pkg_resources
global DATA_PATH # path to data files including module.json.  Global context
#DATA_PATH = pkg_resources.resource_filename('bifacial_radiance', 'data/') 
DATA_PATH = os.path.abspath(pkg_resources.resource_filename('bifacial_radiance', 'data/') )


def _findme(lst, a): #find string match in a list. found this nifty script on stackexchange
    return [i for i, x in enumerate(lst) if x==a]


def _normRGB(r,g,b): #normalize by weight of each color for human vision sensitivity
    return r*0.216+g*0.7152+b*0.0722

def _popen(cmd, data_in, data_out=PIPE):
    """
    Helper function subprocess.popen replaces os.system 
    - gives better input/output process control
    usage: pass <data_in> to process <cmd> and return results
    from rgbeimage.py (Thomas Bleicher 2010)
    """
    cmd = str(cmd) # get's rid of unicode oddities
    #p = Popen(shlex.split(cmd), bufsize=-1, stdin=PIPE, stdout=data_out, stderr=PIPE)
    p = Popen(cmd, bufsize=-1, stdin=PIPE, stdout=data_out, stderr=PIPE)
    data, err = p.communicate(data_in)
    if err:
        return 'message: '+err.strip()
    if data:
        return data

def _interactive_load(title = None):
    # Tkinter file picker
    import Tkinter
    from tkFileDialog import askopenfilename
    root = Tkinter.Tk()
    root.withdraw() #Start interactive file input
    root.attributes("-topmost", True) #Bring window into foreground
    return askopenfilename(parent = root, title = title) #initialdir = data_dir

def _interactive_directory(title = None):
    # Tkinter directory picker
    import Tkinter
    from tkFileDialog import askdirectory
    root = Tkinter.Tk()
    root.withdraw() #Start interactive file input
    root.attributes("-topmost", True) #Bring to front
    return askdirectory(parent = root, title = title)


        

class RadianceObj:
    '''
    RadianceObj:  top level class to work on radiance objects, keep track of filenames, 
    sky values, PV module configuration etc.

    
    values:
        name    : text to append to output files
        filelist    : list of Radiance files to create oconv
        nowstr      : current date/time string
        path        : working directory with Radiance materials and objects
        TODO:  populate this more
    functions:
        __init__   : initialize the object
        _setPath    : change the working directory
        TODO:  populate this more
    
    '''
    
    def __init__(self, name=None, path=None):
        '''
        Description
        -----------
        initialize RadianceObj with path of Radiance materials and objects,
        as well as a basename to append to 
    
        Parameters
        ----------
        name: string, append temporary and output files with this value
        path: location of Radiance materials and objects
    
        Returns
        -------
        none
        '''

        self.metdata = {}        # data from epw met file
        self.data = {}           # data stored at each timestep
        self.path = ""             # path of working directory
        self.name = ""         # basename to append
        #self.filelist = []         # list of files to include in the oconv
        self.materialfiles = []    # material files for oconv
        self.skyfiles = []          # skyfiles for oconv
        self.radfiles = []      # scene rad files for oconv
        self.octfile = []       #octfile name for analysis
                

        now = datetime.datetime.now()
        self.nowstr = str(now.date())+'_'+str(now.hour)+str(now.minute)+str(now.second)
        
        ''' DEFAULTS '''
        #TODO:  check if any of these defaults are necessary
        #self.material_path = "materials"      # directory of materials data. default 'materials'
        #self.sky_path = 'skies'         # directory of sky data. default 'skies'
        #TODO: check if lat/lon/epwfile should be defined in the meteorological object instead
        #self.latitude = 40.02           # default - Boulder
        #self.longitude = -105.25        # default - Boulder
        #self.epwfile = 'USA_CO_Boulder.724699_TMY2.epw'  # default - Boulder
        
        
        if name is None:
            self.name = self.nowstr  # set default filename for output files
        else:
            self.name = name
        self.basename = name # add backwards compatibility for prior versions
        #self.__name__ = self.name  #optional info
        #self.__str__ = self.__name__   #optional info
        if path is None:
            self._setPath(os.getcwd())
        else:
            self._setPath(path)
        
        self.materialfiles = self.returnMaterialFiles('materials')  # load files in the /materials/ directory

    def _setPath(self, path):
        '''
        setPath - move path and working directory
        
        '''
        self.path = path
        
        print('path = '+ path)
        try:
            os.chdir(self.path)
        except:
            print('Path doesn''t exist: %s' % (path)) 
        
        # check for path in the new Radiance directory:
        def _checkPath(path):  # create the file structure if it doesn't exist
            if not os.path.exists(path):
                os.makedirs(path)
                print('Making path: '+path)
                
        _checkPath('images/'); _checkPath('objects/');  _checkPath('results/'); _checkPath('skies/'); _checkPath('EPWs/'); 
        # if materials directory doesn't exist, populate it with ground.rad
        # figure out where pip installed support files. 
        from shutil import copy2 

        if not os.path.exists('materials/'):  #copy ground.rad to /materials
            os.makedirs('materials/') 
            print('Making path: materials/')

            copy2(os.path.join(DATA_PATH,'ground.rad'),'materials')
        # if views directory doesn't exist, create it with two default views - side.vp and front.vp
        if not os.path.exists('views/'):
            os.makedirs('views/')
            with open('views/side.vp', 'wb') as f:
                f.write('rvu -vtv -vp -10 1.5 3 -vd 1.581 0 -0.519234 -vu 0 0 1 -vh 45 -vv 45 -vo 0 -va 0 -vs 0 -vl 0') 
            with open('views/front.vp', 'wb') as f:
                f.write('rvu -vtv -vp 0 -3 5 -vd 0 0.894427 -0.894427 -vu 0 0 1 -vh 45 -vv 45 -vo 0 -va 0 -vs 0 -vl 0') 

    def getfilelist(self):
        ''' return concat of matfiles, radfiles and skyfiles
        '''
        return self.materialfiles + self.skyfiles + self.radfiles
    
    def returnOctFiles(self):
        '''
        return files in the root directory with .oct extension
        
        Returns
        -------
        oct_files : list of .oct files
        
        '''
        oct_files = [f for f in os.listdir(self.path) if f.endswith('.oct')]
        #self.oct_files = oct_files
        return oct_files
        
    def returnMaterialFiles(self, material_path = None):
        '''
        return files in the Materials directory with .rad extension
        appends materials files to the oconv file list
        
        Parameters
        ----------
        material_path - optional parameter to point to a specific materials directory. 
        otherwise /materials/ is default
        
        Returns
        -------
        material_files : list of .rad files
        
        '''
        if material_path is None:
            material_path = 'materials'

        material_files = [f for f in os.listdir(os.path.join(self.path, material_path)) if f.endswith('.rad')]
        
        materialfilelist = [os.path.join(material_path,f) for f in material_files]
        self.materialfiles = materialfilelist
        return materialfilelist
        
    def setGround(self, material = None, material_file = None):
        ''' use GroundObj constructor and return a ground object
        '''
        
        ground_data = GroundObj(material, material_file)
        if material is not None:
            self.ground= ground_data
        else:
            self.ground = None
            
    def getEPW(self,lat,lon):
        ''' 
        Subroutine to download nearest epw files available into the directory \EPWs\
        
        based on github/aahoo
        **note that verify=false is required to operate within NREL's network.
        to avoid annoying warnings, insecurerequestwarning is disabled
        currently this function is not working within NREL's network.  annoying!
        '''
        import numpy as np
        import pandas as pd
        import requests, re
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        hdr = {'User-Agent' : "Magic Browser",
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        path_to_save = 'EPWs\\' # create a directory and write the name of directory here
        if not os.path.exists(path_to_save):
            os.makedirs(path_to_save)
        r = requests.get('https://github.com/NREL/EnergyPlus/raw/develop/weather/master.geojson', verify = False)
        data = r.json() #metadata for available files
        #download lat/lon and url details for each .epw file into a dataframe
        
        df = pd.DataFrame({'url':[],'lat':[],'lon':[],'name':[]})
        for location in data['features']:
            match = re.search(r'href=[\'"]?([^\'" >]+)', location['properties']['epw'])
            if match:
                url = match.group(1)
                name = url[url.rfind('/') + 1:]
                lontemp = location['geometry']['coordinates'][0]
                lattemp = location['geometry']['coordinates'][1]
                dftemp = pd.DataFrame({'url':[url],'lat':[lattemp],'lon':[lontemp],'name':[name]})
                df=df.append(dftemp, ignore_index = True)
  
        #locate the record with the nearest lat/lon
        errorvec = np.sqrt(np.square(df.lat - lat) + np.square(df.lon - lon))
        index = errorvec.idxmin()
        url = df['url'][index]
        name = df['name'][index]
        # download the .epw file to \EPWs\ and return the filename
        print 'Getting weather file: ' + name,
        r = requests.get(url,verify = False, headers = hdr)
        if r.ok:
            with open(path_to_save + name, 'wb') as f:
                f.write(r.text)
            print ' ... OK!'
        else:
            print ' connection error status code: %s' %( r.status_code)
            r.raise_for_status()
        
        self.epwfile = 'EPWs\\'+name
        return 'EPWs\\'+name
    
    def getEPW_all(self):
        ''' 
        Subroutine to download ALL available epw files available into the directory \EPWs\
        
        based on github/aahoo
        **note that verify=false is required to operate within NREL's network.
        to avoid annoying warnings, insecurerequestwarning is disabled
        currently this function is not working within NREL's network.  annoying!
        '''
        import requests, re
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
     
        path_to_save = 'EPWs\\' # create a directory and write the name of directory here
        if not os.path.exists(path_to_save):
            os.makedirs(path_to_save)
        r = requests.get('https://github.com/NREL/EnergyPlus/raw/develop/weather/master.geojson', verify = False)
        data = r.json()
    
        for location in data['features']:
            match = re.search(r'href=[\'"]?([^\'" >]+)', location['properties']['epw'])
            if match:
                url = match.group(1)
                name = url[url.rfind('/') + 1:]
                print name
                r = requests.get(url,verify = False)
                if r.ok:
                    with open(path_to_save + name, 'wb') as f:
                        f.write(r.text.encode('ascii','ignore'))
                else:
                    print ' connection error status code: %s' %( r.status_code)
        print 'done!'    
    

        
    def readTMY(self,tmyfile=None):
        '''
        use pvlib to read in a tmy3 file.  

        
        Parameters
        ------------
        tmyfile:  filename of tmy3 to be read with pvlib.tmy.readtmy3

        Returns
        -------
        metdata - MetObj collected from TMY3 file
        '''
        import pvlib

        if tmyfile is None:
            try:
                tmyfile = _interactive_load()
            except:
                raise Exception('Interactive load failed. Tkinter not supported on this system. Try installing X-Quartz and reloading')

        (tmydata,metadata)=pvlib.tmy.readtmy3(tmyfile)
        # TODO:  replace MetObj _init_ behavior with initTMY behavior
        self.metdata = MetObj(tmydata,metadata)
        #self.metdata = self.metdata.initTMY(tmydata,metadata) # initialize the MetObj using TMY instead of EPW
        csvfile = os.path.join('EPWs','tmy3_temp.csv') #temporary filename with 2-column GHI,DHI data
        #Create new temp csv file for gencumsky. write 8760 2-column csv:  GHI,DHI
        savedata = pd.DataFrame({'GHI':tmydata['GHI'], 'DHI':tmydata['DHI']})  # save in 2-column GHI,DHI format for gencumulativesky -G
        print('Saving file {}, # points: {}'.format(csvfile,savedata.__len__()))
        savedata.to_csv(csvfile,index = False, header = False, sep = ' ', columns = ['GHI','DHI'])
        self.epwfile = csvfile

        return self.metdata    

    def readEPW(self,epwfile=None):
        ''' 
        use readepw from pvlib development forums
        https://github.com/pvlib/pvlib-python/issues/261
        
        rename tmy columns to match: DNI, DHI, GHI, DryBulb, Wspd
        '''
        #from readepw import readepw   # epw file reader from pvlib development forums
        if epwfile is None:
            try:
                epwfile = _interactive_load()
            except:
                raise Exception('Interactive load failed. Tkinter not supported on this system. Try installing X-Quartz and reloading')
        (tmydata,metadata) = readepw(epwfile)
        # rename different field parameters to match output from pvlib.tmy.readtmy: DNI, DHI, DryBulb, Wspd
        tmydata.rename(columns={'Direct normal radiation in Wh/m2':'DNI','Diffuse horizontal radiation in Wh/m2':'DHI',
                                'Dry bulb temperature in C':'DryBulb','Wind speed in m/s':'Wspd',
                                'Global horizontal radiation in Wh/m2':'GHI'}, inplace=True)
           
        self.metdata = MetObj(tmydata,metadata)
        
        # copy the epwfile into the /EPWs/ directory in case it isn't in there already
        if os.path.isabs(epwfile):
            from shutil import copyfile
            dst = os.path.join(self.path,'EPWs',os.path.split(epwfile)[1])
            try:
                copyfile(epwfile,dst) #this may fail if the source and destination are the same
            except:
                pass
            self.epwfile = os.path.join('EPWs',os.path.split(epwfile)[1])
                    
        else:
            self.epwfile = epwfile 
        

        
        return self.metdata

        
    def readEPW_old(self,epwfile=None):
        '''
        use pyepw to read in a epw file.  
        ##  Deprecated. no longer works with updated MetObj.__init__ behavior ##
        pyepw installation info:  pip install pyepw
        documentation: https://github.com/rbuffat/pyepw
        
        Parameters
        ------------
        epwfile:  filename of epw

        Returns
        -------
        metdata - MetObj collected from epw file
        '''
        if epwfile is None:
            try:
                epwfile = _interactive_load()
            except:
                raise Exception('Interactive load failed. Tkinter not supported on this system. Try installing X-Quartz and reloading')

        try:
            from pyepw.epw import EPW
        except:
            print('Error: pyepw not installed.  try pip install pyepw')
        epw = EPW()
        epw.read(epwfile)
        
        self.metdata = MetObj(epw)
        self.epwfile = epwfile  # either epw of csv file to pass in to gencumsky
        return self.metdata
        
    def gendaylit(self, metdata, timeindex):
        '''
        sets and returns sky information using gendaylit.  if material type is known, pass it in to get
        reflectance info.  if material type isn't known, material_info.list is returned
        Note - -W and -O1 option is used to create full spectrum analysis in units of Wm-2
        Parameters
        ------------
        metdata:  MetObj object with 8760 list of dni, dhi, ghi and location
        timeindex: index from 0 to 8759 of EPW timestep
        
        Returns
        -------
        skyname:   filename of sky in /skies/ directory
        
        '''
        locName = metdata.city
        month = metdata.datetime[timeindex].month
        year = metdata.datetime[timeindex].year
        day = metdata.datetime[timeindex].day
        hour = metdata.datetime[timeindex].hour
        minute = metdata.datetime[timeindex].minute
        timeZone = metdata.timezone
        dni = metdata.dni[timeindex]
        dhi = metdata.dhi[timeindex]
        
        print "DNI is", dni
        print "DHI is", dhi
        print "date", month, "/", day, "/", year, "  at hour ", hour
        
        sky_path = 'skies'

         #" -L %s %s -g %s \n" %(dni/.0079, dhi/.0079, self.ground.ReflAvg) + \
        skyStr =   ("# start of sky definition for daylighting studies\n"  
            "# location name: " + str(locName) + " LAT: " + str(metdata.latitude) 
            +" LON: " + str(metdata.longitude) + "\n"
            "!gendaylit %s %s %s" %(month,day,hour+minute/60.0) ) + \
            " -a %s -o %s" %(metdata.latitude, metdata.longitude) +\
            " -m %s" % (float(timeZone)*15) +\
            " -W %s %s -g %s -O 1 \n" %(dni, dhi, self.ground.ReflAvg) + \
            "skyfunc glow sky_mat\n0\n0\n4 1 1 1 0\n" + \
            "\nsky_mat source sky\n0\n0\n4 0 0 1 180\n" + \
            '\nskyfunc glow ground_glow\n0\n0\n4 ' + \
            '%s ' % (self.ground.Rrefl/self.ground.normval)  + \
            '%s ' % (self.ground.Grefl/self.ground.normval) + \
            '%s 0\n' % (self.ground.Brefl/self.ground.normval) + \
            '\nground_glow source ground\n0\n0\n4 0 0 -1 180\n' +\
            "\nvoid plastic %s\n0\n0\n5 %0.3f %0.3f %0.3f 0 0\n" %(
            self.ground.ground_type,self.ground.Rrefl,self.ground.Grefl,self.ground.Brefl) +\
            "\n%s ring groundplane\n" % (self.ground.ground_type) +\
            '0\n0\n8\n0 0 -.01\n0 0 1\n0 100'
         
        skyname = os.path.join(sky_path,"sky_%s.rad" %(self.name))
            
        skyFile = open(skyname, 'w')
        skyFile.write(skyStr)
        skyFile.close()
        
        self.skyfiles = [skyname ]
        
        return skyname
        
    def genCumSky(self,epwfile = None, startdt = None, enddt = None, savefile = None):
        ''' genCumSky
        
        skydome using gencumsky.  note: gencumulativesky.exe is required to be installed,
        which is not a standard radiance distribution.
        You can find the program in the bifacial_radiance distribution directory 
        in \Lib\site-packages\bifacial_radiance\data
        
        TODO:  error checking and auto-install of gencumulativesky.exe  
        
        update 0.0.5:  allow -G filetype option for support of 1-axis tracking
        
        Parameters
        ------------
        epwfile             - filename of the .epw file to read in (-E mode) or 2-column csv (-G mode). 
        hour                - tuple start, end hour of day. default (0,24)
        startdatetime       - datetime.datetime(Y,M,D,H,M,S) object. Only M,D,H selected. default: (0,1,1,0)
        enddatetime         - datetime.datetime(Y,M,D,H,M,S) object. Only M,D,H selected. default: (12,31,24,0)
        savefile            - 
        
        Returns
        -------
        skyname - filename of the .rad file containing cumulativesky info
        '''

        if epwfile is None:
            epwfile = self.epwfile
        if epwfile.endswith('epw'):
            filetype = '-E'  # EPW file input into gencumulativesky
        else:
            filetype = '-G'  # 2-column csv input: GHI,DHI
        
        for foo in range(0,8760):
            locName = metdata.city
            year = metdata.datetime[foo].year
            month = metdata.datetime[foo].month
            day = metdata.datetime[foo].day
            hour = metdata.datetime[foo].hour
            minute = metdata.datetime[foo].minute
            timeZone = metdata.timezone

            print foo , " --> " , year, month, day, hour

            # IMPORTANT TRICK:
            # Sun is not out at 23 hours, and to avoid the program crashing with
            # the 24 hour that TMY3 has, we are just setting it to believe it's
            # still 23. It wil lgenerate a .cal with all 0s.
            # This will not work for latitudes TOO Close to the north pole.
            # But guess what... I don't care at the moment.
            if hour>=23:
                hour = 22    
                
            startdt = datetime.datetime(year,month,day,hour)
            enddt = datetime.datetime(year,month,day,hour+1)
            savefile = "cumulative"
            print startdt
            print enddt
            sky_path = 'skies'
            lat = self.metdata.latitude
            lon = self.metdata.longitude
            timeZone = self.metdata.timezone
            '''
            cmd = "gencumulativesky +s1 -h 0 -a %s -o %s -m %s -E " %(lat, lon, float(timeZone)*15) +\
                "-time %s %s -date 6 17 6 17 %s > cumulative.cal" % (epwfile)     
            print cmd
            os.system(cmd)
            '''
            cmd = "gencumulativesky +s1 -h 0 -a %s -o %s -m %s %s " %(lat, lon, float(timeZone)*15, filetype) +\
                "-time %s %s -date %s %s %s %s %s" % (startdt.hour, enddt.hour+1, 
                                                      startdt.month, startdt.day, 
                                                      enddt.month, enddt.day,
                                                      epwfile) 
    
            with open(savefile+"_"+str(foo)+".cal","w") as f:
                err = _popen(cmd,None,f)
                if err is not None:
                    print err
        
if __name__ == "__main__":
    '''
    Example of how to run a Radiance routine for a simple rooftop bifacial system

    '''
#    testfolder = _interactive_directory(title = 'Select or create an empty directory for the Radiance tree')
    testfolder = r'C:\Users\Psl\Documents\RadianceScenes\Test3'
    demo = RadianceObj('simple_panel',path = testfolder)  # Create a RadianceObj 'object'
    demo.setGround(0.62) # input albedo number or material name like 'concrete'.  To see options, run this without any input.
    try:
       epwfile = demo.getEPW(32.133,-110.96) # pull TMY data for any global lat/lon
    except:
        pass
   
    metdata = demo.readEPW(epwfile) # read in the EPW weather data from above
    #metdata = demo.readTMY() # select a TMY file using graphical picker
    # Now we either choose a single time point, or use cumulativesky for the entire year. 
    fullYear = 
    #startdatetime       - datetime.datetime(Y,M,D,H,M,S) object. Only M,D,H selected. default: (0,1,1,0)
        #enddatetime         - datetime.datetime(Y,M,D,H,M,S) object. Only M,D,H selected. default: (12,31,24,0)
    startdatetime=datetime.datetime(2001,1,1,10)  
    enddatetime=datetime.datetime(2001,1,1,11)
    
    if fullYear:
        demo.genCumSky(demo.epwfile) # entire year.

#        demo.genCumSky(demo.epwfile, startdatetime,enddatetime) # entire year.
    else:
        demo.gendaylit(metdata,4020)  # Noon, June 17th
   
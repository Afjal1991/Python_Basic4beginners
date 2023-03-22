"""
Various functions commonly used in codes in this directory

Daeho Jin
"""

import sys
import os.path
import numpy as np
from datetime import date

def bin_file_read2mtx(fname, dtype=np.float32):
    """ Open a binary file, and read data
        fname : file name with directory path
        dtype   : data type; np.float32 or np.float64, etc. """

    if not os.path.isfile(fname):
        print("File does not exist:"+fname)
        sys.exit()

    with open(fname,'rb') as fd:
        bin_mat = np.fromfile(file=fd, dtype=dtype)

    return bin_mat

from math import ceil
def lon_deg2x(lon,lon0,dlon):
    '''
    For given longitude information, return index of given specific longitude
    lon: target longitude to be transformed to index
    lon0: the first (smallest) value of longitude grid
    dlon: the increment of longitude grid
    return: integer index
    '''
    x = ceil((lon-lon0)/dlon)
    nx = int(360/dlon)
    if x<0:
        while(x<0):
            x+= nx
    if x>=nx: x=x%nx
    return x
lat_deg2y = lambda lat,lat0,dlat: ceil((lat-lat0)/dlat)

def get_tgt_latlon_idx(latlons, tgt_lats, tgt_lons):
    lon0,dlon,nlon= latlons['loninfo']
    lat0,dlat,nlat= latlons['latinfo']
    ##-- Regional index
    if isinstance(tgt_lons,(list,tuple,np.ndarray)):
        lon_idx= [lon_deg2x(ll,lon0,dlon) for ll in tgt_lons]
        if lon_idx[0]==lon_idx[1]:
            if tgt_lons[0]!=tgt_lons[1]:
                lon_ids= np.arange(nlon)+lon_idx[0]
                lon_ids[lon_ids>=nlon] -= nlon
            else:
                lon_ids= np.array([lon_idx,])
        elif lon_idx[1]<lon_idx[0]:
            lon_ids= np.arange(lon_idx[0]-nlon,lon_idx[1],1)
        else:
            lon_ids= np.arange(lon_idx[0], lon_idx[1], 1)
    else:
        lon_ids= np.arange(nlon,dtype=int)
    lat_idx= [lat_deg2y(ll,lat0,dlat) for ll in tgt_lats]
    return lat_idx, lon_ids

def lon_formatter(x,pos):
    if x<=-180: x+=360
    elif x>=360: x-=360

    if x>0 and x<180:
        return "{:.0f}\u00B0E".format(x)
    elif x>180 and x<360:
        return "{:.0f}\u00B0W".format(360-x)
    elif x>-180 and x<0:
        return "{:.0f}\u00B0W".format(-x)
    else:
        return "{:.0f}\u00B0".format(x)

def lat_formatter(x,pos):
    if x>0:
        return "{:.0f}\u00B0N".format(x)
    elif x<0:
        return "{:.0f}\u00B0S".format(-x)
    else:
        return "{:.0f}\u00B0".format(x)

def read_sst_from_HadISST(yrs=[2014,2021],include_ice=False):
    ###--- Parameters
    indir= '../Data/'
    yrs0= [2014,2021]
    lon0,dlon,nlon= -179.5,1.,360
    lat0,dlat,nlat=  -89.5,1.,180
    mon_per_yr= 12
    nt= (yrs0[1]-yrs0[0]+1)*mon_per_yr

    infn= indir+"HadISST1.sample.{}-{}.{}x{}x{}.f32dat".format(*yrs0,nt,nlat,nlon)
    sst= bin_file_read2mtx(infn)  # 'dtype' option is omitted because 'f32' is basic dtype
    sst= sst.reshape([nt,nlat,nlon]).astype(float)  # Improve precision of calculation

    it= (yrs[0]-yrs0[0])*mon_per_yr
    nmons= (yrs[1]-yrs[0]+1)*mon_per_yr
    if (it != 0) or (nmons != nt):
        sst= sst[it:it+nmons,:,:]
    print(sst.shape)

    ### We already know that missings are -999.9, and ice-cover value is -10.00.
    if include_ice:
        miss_idx= sst<-11
    else:
        miss_idx= sst<-9.9
    sst[miss_idx]= np.nan

    lat_info= dict(lat0=lat0,dlat=dlat,nlat=nlat)
    lon_info= dict(lon0=lon0,dlon=dlon,nlon=nlon)
    return sst, lat_info,lon_info

def get_sst_ano_from_HadISST(area_bound,yrs=[2014,2021],remove_AC=True):
    '''
    area_bound= [west,east,south,north] in degrees
    '''

    ### Read SST
    sst, lats, lons= read_sst_from_HadISST(yrs=yrs)

    ### Check validity of given area bound
    if area_bound[2]<lats['lat0'] or area_bound[3]>lats['lat0']+lats['dlat']*lats['nlat']:
        print("area_bound is out of limit", area_bound, lats)
        sys.exit()

    ### Cut by given area_bound
    latlons= dict(latinfo=(lats['lat0'],lats['dlat'],lats['nlat']),
                    loninfo=(lons['lon0'],lons['dlon'],lons['nlon']))
    lat_idx, lon_ids = get_tgt_latlon_idx(latlons, area_bound[2:], area_bound[:2])
    sst= sst[:,lat_idx[0]:lat_idx[1],lon_ids]

    ##- Update parameters
    nt,nlat,nlon= sst.shape
    lons['lon0']= lons['lon0']+lons['dlon']*lon_ids[0]
    lons['nlon']= nlon
    lats['lat0']= lats['lat0']+lats['dlat']*lat_idx[0]
    lats['nlat']= nlat

    ### Remove annual mean
    sstm= sst.mean(axis=0)
    sstano= sst-sstm[None,:,:]  # This is for masking grid cells having any NaN
    sst=1  # Flush sst array data from memory because it's unnecessary hereinafter

    if remove_AC:
        ### Remove seasonal cycle
        mon_per_yr=12
        ssn_mean= sstano.reshape([-1,mon_per_yr,nlat,nlon]).mean(axis=0)
        sstano= (sstano.reshape([-1,mon_per_yr,nlat,nlon])-ssn_mean[None,:,:,:]).reshape([nt,nlat,nlon])

    return sstano, lats, lons

def get_sst_areamean_from_HadISST(area_bound,yrs= [2014,2021],remove_AC=True):
    '''
    area_bound= [west,east,south,north] in degrees
    '''
    ### Read SST
    sst, lats, lons= read_sst_from_HadISST(yrs=yrs)

    ### Check validity of given area bound
    if area_bound[2]<lats['lat0'] or area_bound[3]>lats['lat0']+lats['dlat']*lats['nlat']:
        print("area_bound is out of limit", area_bound, lats)
        sys.exit()

    ### Calculate area mean
    latlons= dict(latinfo=(lats['lat0'],lats['dlat'],lats['nlat']),
                    loninfo=(lons['lon0'],lons['dlon'],lons['nlon']))
    lat_idx, lon_ids = get_tgt_latlon_idx(latlons, area_bound[2:], area_bound[:2])
    am= np.nanmean(sst[:,lat_idx[0]:lat_idx[1],lon_ids],axis=(1,2))
    print([lon_ids[0],lon_ids[-1]]+lat_idx,am.shape, am.min(), am.max())  # Check if NaN exists here

    if remove_AC:
        ### Remove seasonal cycle
        mon_per_yr=12
        am_mean= am.reshape([-1,mon_per_yr]).mean(axis=0)
        am= (am.reshape([-1,mon_per_yr])-am_mean[None,:]).reshape(-1)

    return am

def read_rmm_text(date_range=[]):
    """
    Read RMM Index Text file
    fname: include directory
    date_range: start and end dates, including both end dates, optional
    """
    indir= '../Data/'
    fname= indir+'rmm.74toRealtime.txt'

    if not os.path.isfile(fname):
        #print( "File does not exist:"+fname); sys.exit()
        sys.exit("File does not exist: "+fname)

    if len(date_range)!=0 and len(date_range)!=2:
        print("date_range should be [] or [ini_date,end_date]")
        sys.exit()

    time_info=[]; pcs=[]; phs=[]
    with open(fname,'r') as f:
        for i,line in enumerate(f):
            if i>=2:  ### Skip header (2 lines)
                ww=line.strip().split() #
                onedate=date(*map(int,ww[0:3])) ### "map()": Apply "int()" function to each member of ww[0:3]
                if len(date_range)==0 or (len(date_range)==2 and onedate>=date_range[0] and onedate<=date_range[1]):
                    pcs.append([float(ww[3]),float(ww[4])]) ### RMM PC1 and PC2
                    phs.append(int(ww[5]))  ### MJO Phase
                    time_info.append(onedate)  ### Save month only

    print("Total RMM data record=",len(phs))
    time_info, pcs, phs= np.asarray(time_info),np.asarray(pcs),np.asarray(phs) ### Return as Numpy array
    strs= np.sqrt((pcs**2).sum(axis=1))  # Euclidean distance

    ### Check missing
    miss_idx= phs==999
    if miss_idx.sum()>0:
        print("There are {} missing(s)".format(miss_idx.sum()))
    else:
        print("No missings")

    return time_info, pcs, phs, strs, miss_idx

def get_monthly_dates(date1,date2,day=1,include_date2=True):
    '''
    From date1 to date2 (include or not), yield date monthly.
    "day" indicates default day of each month.
    '''
    mon_per_year=12
    ## Make sure date1 is before date2
    if date1>date2:
        tmpdate= date1
        date1= date2
        date2= tmpdate
    yr1,mo1= date1.year, date1.month
    yr2,mo2= date2.year, date2.month

    outdates=[]
    while True:
        outdates.append(date(yr1,mo1,day))
        mo1+=1
        if mo1>mon_per_year:
            mo1=1
            yr1+=1
        if yr1==yr2 and mo1==mo2:
            break
    if include_date2:
        outdates.append(date(yr1,mo1,day))
    return outdates

def acf(ts1,nlags=None):
    """
    Calculate a series of auto-correlation
    ts1: 1-d time series having no missings
    nlags: maximum number of lag to calculate auto-correlation
    """
    if nlags==None:
        nlags= len(ts1)-1
    else:
        nlags= min(nlags,len(ts1)-1)
    xx,ac= [],[]
    for lag in range(nlags+1):
        xx.append(lag)
        if lag>0:
            ac.append(((ts1[lag:]-ts1[lag:].mean())*(ts1[:-lag]-ts1[:-lag].mean())).sum())
        else:
            ac.append(((ts1-ts1.mean(axis=0))**2).sum())
    ac,xx= np.asarray(ac), np.asarray(xx)
    ac= ac/ac[0]

    return ac,xx

import scipy.stats as st
def get_Eff_DOF(ts1,ts2=[],is_ts1_AR1=True,adjust_AR1=True):
    '''
    Calculate dependency_level in order to estimate "Effective Degrees of Freedom"

    Bayley & Hammersley 1946, http://doi.org/10.2307/2983560
    von Storch & Zwiers 1999, ISBN ‏ : ‎ 0521012309
    Afyouni et al. 2019, https://doi.org/10.1016/j.neuroimage.2019.05.011
    https://stats.stackexchange.com/questions/151604/what-is-bartletts-theory

    '''
    def Tukey_window(ts1):
        '''
        !!!! Tukey window
        '''
        n= len(ts1)
        lim=4.7*n**0.5 #4.7
        for tau in range(1,n,1):
            if (tau<=lim):
                ts1[tau]=ts1[tau]*(1+np.cos(np.pi*tau/lim))/2
            else:
                ts1[tau]=0.
        return ts1,int(lim+1)

    def ccf(ts1,ts2,nlags=None):
        """
        Calculate a series of cross-correlation (similar to auto-correlation)
        ts1,ts2: 1-d time series having no missings
        nlags: maximum number of lag to calculate auto-correlation
        """
        if nlags==None:
            nlags= len(ts1)-1
        else:
            nlags= min(nlags,len(ts1)-1)
        xx,cc= [],[]
        for lag in range(nlags+1):
            xx.append(lag)
            if lag>0:
                cc.append(((ts1[lag:]-ts1[lag:].mean())*(ts2[:-lag]-ts2[:-lag].mean())).sum())
            else:
                cc.append(((ts1-ts1.mean(axis=0))*(ts2-ts2.mean(axis=0))).sum())
        cc,xx= np.asarray(cc), np.asarray(xx)
        cc= cc/np.sqrt(np.sum((ts1-ts1.mean(axis=0))**2))/np.sqrt(np.sum((ts2-ts2.mean(axis=0))**2))
        return cc,xx

    ###-----------------------
    N= len(ts1)
    ### Case1: Considering one timeseries
    ### if is_ts1_AR1==True:
    ###    Neff= N*(1-r)/(1+r) if r>0 else N, by assuming ts1 as AR1
    ### else:
    ###    Neff= N/(1+2*sum((1-k/n)*r_k, k=1,n-1))
    ### where r= auto-correlation
    AR1_crt= 0.05
    if len(ts2)==0:
        ac1= acf(ts1)[0]  ## Calculate auto-correlation function
        if is_ts1_AR1:
            if ac1[1]>=AR1_crt and adjust_AR1:
                ## Fitting ts1 to AR1
                ac0= []
                for k in range(1,min(25,N-1),1):
                    if ac1[k]<AR1_crt:
                        break
                    else:
                        ac0.append(ac1[k]**(1/k))
                r= np.array(ac0).mean()
            else:
                r= ac1[1]
            Neff= N*(1-r)/(1+r) if r>0 else N
        else:
            ac1,M= Tukey_window(ac1)
            vsum=0
            for k in range(M+1):
                vsum+= (1-k/N)*ac1[k]
            Neff= min(N,N/(1+2*vsum))

    ### Case2: Considering two timeseries
    ### Var(r)= (1-r**2)**2/Neff  (assuming ts1 ans ts2 both white but correlated)
    ### Also, Var(r)= complex formula in Afyouni et al. 2019
    ### Hence, Neff= (1-r**2)**2 / complex_formula
    else:
        ac1, ac2= acf(ts1)[0], acf(ts2)[0]
        cc1, cc2= ccf(ts1,ts2)[0], ccf(ts2,ts1)[0]
        r= cc1[0]
        ## Apply Tukey window to ac and cc
        ac1,M= Tukey_window(ac1)
        ac2,cc1,cc2= Tukey_window(ac2)[0],Tukey_window(cc1)[0],Tukey_window(cc2)[0]

        ##-- Calculate Var(r)
        vsum1,vsum2,vsum3= 0,0,0
        for k in range(1,M+1):
            vsum1+= (N-2-k)*(ac1[k]**2+ac2[k]**2+cc1[k]**2+cc2[k]**2)
            vsum2+= (N-2-k)*(ac1[k]+ac2[k])*(cc1[k]+cc2[k])
            vsum3+= (N-2-k)*(ac1[k]*ac2[k]+cc1[k]*cc2[k])
        var_r= ((N-2)*(1-r**2)**2 + r**2*vsum1 - 2*r*vsum2 + 2*vsum3)/N**2
        #print(var_r, (1-r**2)**2,vsum1,vsum2,vsum3)
        #print(np.round(ac1[:5],3),np.round(ac2[:5],3))
        #print(np.round(cc1[:5],3),np.round(cc2[:5],3))
        Neff= (1-r**2)**2/var_r
        if Neff>N: Neff=N
    print("Dependency_level= ",N/Neff)
    return Neff

def regression_stat(x,y,sl,intercept,new_x,pct_range=[5,95],Neff=0):
    """
    Calculate the range of slope and regression mean
    based on given percent range.
    If get_Neff=True, adjust DOF by dependency_level
    """
    ### Neff
    n= len(x)
    if Neff<=0:
        Neff=n
    ### Standard error of mean
    SE= np.sqrt(np.sum((y-sl*x-intercept)**2,axis=0) / (Neff-2))/np.sqrt(Neff)
    t_ppf= st.t.ppf([val/100 for val in pct_range],Neff-2)
    ## Range of slope
    SE_sl= SE/np.std(x)*t_ppf
    ## Range of regression mean
    SE_y= [SE*np.sqrt(1+(new_x-x.mean())**2/np.var(x))*tf for tf in t_ppf]
    return SE_sl, SE_y

from matplotlib.ticker import MultipleLocator, FixedLocator
def map_common(ax,subtit,data_crs,gl_lab_locator=[True,True,False,True],yloc=30,xloc=60,lon_range=[-180,179.9]):
    """ Decorating Cartopy Map
    """
    ### Title
    ax.set_title(subtit,fontsize=13,ha='left',x=0.0)
    ### Coast Lines
    ax.coastlines(color='0.5',linewidth=1.)
    ### Grid Lines
    prop_gl= dict(linewidth=0.8, color='gray', alpha=0.7, linestyle='--')
    import cartopy
    cartopy_version= float(cartopy.__version__[:4])
    if cartopy_version < 0.18:
        print("Cartopy Version= {}".format(cartopy_version))
        print("Caution: This code is optimized for Cartopy version 0.18+")
        ax.gridlines(crs=data_crs, **prop_gl)
    else:
        gl=ax.gridlines(crs=data_crs,draw_labels=True,**prop_gl)
        gl.left_labels,gl.right_labels,gl.top_labels,gl.bottom_labels= gl_lab_locator

    gl.xlabel_style = {'size': 10}
    gl.ylabel_style = {'size': 10}
    gl.xlocator = MultipleLocator(xloc)
    gl.ylocator = MultipleLocator(yloc)
    ### Aspect ratio of map
    #ax.set_aspect('auto') ### 'auto' allows the map to be distorted and fill the defined axes
    return

def draw_colorbar(fig,ax,pic1,type='vertical',size='panel',gap=0.06,width=0.02,extend='neither'):
    '''
    Type: 'horizontal' or 'vertical'
    Size: 'page' or 'panel'
    Gap: gap between panel(axis) and colorbar
    Extend: 'both', 'min', 'max', 'neither'
    '''
    pos1=ax.get_position().bounds  ##<= (left,bottom,width,height)
    if type.lower()=='vertical' and size.lower()=='page':
        cb_ax =fig.add_axes([pos1[0]+pos1[2]+gap,0.1,width,0.8])  ##<= (left,bottom,width,height)
    elif type.lower()=='vertical' and size.lower()=='panel':
        cb_ax =fig.add_axes([pos1[0]+pos1[2]+gap,pos1[1],width,pos1[3]])  ##<= (left,bottom,width,height)
    elif type.lower()=='horizontal' and size.lower()=='page':
        cb_ax =fig.add_axes([0.1,pos1[1]-gap,0.8,width])  ##<= (left,bottom,width,height)
    elif type.lower()=='horizontal' and size.lower()=='panel':
        cb_ax =fig.add_axes([pos1[0],pos1[1]-gap,pos1[2],width])  ##<= (left,bottom,width,height)
    else:
        print('Error: Options are incorrect:',type,size)
        return

    cbar=fig.colorbar(pic1,cax=cb_ax,extend=extend,orientation=type)  #,ticks=[0.01,0.1,1],format='%.2f')
    cbar.ax.tick_params(labelsize=10)
    return cbar

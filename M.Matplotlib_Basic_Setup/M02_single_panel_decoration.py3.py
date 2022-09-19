'''
Matplotlib Basic(2)
: Change property of line plot
: Control x and y axis ticks
: Add title and axis labels

by Daeho Jin

---
Reference:
https://matplotlib.org/stable/api/axes_api.html
'''

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, MultipleLocator, FuncFormatter

###--- Synthesizing data to be plotted ---###
x = np.arange(5)
y = x**2

#for x1,y1 in zip(x,y):
#    print(x1,y1)
###---


###--- Plotting Start ---###

##-- Page Setup --##
fig = plt.figure()
fig.set_size_inches(4.5,6)    # Physical page size in inches, (lx,ly)

fig.subplots_adjust(left=0.08,right=0.97,top=0.92,bottom=0.05) #,hspace=0.2,wspace=0.15)  ### Margins, etc.

##-- Title for the page --##
suptit="Single Panel Setting"
fig.suptitle(suptit,fontsize=15)  #,ha='left',x=0.,y=0.98,stretch='semi-condensed')

##-- Set up axes1 --##
ax1 = fig.add_subplot(1,1,1)   # (# of rows, # of columns, indicater from 1)

##-- Plot on an axes --##
props= dict(color='r',ls='-.',lw=1.5,marker='o',markersize=20)  # ls: line_style, lw: line_width
ax1.plot(x,y,**props)  # https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.plot.html

##-- Various Settings for axes --##
subtit='Panel#1'
ax1.set_title(subtit,fontsize=12,x=0.,ha='left') #,y=0.9

ax1.set_xlim(-0.5,4.5)
ax1.xaxis.set_major_locator(MultipleLocator(1))   # For Major Ticks
ax1.xaxis.set_minor_locator(AutoMinorLocator(2))   # For minor Ticks
# https://matplotlib.org/stable/gallery/ticks/tick-locators.html
ax1.set_xlabel('X-axis Label',fontsize=12)

ax1.set_ylim(-1,17)
ax1.set_ylabel('Y-axis Label',fontsize=12,rotation=90,labelpad=0)
ax1.set_yticks(range(0,17,4))  # Manually set tick locations replacing 'locator'
ax1.yaxis.set_minor_locator(AutoMinorLocator(2))
ax1.yaxis.set_major_formatter("[{x:0.1f}+]")  # Working on ver 3.3+
#ax1.yaxis.set_major_formatter(lambda x, pos: "[{:0.1f}+]".format(x))  # Working on ver 3.4+
#yt_form=FuncFormatter(lambda x, pos: "[{:0.1f}+]".format(x))
#ax1.yaxis.set_major_formatter(yt_form)
# https://matplotlib.org/stable/gallery/ticks/tick-formatters.html
ax1.yaxis.set_ticks_position('both')

ax1.tick_params(axis='both',labelsize=11)
# https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.tick_params.html

ax1.axhline(y=0.,color='k',linestyle=':')
ax1.axvline(x=0.,color='k',ls=':',lw=0.5)

##-- Seeing or Saving Pic --##

#- If want to save to file
outdir = "../Pics/"
outfnm = outdir+"M02_single_panel2.png"
print(outfnm)
#fig.savefig(outfnm,dpi=100)   # dpi: pixels per inch
#fig.savefig(outfnm,dpi=100,facecolor='0.8')
#fig.savefig(outfnm,dpi=100,facecolor='0.8',transparent=True)
fig.savefig(outfnm,dpi=100,bbox_inches='tight')   # dpi: pixels per inch
# Defalut: facecolor='w', edgecolor='w', transparent=False

#- If want to see on screen -#
plt.show()

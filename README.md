# FRED-GenCumSky

To generate the GenCumSky for the desired location, bifacial_radiance github must be installed (www.github.com/NREL/bifacial_radiance),

At some point I'll streamline the process but, so far:

1 - Run bifacial_radiance modified script to generate GenCumSky for each hour (it generates basically one cumulative_X.cal (X: 1 to 8760) file for each hour, total of 8760 files)

2 -Run matlab script to read and change all 8760 cumulative_X.cal to one big excel file.

3 -Run SMARTS (through matlab) to generate one huge excel with all the direct spectra for each TMY3 hour with routine.
   -Run SMARTS (through matlab) to generate one huge excel with all the diffuse spectra 
  ** SMARTS-Matlab is not yet available for public. To get SMARTS spectra follow the instructions available on https://www.nrel.gov/grid/solar-resource/smarts.html
  
4 -Run creative_cumulative_spectra.py file to calculate accumulated spectra for each patch, using as input files from 2 and 3. An example of the output spectra for Tucson is available in this github, in "data/" folder.


FRED:
GenCumSky_Function calls for an address where the values for the sky patches are stored. It expects 147 values: 145 for the patches, and then the minimum and maximum values of the array to color the patches.


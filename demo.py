'''
demo.py
Spring 2026 PJW

Carry out a risk assessment measuring the benefits
from reducing PM2.5 exposure in New York City.
'''

import tomllib
import rasterio
import geopandas as gpd
import pandas as pd
from rasterstats import zonal_stats
from ratools import raster_info
import matplotlib.pyplot as plt
import seaborn as sns
import os

plt.rcParams['figure.dpi'] = 300

#
#  Input files
#
#    setup file = key settings and parameters
#    bg file    = boundaries of block groups
#    pop data   = population data from the Census
#    risk file  = baseline risk from the CDC
#

setup_file = 'setup.toml'
bg_file = 'cb_2024_36_bg_500k.zip'
pop_data = 'pop_by_bg.csv'
risk_file = 'baseline_risk.csv'

#
#  Read the setup file
#

with open(setup_file,'rb') as fh:
    setup = tomllib.load(fh)
    airdata = setup['air_data']
    crf_hr = setup['hazard_ratio']
    nyc_fips = setup['counties']
    vsl = setup['vsl']

#
#  Read the block group shape file and filter to NYC.
#  Reset the index to sequential integers to facilitate
#  joining on zonal statistics later.
#

bgs = gpd.read_file(bg_file)
bgs = bgs[ bgs['COUNTYFP'].isin(nyc_fips) ]
bgs = bgs.reset_index(drop=True)

#%%
#
#  Walk through the air quality data files and compute
#  block group zonal statistics for each one.
#

bgdata = {}

for year,airfile in airdata.items():

    print('Year',year,flush=True)

    #
    #  See if we've already done this on a previous run
    #  If so, read the pickle file and go on to the next year
    #

    pickle_file = f'pm{year}.pkl'
    if os.path.exists(pickle_file):
        print('Reading existing file',pickle_file)
        bgplus = pd.read_pickle(pickle_file)
        bgdata[year] = bgplus
        continue

    #
    #  Read the raster, print out its metadata, and
    #  grab its CRS
    #

    ras = rasterio.open(airfile)
    raster_info(ras)
    crs = ras.crs
    ras.close()

    #
    #  Reproject the block groups to the raster's CRS
    #

    bgplus = bgs.to_crs(crs)

    #
    # Compute air quality for each block group. Use the
    # all_touched parameter because some block groups are
    # small relative to the grid cells. Without it, only
    # cells whose centers are in the block group are used
    # for the statistics.
    #

    print(f'\nComputing {year} statistics...',end='',flush=True)

    stats = zonal_stats(bgplus,airfile,all_touched=True)

    print('done',flush=True)

    #
    #  Turn the stats into a dataframe and join them onto
    #  the GEOID column from the block group file
    #

    stats = pd.DataFrame(stats)

    bgplus = bgplus[['GEOID']].join(stats)
    bgplus = bgplus.set_index('GEOID')

    #
    #  Write out a pickle file in case we need to rerun
    #

    bgplus.to_pickle(pickle_file)
    print('Wrote',pickle_file)

    #
    #  Add the dataframe to the list
    #

    bgdata[year] = bgplus

#%%
#
#  Concatenate the data for different years
#

bgs_all = pd.concat(bgdata)
bgs_all.index = bgs_all.index.set_names('year',level=0)

#%%
#
#  Draw histograms of the before and after concentrations to
#  see if there's much difference.
#

fig,ax = plt.subplots()
fig.suptitle('Distribution of Block Groups by PM2.5 Concentration')
sns.histplot(bgs_all,x='mean',hue='year',ax=ax)
fig.tight_layout()

#%%
#
#  Unstack the year and calculate how much larger PM
#  concentrations were in 2009. Effectively, we'll compute
#  increased mortality if air quality went backwards.
#

byyear = bgs_all['mean'].unstack('year')
byyear['change'] = byyear['2009'] - byyear['2024']

#
#  Draw a scatterplot comparing the years
#

fig,ax = plt.subplots()

fig.suptitle('PM2.5 Concentration, 2009 and 2024')

sns.scatterplot(byyear,x='2009',y='2024',ax=ax)

ax.axline((5,5),slope=1,color='red')

ax.annotate('2024=2009',
            xy=(9,9),           # tip of arrow
            xytext=(6,10),      # start of text
            arrowprops={        # features of arrow
                'width':0.5,
                'headwidth':10,
                'color':'red'
                }
            )

fig.tight_layout()

#%%
#
#  Map the changes
#

change_by_bg = bgs.set_index('GEOID')[['geometry']]
change_by_bg['change'] = byyear['change']
fig,ax = plt.subplots()
fig.suptitle('2009 Elevation in PM2.5 vs 2024')
change_by_bg.plot('change',legend=True,ax=ax)
ax.axis('off')

#%%
#
#  Read baseline risk by race, drop covid years, and convert
#  from per 100,000 to individual risk.
#

by_race_risk = pd.read_csv(risk_file,index_col='Race')
by_race_risk = by_race_risk[ by_race_risk['Covid']==False ]
by_race_risk = by_race_risk['Age Adjusted Rate']/100e3

print('Baseline risk by race:')
print(by_race_risk)

#
#  Now expand to a dataframe with baseline risk by block group
#

geoids = byyear.index

bg_risk_baseline = pd.DataFrame( index=geoids )

for race,base_rate in by_race_risk.items():
    bg_risk_baseline[race] = base_rate

print('Check rates:')
print(bg_risk_baseline.mean())

#%%
#
#  Now calculate the rate for a 10 ug/m3 increase, which
#  is the change used to define the CRF beta. Will be the
#  same across block groups. Will differ across races since
#  the baseline risks differed.
#

bg_risk_10ug = bg_risk_baseline * crf_hr

print('Elevated risk, 10 ug/m3:')
print(bg_risk_10ug.mean())

#
#  Excess risk due to a 10 ug increase
#

bg_excess_10ug = bg_risk_10ug - bg_risk_baseline

#%%
#
#  Now calculate excess risk for actual changes in PM by
#  block group. Concentration data is ug/m3 so divide by
#  ten before multiplying. Result will differ by race and
#  block group.
#

pm_change = byyear['change']

bg_excess_act = bg_excess_10ug.mul( pm_change/10, axis='index' )

#
#  Plot a histogram with increased rates per 100k
#

stack = bg_excess_act.melt(var_name='Race',value_name='Risk')

stack['Risk'] = stack['Risk']*100e3

fig,ax = plt.subplots()
fig.suptitle('Increased Risk per 100,000')
sns.histplot(stack,x='Risk',hue='Race',ax=ax)
fig.tight_layout()

#%%
#
#  Now get the population, drop "OTH" which is small and
#  doesn't have a baseline risk, and set the index to the
#  block group's GEOID
#

pop = pd.read_csv(pop_data,dtype={'GEOID':str})
pop = pop.drop(columns='OTH')
pop = pop.set_index('GEOID')

#
#  Calculate the excess mortality by multiplying the excess
#  risk by block group by the block group's population.
#

excess_mort = bg_excess_act*pop
excess_mort['Total'] = excess_mort.sum(axis='columns')

#
#  Total excess mortality by race if we went back to 2009,
#  or the expected lives saved by the reduction in pollution.
#

excess_mort_by_race = excess_mort.sum()

print('\nExcess fatalites by race:')
print(excess_mort_by_race.round(2))

#
#  Benefits valued at the VSL
#

tot_excess = excess_mort_by_race['Total']
tot_cost_m = tot_excess*vsl/1e6

print('\nTotal cost:')
print(f'{round(tot_cost_m,2):,} M')

#%%
#
#  Map excess mortality by block group for all races
#

merged = bgs.set_index('GEOID')[['geometry']]
merged = merged.join(excess_mort)

fig,ax = plt.subplots()
fig.suptitle('Excess Mortality, All Races')
merged.plot('Total',legend=True,ax=ax)
ax.axis('off')

#%%
#
#  Summarize fatalities avoided by race with the racial
#  composition of the city. Compute shares in total
#  fatalities avoided and compare that with shares in
#  in the total population and the population-weighted
#  change in air quality.
#

excess_mort_pct = 100*excess_mort_by_race/tot_excess

pop_by_race = pop.sum()
pop_by_race['Total'] = pop_by_race.sum()
pop_pct = 100*pop_by_race/pop_by_race['Total']

weighted_change = pop.mul(change_by_bg['change'],axis='index')
weighted_change = weighted_change.sum()/pop.sum()

print('\nPopulation weighted change in PM')
print(weighted_change.round(2))

summary = pd.DataFrame()
summary['% pop'] = pop_pct
summary['% avoided'] = excess_mort_pct
summary['PM chg'] = weighted_change
summary['Base/100k'] = 100e3*by_race_risk
summary['RR/100k'] = 100e3*excess_mort_by_race/pop.sum()
summary = summary.round(2)

print('\nOverall Impacts by Race:')
print(summary)

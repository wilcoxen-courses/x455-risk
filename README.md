# Example: Risk Assessment for PM in NYC

## Summary

The **demo.py** file in this repository carries out an assessment of the impact of fine particulate matter (PM2.5) air pollution in New York City between 2009 and 2024.

## Input Data

There are five input files, all of which are provided in the repository: **cb_2024_36_bg_500k.zip**, the cartographic boundary file for block groups in New York State; **aa01_pm300m-2009.tif** and **aa16_pm300m-2024.tif**, raster files giving the ambient level of PM2.5 pollution in New York City in 2009 and 2024; **baseline_risk.csv**, baseline mortality risk, by race, from the CDC WONDER database; and **setup.toml**, a configuration file read by the script. In addition, a short module, **ratools.py**, is provided with a function for printing information about a raster.

## Deliverables

**None**. This is an example only and there's **nothing due**.

## Instructions

1. Look over the demo script to see how it works, and then try running it.

1. Try changing changing some of the parameters to see how the results change. For example, you could switch the baseline mortality rates to those of the Covid years.

## Tips

1. The baseline risks, the hazard ratio associated with PM are estimates, and the VSL are all estimates and have confidence intervals. The bounds for the baseline risks are included in baseline_risk.csv and those for the hazard ratio are about [1.05, 1.07]. For the VSL, a meta-analysis by the EPA found that empirical estimates follow a Weibull distribution that in 2024 dolllars has a mean of 11 M and a 95% confidence interval of [680k, 27.5M]. A complete analysis could use these bounds to compute lower and upper limits for the mortality and overall benefit, or a Monte Carlo analysis could be carried out to compute the full distributions.

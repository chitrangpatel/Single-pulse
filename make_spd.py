#!/usr/bin/env python

"""
sp_pipeline.py

Make single pulse plots which include the waterfall plots and dedispersed time series with Zero-DM On/Off.
Also includes Signal-to-noise vs DM and DM vs Time subplots.
Usage on the command line:
./sp_pipeline.py --infile <any .inf file> --groupsfile <a groups.txt file> --mask <.rfifind.mask file> <psrfits file> <singlepulse files>

Chitrang Patel - May. 21, 2015
"""

import sys
import copy
from time import strftime
import infodata
from subprocess import Popen, PIPE

import numpy as np
import optparse
import waterfaller
import sp_utils
import bary_and_topo
import psr_utils
import rfifind
import plot_spd
import spcand

from sp_pulsar.formats import psrfits
from sp_pulsar.formats import spectra

DEBUG = True
def print_debug(msg):
    if DEBUG:
        print msg

def waterfall_array(rawdatafile, start, duration, dm, nbins, nsub, subdm, zerodm, \
                    downsamp, scaleindep, width_bins, mask, maskfn, bandpass_corr):
    """
    Runs the waterfaller. If dedispersing, there will be extra bins added to the 2D plot.
    Inputs:
        Inputs required for the waterfaller. dm, nbins, etc. 
    Outputs:
       data: 2D array as an "object" 
       array: 2D array ready to be plotted by sp_pgplot.plot_waterfall(array). 
    """
    data, bins, nbins, start = waterfaller.waterfall(rawdatafile, start, duration, dm=dm, nbins=nbins, \
                                                     nsub=nsub, subdm=subdm, zerodm=zerodm, \
                                                     downsamp=downsamp, scaleindep=scaleindep, \
                                                     width_bins=width_bins, mask=mask, \
                                                     maskfn=maskfn, bandpass_corr=bandpass_corr)
    array = np.array(data.data)
    if dm is not None:            # If dedispersing the data, extra bins will be added. We need to cut off the extra bins to get back the appropriate window size.   
        ragfac = float(nbins)/bins
        dmrange, trange = array.shape
        nbinlim = np.int(trange * ragfac)
    else:
        nbinlim = nbins
    array = array[..., :nbinlim]
    array = (array[::-1]).astype(np.float16)
    return data, array

def make_spd_from_file(spdcand, rawdatafile, \
                       inffile, txtfile, maskfile, \
                       min_rank, \
                       plot, just_waterfall, \
                       integrate_ts, integrate_spec, \
                       maxnumcands, \
                       basename, \
                       mask=False, bandpass_corr=True, man_params=None):
    
    numcands=0 # counter for max number of candidates
    loop_must_break = False # dont break the loop unless num of cands >100.
    inf = infodata.infodata(inffile)
    files = sp_utils.spio.get_textfile(options.txtfile)
    groups = [i for i in range(7) if(i>=min_rank)]
     
    for group in groups:
        rank = group+1
        if files[group] != "Number of rank %i groups: 0 "%rank:
            print_debug(files[group])
            values = sp_utils.spio.split_parameters(rank, txtfile)
            lis = np.where(files == '\tRank:             %i.000000'%rank)[0]
            for ii in range(len(values)):
                #### Arrays for Plotting DM vs SNR
                dm_list, time_list, dm_arr, sigma_arr, width_arr = sp_utils.spio.read_RRATrap_info(txtfile, lis, rank)


                # Array for Plotting Dedispersed waterfall plot - zerodm - OFF
                spdcand.read_from_file(values[ii], rawdatafile.tsamp, inf.N, rawdatafile.frequencies[0], \
                                       rawdatafile.frequencies[-1], inffile, dedisp = True, \
                                       scaleindep = None, zerodm = None, mask = mask, \
                                       bandpass_corr = bandpass_corr)

                #make an array to store header information for the spd files
                temp_filename = basename+"_DM%.1f_%.1fs_rank_%i"%(spdcand.subdm, \
                                                   spdcand.topo_start_time, rank)
                
                print_debug("Running waterfaller with Zero-DM OFF...")
                
                # Add additional information to the header information array
                data, Data_dedisp_nozerodm = waterfall_array(rawdatafile, spdcand.start, \
                                             spdcand.duration, spdcand.dm, spdcand.nbins, spdcand.nsub, \
                                             spdcand.subdm, spdcand.zerodm, spdcand.downsamp, \
                                             spdcand.scaleindep, spdcand.width_bins, \
                                             spdcand.mask, maskfile, spdcand.bandpass_corr)

                text_array = np.array([args[0], inf.telescope, inf.RA, inf.DEC, inf.epoch, \
                                       rank, spdcand.nsub, spdcand.nbins, spdcand.subdm, \
                                       spdcand.sigma, spdcand.sample_number, spdcand.duration, \
                                       spdcand.width_bins, spdcand.pulse_width, rawdatafile.tsamp,\
                                       Total_observed_time, spdcand.topo_start_time, data.starttime, \
                                       data.dt,data.numspectra, data.freqs.min(), data.freqs.max()])

                #### Array for plotting Dedispersed waterfall plot zerodm - ON
                print_debug("Running Waterfaller with Zero-DM ON...")
                zerodm=True
                data, Data_dedisp_zerodm = waterfall_array(rawdatafile, spdcand.start, \
                                           spdcand.duration, spdcand.dm, spdcand.nbins, spdcand.nsub, \
                                           spdcand.subdm, zerodm, spdcand.downsamp, \
                                           spdcand.scaleindep, spdcand.width_bins, \
                                           spdcand.mask, maskfile, spdcand.bandpass_corr)
                ####Sweeped without zerodm
                spdcand.read_from_file(values[ii], rawdatafile.tsamp, inf.N, rawdatafile.frequencies[0], \
                                      rawdatafile.frequencies[-1], inffile, dedisp = None, \
                                      scaleindep = None, zerodm = None, mask = mask, \
                                      bandpass_corr = bandpass_corr)
                data, Data_nozerodm = waterfall_array(rawdatafile, spdcand.start, \
                                           spdcand.duration, spdcand.dm, spdcand.nbins, spdcand.nsub, \
                                           spdcand.subdm, spdcand.zerodm, spdcand.downsamp, \
                                           spdcand.scaleindep, spdcand.width_bins, \
                                           spdcand.mask, maskfile, spdcand.bandpass_corr)
                text_array = np.append(text_array, spdcand.sweep_duration)
                text_array = np.append(text_array, data.starttime)
                text_array = np.append(text_array, spdcand.bary_start_time)
                text_array = np.append(text_array, man_params)
                # Array to Construct the sweep
                if spdcand.sweep_dm is not None:
                    ddm = spdcand.sweep_dm-data.dm
                    delays = psr_utils.delay_from_DM(ddm, data.freqs)
                    delays -= delays.min()
                    delays_nozerodm = delays
                    freqs_nozerodm = data.freqs
                # Sweeped with zerodm-on 
                zerodm = True
                #downsamp_temp = 1
                data, Data_zerodm = waterfall_array(rawdatafile, spdcand.start, \
                                           spdcand.duration, spdcand.dm, spdcand.nbins, spdcand.nsub, \
                                           spdcand.subdm, zerodm, spdcand.downsamp, \
                                           spdcand.scaleindep, spdcand.width_bins, \
                                           spdcand.mask, maskfile, spdcand.bandpass_corr)
                # Saving the arrays into the .spd file.
                with open(temp_filename+".spd", 'wb') as f:
                    np.savez_compressed(f, \
                                        Data_dedisp_nozerodm = Data_dedisp_nozerodm.astype(np.float16),\
                                        Data_dedisp_zerodm = Data_dedisp_zerodm.astype(np.float16),\
                                        Data_nozerodm = Data_nozerodm.astype(np.float16),\
                                        delays_nozerodm = delays_nozerodm, \
                                        freqs_nozerodm = freqs_nozerodm,\
                                        Data_zerodm = Data_zerodm.astype(np.float16), \
                                        dm_arr= map(np.float16, dm_arr),\
                                        sigma_arr = map(np.float16, sigma_arr), \
                                        width_arr =map(np.int8, width_arr),\
                                        dm_list= map(np.float16, dm_list), \
                                        time_list = map(np.float16, time_list), \
                                        text_array = text_array)
                #### Arrays for Plotting DM vs Time is in plot_spd.plot(...)
                if plot:
                    print_debug("Now plotting...")
                    plot_spd.plot(temp_filename+".spd", args[1:], \
                                  just_waterfall, xwin=False, \
                                  outfile = basename, tar = None)
                    print_debug("Finished plot %i " %j+strftime("%Y-%m-%d %H:%M:%S"))
                numcands+= 1
                print_debug('Finished sp_candidate : %i'%numcands)
                if numcands >= maxnumcands:    # Max number of candidates to plot 100.
                    loop_must_break = True
                    break
            if loop_must_break:
                break

        print_debug("Finished group %i... "%rank+strftime("%Y-%m-%d %H:%M:%S"))
    print_debug("Finished running waterfaller... "+strftime("%Y-%m-%d %H:%M:%S"))
        
def make_spd_from_man_params(spdcand, rawdatafile, \
                             inffile, txtfile, maskfile, \
                             plot, just_waterfall, \
                             subdm, dm, sweep_dm, \
                             sigma, \
                             start_time, duration, \
                             width_bins, nbins, downsamp, \
                             nsub, \
                             scaleindep, \
                             integrate_ts, integrate_spec, \
                             basename, \
                             mask, bandpass_corr, man_params):            
    rank = None
    inf = infodata.infodata(inffile)
    # Array for Plotting Dedispersed waterfall plot - zerodm - OFF
    spdcand.manual_params(subdm, dm, sweep_dm, sigma, start_time, \
                         width_bins, downsamp, duration, nbins, nsub, rawdatafile.tsamp, inf.N, \
                         rawdatafile.frequencies[0], rawdatafile.frequencies[-1], inffile, \
                         dedisp=True, scaleindep=False, zerodm=False, \
                         mask=mask, bandpass_corr=bandpass_corr)
    #make an array to store header information for the spd files
    temp_filename = basename+"_DM%.1f_%.1fs"%(spdcand.subdm, spdcand.topo_start_time)
           
    print_debug("Running waterfaller with Zero-DM OFF...")
    data, Data_dedisp_nozerodm = waterfall_array(rawdatafile, spdcand.start, \
                                 spdcand.duration, spdcand.dm, spdcand.nbins, spdcand.nsub, \
                                 spdcand.subdm, spdcand.zerodm, spdcand.downsamp, \
                                 spdcand.scaleindep, spdcand.width_bins, \
                                 spdcand.mask, maskfile, spdcand.bandpass_corr)
    # Add additional information to the header information array
    text_array = np.array([args[0], inf.telescope, inf.RA, inf.DEC, inf.epoch, rank, \
                           spdcand.nsub, spdcand.nbins, \
                           spdcand.subdm, spdcand.sigma, spdcand.sample_number, \
                           spdcand.duration, spdcand.width_bins, spdcand.pulse_width, \
                           rawdatafile.tsamp, Total_observed_time, spdcand.topo_start_time, \
                           data.starttime, data.dt,data.numspectra, data.freqs.min(), \
                           data.freqs.max()])

    #### Array for plotting Dedispersed waterfall plot zerodm - ON
    print_debug("Running Waterfaller with Zero-DM ON...")
    zerodm=True
    data, Data_dedisp_zerodm = waterfall_array(rawdatafile, spdcand.start, \
                                 spdcand.duration, spdcand.dm, spdcand.nbins, spdcand.nsub, \
                                 spdcand.subdm, zerodm, spdcand.downsamp, \
                                 spdcand.scaleindep, spdcand.width_bins, \
                                 spdcand.mask, maskfile, spdcand.bandpass_corr)
    ####Sweeped without zerodm
    spdcand.manual_params(subdm, dm, sweep_dm, sigma, start_time, \
                          width_bins, downsamp, duration, nbins, nsub, rawdatafile.tsamp, inf.N, \
                          rawdatafile.frequencies[0], rawdatafile.frequencies[-1], inffile, \
                          dedisp=None, scaleindep=None, zerodm=None, mask=mask, \
                          bandpass_corr=bandpass_corr)
    data, Data_nozerodm = waterfall_array(rawdatafile, spdcand.start, \
                                 spdcand.duration, spdcand.dm, spdcand.nbins, spdcand.nsub, \
                                 spdcand.subdm, spdcand.zerodm, spdcand.downsamp, \
                                 spdcand.scaleindep, spdcand.width_bins, \
                                 spdcand.mask, maskfile, spdcand.bandpass_corr)
    text_array = np.append(text_array, spdcand.sweep_duration)
    text_array = np.append(text_array, data.starttime)
    text_array = np.append(text_array, spdcand.bary_start_time)
    text_array = np.append(text_array, man_params)
    # Array to Construct the sweep
    if spdcand.sweep_dm is not None:
        ddm = spdcand.sweep_dm-data.dm
        delays = psr_utils.delay_from_DM(ddm, data.freqs)
        delays -= delays.min()
        delays_nozerodm = delays
        freqs_nozerodm = data.freqs
    # Sweeped with zerodm-on 
    zerodm = True
    #downsamp_temp = 1
    data, Data_zerodm = waterfall_array(rawdatafile, spdcand.start, \
                                 spdcand.duration, spdcand.dm, spdcand.nbins, spdcand.nsub, \
                                 spdcand.subdm, zerodm, spdcand.downsamp, \
                                 spdcand.scaleindep, spdcand.width_bins, \
                                 spdcand.mask, maskfile, spdcand.bandpass_corr)
    with open(temp_filename+".spd", 'wb') as f:
        np.savez_compressed(f, \
                            Data_dedisp_nozerodm = Data_dedisp_nozerodm.astype(np.float16),\
                            Data_dedisp_zerodm = Data_dedisp_zerodm.astype(np.float16),\
                            Data_nozerodm = Data_nozerodm.astype(np.float16),\
                            delays_nozerodm = delays_nozerodm, \
                            freqs_nozerodm = freqs_nozerodm,\
                            Data_zerodm = Data_zerodm.astype(np.float16), \
                            text_array = text_array)
    #### Arrays for Plotting DM vs Time is in plot_spd.plot(...)
    if plot:
        print_debug("Now plotting...")
        plot_spd.plot(temp_filename+".spd", args[1:], just_waterfall, \
        xwin=False, outfile = basename, tar = None)

def main():
    fn = args[0]
    if fn.endswith(".fil"):
        # Filterbank file
        filetype = "filterbank"
        print_debug("Reading filterbank file..")
        rawdatafile = filterbank.filterbank(fn)
        basename = fn[:-4]
    if fn.endswith(".fits"):
        # PSRFITS file
        filetype = "psrfits"
        print_debug("Reading PSRFITS file..")
        rawdatafile = psrfits.PsrfitsFile(fn)
        basename = fn[:-5]
    else:
        raise ValueError("Cannot recognize data file type from "
                         "extension. (Only '.fits' and '.fil' "
                         "are supported.)")

    spdcand = spcand.params
    if not options.man_params:
        print_debug('Maximum number of candidates to plot: %i'%options.maxnumcands)
        make_spd_from_file(spdcand, rawdatafile, \
                           options.infile, options.txtfile, options.maskfile, \
                           options.min_rank, \
                           options.plot, options.just_waterfall, \
                           options.integrate_ts, options.integrate_spec, \
                           options.maxnumcands, \
                           basename, \
                           mask=options.mask, bandpass_corr=options.bandpass_corr)
    else:
        print_debug("Making spd files based on mannual parameters. I suggest reading in parameters from the groups.txt file.")
        make_spd_from_man_params(spdcand, rawdatafile, \
                                 options.infile, options.txtfile, options.maskfile, \
                                 options.plot, options.just_waterfall, \
                                 options.subdm, options.dm, options.sweep_dm, \
                                 options.sigma, \
                                 options.start_time, options.duration, \
                                 options.width_bins, options.nbins, options.downsamp, \
                                 options.nsub, \
                                 options.scaleindep, \
                                 options.integrate_ts, options.integrate_spec, \
                                 basename, \
                                 options.mask, options.bandpass_corr, options.man_params)            

if __name__=='__main__':
    parser = optparse.OptionParser(prog="sp_pipeline..py", \
                        version=" Chitrang Patel (May. 12, 2015)", \
                        usage="%prog INFILE(PsrFits FILE, SINGLEPULSE FILES)", \
                        description="Create single pulse plots to show the " \
                                    "frequency sweeps of a single pulse,  " \
                                    "DM vs time, and SNR vs DM,"\
                                    "in psrFits data.")
    parser.add_option('--infile', dest='infile', type='string', \
                        help="Give a .inf file to read the appropriate header information.")
    parser.add_option('--groupsfile', dest='txtfile', type='string', \
                        help="Give the groups.txt file to read in the groups information.", \
                        default=None) 
    parser.add_option('--maskfile', dest='maskfile', type='string', \
                        help="Mask file produced by rfifind. Used for " \
                             "masking and bandpass correction.", \
                        default=None)
    parser.add_option('--mask', dest='mask', action="store_true", \
                        help="Mask data using rfifind mask (Default: Don't mask).", \
                        default=False)
    parser.add_option('--numcands', dest='maxnumcands', type='int', \
                        help="Maximum number of candidates to plot. (Default: 100).", \
                        default=100)
    parser.add_option('--subdm', dest='subdm', type='float', \
                        help="DM to use when subbanding. (Default: " \
                                "same as --dm)", default=None)
    parser.add_option('--zerodm', dest='zerodm', action='store_true', \
                        help="If this flag is set - Turn Zerodm filter - ON  (Default: " \
                                "OFF)", default=False)
    parser.add_option('-s', '--nsub', dest='nsub', type='int', \
                        help="Number of subbands to use. Must be a factor " \
                                "of number of channels. (Default: " \
                                "number of channels)", default=None)
    parser.add_option('--sigma', dest='sigma', type='float', \
                        help="Signal-to-Noise of the pulse." \
                             "(Default: Do not specify. You must specify the number ofsubbands.)", \
                        default=None)
    parser.add_option('-d', '--dm', dest='dm', type='float', \
                        help="DM to use when dedispersing data for plot. " \
                                "(Default: 0 pc/cm^3)", default=0.0)
    parser.add_option('--dont-show-ts', dest='integrate_ts', action='store_false', \
                        help="Do not plot the time series. " \
                                "(Default: Show the time series)", default=True)
    parser.add_option('--show-spec', dest='integrate_spec', action='store_true', \
                        help="Plot the spectrum. " \
                                "(Default: Do not show the spectrum)", default=False)
    parser.add_option('--bandpass', dest='bandpass_corr', action='store_true', \
                        help="Correct for the bandpass. Requires an rfifind " \
                                "mask provided by --mask option." \
                                "(Default: Do not remove bandpass)", default=False)
    parser.add_option('-T', '--start-time', dest='start', type='float', \
                        help="Time into observation (in seconds) at which " \
                                "to start plot.")
    parser.add_option('-t', '--duration', dest='duration', type='float', \
                        help="Duration (in seconds) of plot.")
    parser.add_option('-n', '--nbins', dest='nbins', type='int', \
                        help="Number of time bins to plot. This option takes " \
                                "precedence over -t/--duration if both are " \
                                "provided.")
    parser.add_option('--width-bins', dest='width_bins', type='int', \
                        help="Smooth each channel/subband with a boxcar " \
                                "this many bins wide. (Default: Don't smooth)", \
                        default=1)
    parser.add_option('--sweep-dm', dest='sweep_dms', type='float', \
                        action='append', \
                        help="Show the frequency sweep using this DM. " \
                                "(Default: Don't show sweep)", default=[])
    parser.add_option('--sweep-posn', dest='sweep_posns', type='float', \
                        action='append', \
                        help="Show the frequency sweep at this position. " \
                                "The position refers to the high-frequency " \
                                "edge of the plot. Also, the position should " \
                                "be a number between 0 and 1, where 0 is the " \
                                "left edge of the plot. "
                                "(Default: 0)", default=None)
    parser.add_option('--downsamp', dest='downsamp', type='int', \
                        help="Factor to downsample data by. (Default: 1).", \
                        default=1)
    parser.add_option('--scaleindep', dest='scaleindep', action='store_true', \
                        help="If this flag is set scale each channel " \
                                "independently. (Default: Scale using " \
                                "global maximum.)", \
                        default=False)
    parser.add_option('--min-rank', dest='min_rank', type='int',\
                       help="Min rank you want to make spd files for. (Default: 3)"\
                             "  Rank 1: noise,"\
                             "  Rank 2: RFI,"\
                             "  Rank 3: maybe astrophysical, very low S/N,"\
                             "  Rank 4: probably astrophysical but weak, low S/N,"\
                             "  Rank 5: Very high chance of being astrophysical. S/N>8.0,"\
                             "  Rank 6: Almost guranteed to be astrophysical. S/N>9.2,"\
                             "  Rank 7: Either bright astrophysical source or RFI.",\
                        default=3)
    parser.add_option('--use_manual_params', dest='man_params', action='store_true', \
                        help="If this flag is not set it will use the parameters " \
                                "from the RRATrap groups.txt file. "\
                                "(Default: Not use this flag. When using "\
                                "parameters from the output of rratrap. Just input"\
                                "the .inf file, groups.txt file, mask file, the PSRFITs file"\
                                "and the .singlepulse files as input. No need to specify any of"\
                                " the other arguments.)",\
                        default=False)
    parser.add_option('--noplot', dest='plot', action='store_false', \
                        help="Do not generate spd plots.", \
                        default=True)
    parser.add_option('--just-waterfall', dest='just_waterfall', action='store_true', \
                        help="Only produce the waterfall plots (frequency vs Time).", \
                        default=False)
    options, args = parser.parse_args()

    if not args[0].endswith("fits") or args[0].endswith("fil"):
        raise ValueError("The first file must be a psrFits or a filterbank file! ") 
    if (hasattr(options, 'bandpass_corr')) and (not hasattr(options, 'maskfile')):
        raise ValueError("For bandpass correction you need to supply a mask file.")
    if not hasattr(options, 'man_params'):
        if not hasattr(options, 'infile'):
            raise ValueError("A .inf file must be given on the command line! ") 
        if not hasattr(options, 'txtfile'):
            raise ValueError("The groups.txt file must be given on the command line! ") 
    else:
        if not hasattr(options, 'start'):
            raise ValueError("Start time (-T/--start-time) " \
                                "must be given on command line!")
        if (not hasattr(options, 'duration')) and (not hasattr(options, 'nbins')):
            raise ValueError("One of duration (-t/--duration) " \
                                "and num bins (-n/--nbins)" \
                                "must be given on command line!")
        if options.subdm is None:
            options.subdm = options.dm
    
    main()

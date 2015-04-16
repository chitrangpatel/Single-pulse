import numpy as np

class SPcand:
    """
    A class for reading in single pulse candidate files.

    A quick description of each item in the class:

     data_zerodm
        A 2D freq-vs-time array around the pulse, not dedispersed (zero-DM'd data)
     data_zerodm_dedisp
        A 2D freq-vs-time array around the pulse, dedispersed (zero-DM'd data)
     data_nozerodm
        A 2D freq-vs-time array around the pulse, not dedispersed (non-zero-DM'd data)
     data_nozerodm_dedisp
        A 2D freq-vs-time array around the pulse, dedispersed (non-zero-DM'd data)

     dmVt_dms
        DM values for the DM-vs-time scatterplot
     dmVt_times
        Time values for the DM-vs-time scatterplot
     dmVt_sigmas
        Sigma values (determining point size) for the DM-vs-time scatterplot

     dmsweep_delays
        Delays corresponding to frequencies for drawn-in dispersion sweep
     dmsweep_freqs
        Frequencies corresponding to delays for drawn-in dispersion sweep

     filename
        Name of the observation file that was analyzed     
     telescope
        Which telescope was used
     ra
        Right ascension as hh:mm:ss.s string
     dec
        Declination as dd:mm:ss.s string
     mjd
        Observation MJD
     total_obs_time
        Total duration of the observation this pulse was found in, in seconds
     rank
        Single pulse sifting rank
     tsamp
        Sampling time of raw data in seconds
     best_dm
        Best determined dispersion measure for this event
     sigma
        Significance of this event
     pulse_peak_sample
        The sample number in the full dedispersed time series at which this event peaked
     pulse_peak_time
        The time in seconds in the full dedispersed time series at which this event peaked
     pulsewidth_bins
        The width of the boxcar filter used to optimally detect this event, in number of bins
     pulsewidth_seconds
        The width of the boxcar filter used to optimally detect this event, in seconds
     waterfall_duration
        The total duration of the dedispersed waterfall plot
     waterfall_start_time
        The time (in seconds) in the full dedispersed time series at which the waterfall plot begins
     waterfall_tsamp
        Sampling time of the waterfall plot in seconds
     waterfall_nbins
        The number of samples across the dedispersed waterfall plot
     waterfall_nsubs
        The number of frequency bins across the waterfall plot
     waterfall_prededisp_nbins
        The number of samples prior to dedispersing and cutting off the ends of the waterfall plot
     min_freq
        The lowest frequency plotted
     max_freq
        The highest frequency plotted
     sweep_duration
        The total duration of the dispersed pulse across the band
     sweep_start_time
        The time at which to start plotting the dispersed reference line
    """
    def __init__(self, npz_file):
        dd = dict(np.load(npz_file))
        self.data_zerodm = dd['Data_zerodm']
        self.data_zerodm_dedisp = dd['Data_dedisp_zerodm']
        self.data_nozerodm = dd['Data_nozerodm']
        self.data_nozerodm_dedisp = dd['Data_dedisp_nozerodm']
         
        self.dmVt_dms = dd['dm_range']
        self.dmVt_times = dd['time_range']
        self.dmVt_sigmas = dd['sigma_range']

        self.dmVt_this_dms = dd['dm_arr']
        self.dmVt_this_times = np.array(dd['time_list'])
        self.dmVt_this_sigmas = dd['sigma_arr']

        self.dmsweep_delays = dd['delays_nozerodm']
        self.dmsweep_freqs = dd['freqs_nozerodm']

        ll = dd['text_array']
        self.filename = ll[0]
        self.telescope = ll[1]
        self.ra = ll[2]
        self.dec = ll[3]
        self.mjd = float(ll[4])
        self.total_obs_time = float(ll[15])
        self.rank = int(ll[5])
        self.tsamp = float(ll[14])
        self.best_dm = float(ll[8])
        self.sigma = float(ll[9])
        self.pulse_peak_sample = int(ll[10])
        self.pulse_peak_time = float(ll[16])
        self.pulsewidth_bins = int(ll[12])
        self.pulsewidth_seconds = float(ll[13])
        self.waterfall_duration = float(ll[11])
        self.waterfall_start_time = float(ll[17])
        self.waterfall_tsamp = float(ll[18])
        self.waterfall_nbins = int(ll[7])
        self.waterfall_nsubs = int(ll[6])
        self.waterfall_prededisp_nbins = int(ll[19])
        self.min_freq = float(ll[20])
        self.max_freq = float(ll[21])
        self.sweep_duration = float(ll[22])
        self.sweep_start_time = float(ll[23])



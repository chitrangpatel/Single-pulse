import numpy as np

class spd:
    """
    A class for reading in single pulse files.

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
     ra_deg
        Right ascension in degrees
     dec_deg
        Declination in degrees
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
     nsamp
        The number of original time series samples included in the (possibly downsampled) waterfall plot
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
        self.ra_deg = np.sum(np.array(self.ra.split(":"), dtype=float) * np.array([15., 15./60., 15./3600.]))
        dec_arr = np.array(self.dec.split(":"), dtype=float)
        self.dec_deg = np.sum(np.abs(dec_arr) * np.sign(dec_arr[0]) * np.array([1., 1./60., 1./3600.]))
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
        self.nsamp = int(ll[7])
        self.waterfall_duration = float(ll[11])
        self.waterfall_start_time = float(ll[17])
        self.waterfall_tsamp = float(ll[18])
        self.waterfall_nbins = self.data_zerodm_dedisp.shape[1]
        self.waterfall_nsubs = int(ll[6])
        self.waterfall_prededisp_nbins = int(ll[19])
        self.waterfall_downsamp = int(np.round(self.waterfall_tsamp/self.tsamp))
        self.min_freq = float(ll[20])
        self.max_freq = float(ll[21])
        self.sweep_duration = float(ll[22])
        self.sweep_start_time = float(ll[23])

        # Get variance from the half of the waterfall plot that definitely should not contain the pulse
        # (which is 1/4 of the way into the plot)
        self.varprof = np.var(self.data_zerodm_dedisp.sum(axis=0)[(self.waterfall_nbins/2):])

    def waterfall_time_axis(self, use_timeseries_time=False):
        """
        Generate a time axis for the waterfall plot in seconds, either beginning
        at zero or at the duration into the time series at which the plot actually
        begins.
        """
        self.waterfall_tsamp
        self.waterfall_start_time
        self.waterfall_nbins
        time_axis = np.arange(0, self.waterfall_duration, self.waterfall_tsamp)[:self.waterfall_nbins]
        if use_timeseries_time: return time_axis + self.waterfall_start_time
        else: return time_axis

    def waterfall_freq_axis(self):
        """
        Generate a frequency axis for the waterfall plot.
        """
        return np.linspace(self.min_freq, self.max_freq, self.waterfall_nsubs, endpoint=False)

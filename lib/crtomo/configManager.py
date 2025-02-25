# *-* coding: utf-8 *-*
"""Manage measurement configurations and corresponding measurements.

Geometric Factors
-----------------

.. plot:: pyplots/plot_K_vs_dipol_sep.py

Literature
----------

* Noel, Mark and Biwen Xu; Archaeological investigation by electrical
    resistivity tomography: a preliminary study. Geophys J Int 1991; 107 (1):
    95-102. doi: 10.1111/j.1365-246X.1991.tb01159.x
* Stummer, Peter, Hansruedi Maurer, and Alan G. Green. “Experimental Design:
  Electrical Resistivity Data Sets That Provide Optimum Subsurface
  Information.” Geophysics 69, no. 1 (January 1, 2004): 120–120.
  doi:10.1190/1.1649381.
* Roy, A., and A. Apparao. “DEPTH OF INVESTIGATION IN DIRECT CURRENT METHODS.”
  GEOPHYSICS 36, no. 5 (January 1, 1971): 943–59. doi:10.1190/1.1440226.

"""
import itertools

import scipy.interpolate as si
import numpy as np
import pandas as pd

import crtomo.mpl
plt, mpl = crtomo.mpl.setup()
import reda.utils.geometric_factors as edfK
import reda.utils.filter_config_types as fT

import reda.configs.configManager as reda_config_mgr


class ConfigManager(reda_config_mgr.ConfigManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # store measurements in a list of size N arrays
        self.measurements = {}
        # global counter for measurements
        self.meas_counter = - 1

    def clear_measurements(self):
        """Remove all measurements from self.measurements. Reset the
        measurement counter. All ID are invalidated.
        """
        keys = list(self.measurements.keys())
        for key in keys:
            del(self.measurements[key])
        self.meas_counter = -1

    def clear_measurements(self):
        """Remove all measurements from self.measurements. Reset the
        measurement counter. All ID are invalidated.
        """
        keys = list(self.measurements.keys())
        for key in keys:
            del(self.measurements[key])
        self.meas_counter = -1

    def delete_measurements(self, mid):
        del(self.measurements[mid])

    def add_measurements(self, measurements):
        """Add new measurements to this instance

        Parameters
        ----------
        measurements: numpy.ndarray
            one or more measurement sets. It must either be 1D or 2D, with the
            first dimension the number of measurement sets (K), and the second
            the number of measurements (N): K x N

        Returns
        -------
        mid: int
            measurement ID used to extract the measurements later on

        Examples
        --------
        >>> import numpy as np
            import crtomo.configManager as CRconfig
            config = CRconfig.ConfigManager(nr_of_electrodes=10)
            config.gen_dipole_dipole(skipc=0)
            # generate some random noise
            random_measurements = np.random.random(config.nr_of_configs)
            mid = config.add_measurements(random_measurements)
            # retrieve using mid
            print(config.measurements[mid])

        """
        subdata = np.atleast_2d(measurements)

        if self.configs is None:
            raise Exception(
                'must read in configuration before measurements can be stored'
            )

        # we try to accommodate transposed input
        if subdata.shape[1] != self.configs.shape[0]:
            if subdata.shape[0] == self.configs.shape[0]:
                subdata = subdata.T
            else:
                raise Exception(
                    'Number of measurements does not match number of configs'
                )

        return_ids = []
        for dataset in subdata:
            cid = self._get_next_index()
            self.measurements[cid] = dataset.copy()
            return_ids.append(cid)

        if len(return_ids) == 1:
            return return_ids[0]
        else:
            return return_ids

    def plot_error_pars(self, mid):
        """ ???

        """
        fig, axes = plt.subplots(1, 2, figsize=(10, 6))

        def plot_error_pars(axes, a, b, R, label=''):
            dR = a * R + b
            dlogR = np.abs(a + b / R)
            ax = axes[0]
            ax.scatter(R, dR / R * 100, label=label)
            ax = axes[1]
            ax.scatter(R, dlogR / np.abs(np.log(R)) * 100, label=label)
            ax.set_xscale('log')
            ax.set_yscale('log')

        for b in np.linspace(R.min(), np.percentile(R, 10), 5):
            plot_error_pars(axes, 0.05, b, R, label='b={0:.4f}'.format(b))
        axes[0].set_xlabel(r'$R [\Omega]$')
        axes[0].set_ylabel(r'$(\Delta R/R) \cdot 100 [\%]$')
        axes[1].set_xlabel(r'$log_{10}(R [\Omega])$')
        axes[1].set_ylabel(
            r'$log_{10}(R) / \Delta log_{10}(R) \cdot 100 [\%]$'
        )
        axes[0].axhline(y=100)
        axes[1].axhline(y=100)
        fig.tight_layout()
        fig.subplots_adjust(bottom=0.2)
        axes[0].legend(
            loc="lower center",
            ncol=4,
            bbox_to_anchor=(0, 0, 1, 1),
            bbox_transform=fig.transFigure
        )

        # fig.savefig('out.png', dpi=300)
        return fig

    def gen_voltage_dipoles_skip(self, cinj, skip=0):
        """For given current injections, generate all possible voltage dipoles
        with skip **skip**.

        Parameters
        ----------
        cinj : :py:class:`numpy.ndarray`
            Nx2 array containing the current injection electrodes a,b
        skip : int, optional
            Skip used for voltage electrodes. Default: 0

        """
        new_configs = []
        for ab in cinj:
            for i in range(1, self.nr_electrodes + 1):
                m = i
                n = i + skip + 1
                if m in ab or n in ab:
                    continue
                if n > self.nr_electrodes:
                    continue
                new_configs.append((ab[0], ab[1], m, n))
        configs = np.array(new_configs)
        self.add_to_configs(configs)
        return configs

    def load_crmod_data(self, data_source):
        """Load CRMod measurement data, either from file or directly from a
        numpy array.

        Parameters
        ----------
        data_source : string|numpy.ndarray
            if this is a string, treat it as an input filename. If it is a Nx5
            or Nx3 numpy array, use this data directly
        Returns
        -------
        cid_mag : int
            Measurement id for magnitude data
        cid_pha : int
            Measurement id for phase data
        """
        if isinstance(data_source, str):
            with open(filename, 'r') as fid:
                nr_of_configs = int(fid.readline().strip())
                measurements = np.loadtxt(fid)
                if nr_of_configs != measurements.shape[0]:
                    raise Exception(
                        'indicated number of measurements does not equal ' +
                        'to actual number of measurements'
                    )
        elif isinstance(data_source, pd.DataFrame):
            measurements = data_source[
                ['a', 'b', 'm', 'n', 'r' , 'rpha']
            ].values
        else:
            # assume numpy array
            # data already stored in the variable
            measurements = data_source

        assert measurements.shape[1] in (4, 6)
        if measurements.shape[1] == 4:
            # crmod ab-mn scheme
            abmn = self._crmod_to_abmn(measurements[:, 0:2])
            rmag = measurements[:, 2]
            rpha = measurements[:, 3]
        else:
            # abmn in separate columns
            abmn = measurements[:, 0:4]
            rmag = measurements[:, 4]
            rpha = measurements[:, 5]

        if self.configs is None:
            self.configs = abmn
        else:
            # check that configs match
            if not np.all(abmn == self.configs):
                raise Exception(
                    'previously stored configurations do not match new ' +
                    'configurations'
                )
        # add data
        cid_mag = self.add_measurements(rmag)
        cid_pha = self.add_measurements(rpha)
        return cid_mag, cid_pha


    def load_crmod_volt(self, filename):
        """Load a CRMod measurement file (commonly called volt.dat)

        Parameters
        ----------
        filename : string
            path to input filename

        Returns
        -------
        cid_mag : int
            Measurement id for magnitude data
        cid_pha : int
            Measurement id for phase data
        """
        cid_mag, cid_pha = self.load_crmod_data(filename)
        return cid_mag, cid_pha

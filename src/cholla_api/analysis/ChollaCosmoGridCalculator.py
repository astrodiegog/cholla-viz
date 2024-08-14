import numpy as np

class ChollaCosmoGridCalculator:
    '''
    Cholla Cosmology Grid Calculator object
        Serves as a calculator for cosmology-related values given a discretized
            ChollaGrid object. 
        
        Initialized with:
        - ChollaGrid (ChollaGrid): ChollaGrid object
        - OmegaM (float): present-day energy density parameter for matter
        - OmegaR (float): present-day energy density parameter for radiation
        - OmegaK (float): present-day energy density parameter for spatial curvature
        - OmegaL (float): present-day energy density parameter for dark energy
        - w0 (float): constant term in dark energy equation of state
        - wa (float): linear term in dark energy equation of state
        - H0 (float): present-day Hubble parameter in units of [km / s / Mpc]

    Values are returned in code units unless otherwise specified.
    '''
    
    def __init__(self, ChollaGrid, OmegaM, OmegaR, OmegaK, OmegaL, w0, wa, H0):
        
        # current implementation only works for cube grid
        assert ChollaGrid.nx_global == ChollaGrid.ny_global
        assert ChollaGrid.nx_global == ChollaGrid.nz_global
        assert ChollaGrid.Lx == ChollaGrid.Ly
        assert ChollaGrid.Lx == ChollaGrid.Lz

        self.nx = ChollaGrid.nx_global
        self.ny = ChollaGrid.ny_global
        self.nz = ChollaGrid.nz_global

        # present-day energy density for matter, radiation, curvature, and Dark Energy
        self.OmegaM = OmegaM
        self.OmegaR = OmegaR
        self.OmegaK = OmegaK
        self.OmegaL = OmegaL

        # Dark Energy equation of state like w(a) = w0 + wa(1-a)
        self.w0, self.wa = w0, wa

        # present-day hubble parameter in (km/s/Mpc)
        self.H0 = H0

        # some useful units
        self.cosmoh = self.H0 / 100.

        # NOTE: dx is saved in [kiloparsecs] ! convert to [h^-1 kpc]
        self.dx_h = ChollaGrid.dx / self.cosmoh

        self.Msun_cgs = 1.98847e33 # Solar Mass in grams
        self.kpc_cgs = 3.0857e21 # kiloparsecs in centimeters
        self.Mpc_cgs = self.kpc_cgs * 1.e3 # Megaparsecs in centimeters
        self.km_cgs = 1.e5 # kilometers in centimeters
        self.kyr_cgs = 3.15569e10 # kilo-years in seconds
        self.Myr_cgs = self.kyr_cgs * 1.e3 # mega-years in seconds
        self.Gyr_cgs = self.Myr_cgs * 1.e3 # giga-years in seconds

        self.G_cgs = 6.67259e-8 # gravitational constant in cgs [cm3 g-1 s-2]
        self.G_cosmo = self.G_cgs / self.km_cgs / self.km_cgs / self.kpc_cgs * self.Msun_cgs # gravitational constant in cosmological units [kpc (km2 s-2) Msun-1]

        self.kpc3_cgs = self.kpc_cgs * self.kpc_cgs * self.kpc_cgs
        self.Mpc3_cgs = self.Mpc_cgs * self.Mpc_cgs * self.Mpc_cgs

        # density cosmo units
        self.densityunit_cosmo2cgs = self.cosmoh * self.cosmoh * self.Msun_cgs / self.kpc3_cgs

        # Hubble time (1/H0)
        H0_cgs = self.H0 * self.km_cgs / self.Mpc_cgs
        t_H0_cgs = 1. / H0_cgs # in seconds
        self.t_H0 = t_H0_cgs / self.Myr_cgs # Hubble time in Gyrs

        # critical density in units of [g cm-3]
        self.rho_crit0_cgs = 3. * H0_cgs * H0_cgs / (8. * np.pi * self.G_cgs)
        
        # critical density in units of [h2 Msun Mpc-3]
        self.rho_crit0_cosmo = self.rho_crit0_cgs * (self.Mpc3_cgs) / (self.Msun_cgs) / self.cosmoh / self.cosmoh


    def get_lengthunit(self, a):
        '''
        Return the cosmological length unit [h^-1 / Mpc] in cgs at some scale
            factor. Length scales as (1/a)
        '''

        return self.Mpc_cgs / a

    def get_densityunit(self, a):
        '''
        Return the cosmological density unit [h2 Msun / kpc3] in cgs at some 
            scale factor. Density scales as (1/a^3)

        Args:
            a (float): scale factor
        Returns:
            (float): density unit (h^2 * Msun / kpc^3)
        '''
        a3 = a * a * a

        return self.densityunit_cosmo2cgs / a3

    def get_Hubble(self, a):
        '''
        Return the Hubble parameter at some scale factor

        Args:
            a (float): scale factor
        Returns:
            H (float): Hubble parameter (km/s/Mpc)
        '''

        a2 = a * a
        a3 = a2 * a
        a4 = a3 * a
        DE_factor = (a)**(-3. * (1. + self.w0 + self.wa))
        DE_factor *= np.exp(-3. * self.wa * (1. - a))

        H0_factor = (self.Omega_R / a4) + (self.Omega_M / a3)
        H0_factor += (self.Omega_K / a2) + (self.Omega_L * DE_factor)

        return self.H0 * np.sqrt(H0_factor)

    def get_dxproper(self, a):
        '''
        Return the proper distance between cells

        Args:
            a (float): scale factor
        Returns:
            (float): differential cell distance (h^-1 Mpc)
        '''
        dx_cgs = self.dx_h * self.kpc_cgs # h^-1 kpc * (#cm / kpc) =  h^-1 cm
        dx_Mpc = dx_cgs / self.Mpc_cgs # h^-1 cm / (#cm / Mpc) = h^-1 Mpc

        return dx_Mpc * a

    def get_dvHubble(self, a):
        '''
        Return the Hubble flow through a cell

        Args:
            a (float): scale factor
        Returns:
            (float): Hubble flow over a cell (km/s)
        '''

        return self.get_Hubble(a) * self.get_dxproper(a)


from hsz import HamiltonianMatrix, h, wf
import numpy as np
from scipy.special import sph_harm
import matplotlib.pyplot as plt
from tqdm import tqdm
import functools
import os
from ipywidgets import interact

class HeliumStarkAnimator(object):
    """
    """
    
    def __init__(self, hamiltonianMatrix):
        """
        """
        self.hamiltonianMatrix = hamiltonianMatrix
        
    def charge_distributions(self, state_idx, Efield, Bfield=0.0, **kwargs):
        """
        """
        eig_val, eig_vec = self.hamiltonianMatrix.stark_map(
            Efield, Bfield=Bfield, eig_vec=True, **kwargs)
        
        charge_dists = []
        for _eig_vec in tqdm(eig_vec, desc='Computing charge distributions'):
            charge_dists.append(
                self.charge_distribution(_eig_vec, state_idx))
        return charge_dists, eig_val
        
    def charge_distribution(self, eig_vec, state_idx, resolution=101, thres=1e-2):
        """
        """
        _wf_2d_all = []
        _sph_r_2d = None
        for i, eig_vec_comp in enumerate(eig_vec[:,state_idx]**2):
            if abs(eig_vec_comp)>thres:
                _rad_y_2d, _sph_y_2d, _sph_r_2d = wf_2d_cross_section(
                    self.hamiltonianMatrix.basis.states[i], resolution=resolution)
                _wf_2d_all.append(eig_vec_comp * _rad_y_2d * _sph_y_2d)
            else:
                _wf_2d_all.append(np.zeros([resolution, resolution]))
        _wf_2d_all = np.array(_wf_2d_all)
        _charge_2d = np.sum(_wf_2d_all, axis=0)**2 * _sph_r_2d**2
        return _charge_2d
    
    def plot_interactive(self, Efield, charge_dists, stark_map, state_idx, figsize=(8,4), cmap='RdBu_r'):
        """
        """   
        fig = plt.figure(figsize=figsize)
        i0 = 0
        limit = np.max(np.abs(charge_dists[i0]))

        ax1 = fig.add_subplot(1, 2, 1)
        ax1.set_xlabel('Electric field (V/cm)')
        ax1.set_ylabel('Energy / h (GHz)')
        ax1.set_title('Stark map')
        sm = ax1.plot(Efield, stark_map / (h*10**9), ls='-', lw=1.0, alpha=1, c=(0.2, 0.2, 0.8))
        mp = ax1.plot(Efield[i0], stark_map[i0, state_idx] / (h*10**9), 'ro')

        ax2 = fig.add_subplot(1, 2, 2)
        ax2.set_title('Charge distribution')
        ax2.set_axis_off()
        hp = ax2.imshow(np.abs(charge_dists[i0]), cmap=cmap, vmin=-limit, vmax=+limit)

        @interact(i=(0, len(charge_dists)-1, 1))
        def interaction_plots(i=0):
            hp.set_data(np.abs(charge_dists[i]))
            limit = np.max(np.abs(charge_dists[i]))
            hp.vmin = -limit
            hp.vmax = +limit
            mp[0].set_data(Efield[i], stark_map[i, state_idx] / (h*10**9))
            fig.canvas.draw()
    
    def plot(self, distribution, figsize=(3,3), cmap='RdBu_r'):
        """
        """
        fig, ax = plt.subplots(figsize=figsize)
        limit = np.max(np.abs(distribution))
        plot = plt.imshow(np.abs(distribution), cmap=cmap, vmin=-limit, vmax=+limit)
        ax.set_axis_off()
        
    def save(self, distributions, images_dir='images'):
        """
        """
        if not os.path.isdir(images_dir):
            os.mkdir(images_dir)
            
        for i, distribution in enumerate(distributions):
            limit = np.max(np.abs(distribution))
            plt.imsave(os.path.join(images_dir, '{}.jpg'.format(i)), 
                       np.abs(distribution), cmap = "RdBu_r", vmin=-limit, vmax=limit)
        

def find_nearest_rad_y(value, find_array_X, find_array_Y):
    idx = (np.abs(find_array_X-value)).argmin()
    return find_array_Y[idx]

def wf_2d_cross_section(state, frac_max_r=0.4, resolution=101):
    # Get radial values for the state
    nmax = state.n
    rad_r_1d, rad_y_1d = wf(state.n, state.L, nmax)

    # Set up the plotting grid
    x = 0.0
    y = np.linspace(-np.max(rad_r_1d)*frac_max_r, np.max(rad_r_1d)*frac_max_r, resolution)
    z = np.linspace(-np.max(rad_r_1d)*frac_max_r, np.max(rad_r_1d)*frac_max_r, resolution)
    _y, _z = np.meshgrid(y, z)

    # Calculate the corresponding spherical polar coordinates
    sph_az_2d, sph_el_2d, sph_r_2d = cart2sph(x, _y, _z)

    # Get the value of the radial wavefunction for each value of r
    rad_y_2d = np.array([list(map(functools.partial(
        find_nearest_rad_y, find_array_X = rad_r_1d, find_array_Y = rad_y_1d), i)) for i in sph_r_2d])

    # Get the value of the elevation part of the spherical wavefunction for each value of el
    phi = sph_el_2d # Elevation
    theta = sph_az_2d # Azithumal
    sph_y_2d = sph_harm(state.M, state.L, theta, phi)
    
    return rad_y_2d, sph_y_2d, sph_r_2d

def cart2sph(x, y, z):
    hxy = np.hypot(x, y)
    r = np.hypot(hxy, z)
    el = np.arctan2(z, hxy) + np.pi/2.0
    az = np.arctan2(y, x) + np.pi/2.0
    return az, el, r

def wf_2d(rad_y_2d, sph_y_2d, sph_r_2d):
    return rad_y_2d * sph_y_2d

def amp_2d(rad_y_2d, sph_y_2d, sph_r_2d):
    return 4 * np.pi * sph_r_2d**2 * np.abs(rad_y_2d * sph_y_2d)**2
    
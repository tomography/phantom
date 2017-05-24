#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) 2016, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2016. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import numpy as np
import scipy.ndimage
import logging
import warnings
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from xdesign.grid import *
from xdesign.util import gen_mesh
from numpy.fft import fftn, ifftn, fftshift, ifftshift

logger = logging.getLogger(__name__)


__author__ = "Daniel Ching, Doga Gursoy"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['multislice_propagate',
           'plot_wavefront',
           'initialize_wavefront']





def initialize_wavefront(grid, **kwargs):
    """Initialize wavefront.

    Parameters:
    -----------
    wvfnt_width : int
        Pixel width of wavefront.
    """
    type = kwargs['type']
    wave_shape = grid.grid_delta.shape[1:]
    if type == 'plane':
        wavefront = np.ones(wave_shape).astype('complex64')
    if type == 'point':
        wid = kwargs['width']
        wavefront = np.zeros(wave_shape).astype('complex64')
        center = int(wave_shape / 2)
        radius = int(wid / 2)
        wavefront[:wid] = 1.
        wavefront = np.roll(wavefront, int((wave_shape - wid) / 2))
    return wavefront


def _extract_slice(delta_grid, beta_grid, islice):
    """Extract a specified slice from the grid.

    Parameters:
    -----------
    delta_grid : ndarray
        As-constructed grid with defined phantoms filled with material delta values.
    beta_grid : ndarray
        As-constructed grid with defined phantoms filled with material beta values.
    islice : int
        Index of slice to be extracted.
    """
    pass


def _slice_modify(grid, delta_slice, beta_slice, wavefront, lmda):
    """Modify wavefront within a slice.

    Parameters:
    -----------
    delta_slice : ndarray
        Extracted slice filled with material delta values.
    beta_slice : ndarray
        Extracted slice filled with material beta values.
    wavefront : ndarray
        Wavefront.
    delta_nm : float
        Slice thickness in nm.
    lmda : float
        Wavelength in nm.
    """
    delta_nm = grid.voxel_z
    kz = 2 * np.pi * delta_nm / lmda
    wavefront = wavefront * np.exp((kz * delta_slice) * 1j) * np.exp(-kz * beta_slice)

    return wavefront


def _slice_propagate(grid, wavefront, lmda):
    """Free space propagation.

    Parameters:
    -----------
    wavefront : ndarray
        Wavefront.
    delta_nm : float
        Slice thickness in nm.
    lat_nm : float
        Lateral pixel length in nm.
    wvfnt_width : int
        Pixel width of wavefront.
    lmda : float
        Wavelength in nm.
    """
    delta_nm = grid.voxel_z
    u_max = 1. / (2. * grid.voxel_x)
    v_max = 1. / (2. * grid.voxel_y)
    u, v = gen_mesh([v_max, u_max], grid.grid_delta.shape[1:3])
    H = np.exp(-1j * 2 * np.pi * delta_nm / lmda * np.sqrt(1. - lmda ** 2 * u ** 2  - lmda ** 2 * v ** 2))
    wavefront = ifftn(ifftshift(fftshift(fftn(wavefront)) * H))
    # H = np.exp(-1j * 2 * np.pi * delta_nm / lmda * np.sqrt(1. - lmda ** 2 * u ** 2))
    # wavefront = np.fft.ifftn(np.fft.fftn(wavefront) * np.fft.fftshift(H))
    return wavefront


def _free_propagate(grid, wavefront, lmda, dist_nm):

    u_max = 1. / (2. * grid.voxel_x)
    v_max = 1. / (2. * grid.voxel_y)
    u, v = gen_mesh([v_max, u_max], grid.grid_delta.shape[1:3])
    H = np.exp(-1j * 2 * np.pi * dist_nm / lmda * np.sqrt(1. - lmda ** 2 * u ** 2  - lmda ** 2 * v ** 2))
    wavefront = ifftn(ifftshift(fftshift(fftn(wavefront)) * H))
    # H = np.exp(-1j * 2 * np.pi * delta_nm / lmda * np.sqrt(1. - lmda ** 2 * u ** 2))
    # wavefront = np.fft.ifftn(np.fft.fftn(wavefront) * np.fft.fftshift(H))
    return wavefront


def _far_propagate(grid, wavefront, lmda, z):
    """Free space propagation using double Fourier algorithm.
    """
    assert isinstance(grid, Grid3d)
    y0 = grid.yy[0, :, :]
    x0 = grid.xx[0, :, :]
    y = y0 * (lmda * z) * (grid.size[1] * grid.voxel_y ** 2)
    x = x0 * (lmda * z) * (grid.size[2] * grid.voxel_x ** 2)
    wavefront = fftshift(fftn(wavefront * np.exp(-1j * 2 * np.pi / lmda * np.sqrt(z ** 2 + x0 ** 2 + y0 ** 2))))
    wavefront = wavefront * np.exp(-1j * 2 * np.pi / lmda * np.sqrt(z ** 2 + x ** 2 + y ** 2))
    return wavefront


def _far_propagate_2(grid, wavefront, lmd, z_um):
    """Free space propagation using double Fourier algorithm.
    """
    assert isinstance(grid, Grid3d)

    N = grid.size[1]
    M = grid.size[2]
    D = N * grid.voxel_y
    H = M * grid.voxel_x
    f1 = wavefront

    V = N/D
    U = M/H
    d = np.arange(-(N-1)/2,(N-1)/2+1,1)*D/N
    h = np.arange(-(M-1)/2,(M-1)/2+1,1)*H/M
    v = np.arange(-(N-1)/2,(N-1)/2+1,1)*V/N
    u = np.arange(-(M-1)/2,(M-1)/2+1,1)*U/M

    f2 = np.fft.fftshift(np.fft.fft2(f1*np.exp(-1j*2*np.pi/lmd*np.sqrt(z_um**2+d**2+h[:,np.newaxis]**2))))*np.exp(-1j*2*np.pi*z_um/lmd*np.sqrt(1.+lmd**2*(v**2+u[:,np.newaxis]**2)))/U/V/(lmd*z_um)*(-np.sqrt(1j))
    d2,h2=v*lmd*z_um,u*lmd*z_um
    return f2


def plot_wavefront(wavefront, grid, save_folder='simulation', fname='exiting_wave'):
    """Plot wavefront intensity.

    Parameters:
    -----------
    wavefront : ndarray
        Complex wavefront.
    lat_nm : float
        Lateral pixel length in nm.
    """
    i = np.abs(wavefront * np.conjugate(wavefront))

    fig = plt.figure(figsize=[9, 9])
    plt.imshow(np.log(i), cmap='gray')
    plt.xlabel('x (nm)')
    plt.ylabel('y (nm)')
    plt.show()
    #fig.savefig(save_folder+'/'+fname+'.png', type='png')


def multislice_propagate(grid, probe, wavefront, free_prop_dist=None):
    """Do multislice propagation for wave with specified properties in the constructed grid.

    Parameters:
    -----------
    delta_grid : ndarray
        As-constructed grid with defined phantoms filled with material delta values.
    beta_grid : ndarray
        As-constructed grid with defined phantoms filled with material beta values.
    probe : instance
        Probe beam instance.
    delta_nm : float
        Slice thickness in nm.
    lat_nm : float
        Lateral pixel size in nm.
    """
    # 2d array should be reshaped to 3d.
    assert isinstance(grid, Grid3d)
    delta_grid = grid.grid_delta
    beta_grid = grid.grid_beta

    # wavelength in nm
    lmda = probe.wavelength
    # I assume Probe class has a wavelength attribute. E.g.:
    # class Probe:
    #     def __init__(self, energy):
    #         self.energy = energy
    #         self.wavelength = 1.23984/energy
    n_slice = delta_grid.shape[0]
    for i_slice in range(n_slice):
        delta_slice = delta_grid[i_slice, :, :]
        beta_slice = beta_grid[i_slice, :, :]
        wavefront = _slice_modify(grid, delta_slice, beta_slice, wavefront, lmda)
        wavefront = _slice_propagate(grid, wavefront, lmda)
    if free_prop_dist is not None:
        wavefront = _free_propagate(grid, wavefront, lmda, free_prop_dist)
    return wavefront
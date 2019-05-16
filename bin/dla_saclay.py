#!/usr/bin/env python
from __future__ import print_function, division
import numpy as np
from scipy.stats import norm
from scipy.interpolate import interp1d, interp2d
import astropy.table
import os
import fitsio
import time
import glob
import argparse
from SaclayMocks import constant, util
import cosmolopy.distance as dist

try:
    from pyigm.fN.fnmodel import FNModel
    fN_default = FNModel.default_model()
    fN_default.zmnx = (0.,4)
    fN_cosmo = fN_default.cosmo
    use_pyigm = True
except:
    use_pyigm = False


def dz_of_z(cell_size=2.19, zmin=1.3, zmax=4., nbin=500):
    h = constant.h
    Om = constant.omega_M_0
    Om = constant.omega_M_0
    OL = constant.omega_lambda_0
    Ok = constant.omega_k_0
    cosmo_fid = {'omega_M_0':Om, 'omega_lambda_0':OL, 'omega_k_0':Ok, 'h':h}
    R_of_z, z_of_R = dist.quick_distance_function(dist.comoving_distance, return_inverse=True, **cosmo_fid)
    rmin = R_of_z(zmin)*h
    rmax = R_of_z(zmax)*h
    r_vec = np.linspace(rmin, rmax, nbin)
    z_vec = z_of_R(r_vec/h)
    dz = z_of_R((r_vec + cell_size)/h) - z_of_R(r_vec/h)
    return interp1d(z_vec, dz)


def doloop(dlas_in_cell,velocity,zedges, dla_z, dla_skw_id, dla_rsd_dz, dla_count):
    """ Auxiliary function to perform the loop to populate the DLA cells"""
    for skw_id,dla in enumerate(dlas_in_cell):
        #Find cells that will be allocated at least one DLA
        dla_cells = np.where(dla>0)[0]
        #For each dla, assign it a redshift, a velocity and a column density.
        for cell in dla_cells:
            dla_z[dla_count:dla_count+dla[cell]] = zedges[cell]+(zedges[cell+1]-zedges[cell])*np.random.random(size=dla[cell])
            dla_skw_id[dla_count:dla_count+dla[cell]] = skw_id
            dla_rsd_dz[dla_count:dla_count+dla[cell]] = velocity[skw_id,cell]/constant.c
            dla_count = dla_count+dla[cell]
    return dla_z, dla_skw_id, dla_rsd_dz, dla_count

def nu_of_bD(b):
    """ Compute the Gaussian field threshold for a given bias"""
    nu = np.linspace(-10,100,500) # Generous range to interpolate
    # use something non linear for nu ? To get more points close to 0
    p_nu = norm.pdf(nu)
    galaxy_mean = norm.cdf(-nu)  # probability to be above threshold
                                # this gives zero for nu > 37.5
    b_nu = np.zeros(nu.shape)
    b_nu[galaxy_mean!=0] = p_nu[galaxy_mean!=0]/galaxy_mean[galaxy_mean!=0]
    # it means that to get a bias of 2, you need a value of the field
    # to be 2 times more probable than the probability to be above this value
    b_nu[galaxy_mean==0] = nu[galaxy_mean==0]
        # approximation for nu > 37.5, better than 0.027, i.e 0.07%
    y = interp1d(b_nu,nu)
    return y(b)

# # Not used
# def get_bias_z(fname,dla_bias):
#     """ Given a path, read the z array there and return a bias inversely
#     proportional to the growth"""
#     colore_cosmo = fits.open(fname)[4].data
#     z = colore_cosmo['Z']
#     D = colore_cosmo['D']
#     y = interp1d(z,D)
#     bias = dla_bias/D*y(2.25)
#     return z, bias, D

# # Not used
# def get_sigma_g(fname, mode='SG'):
#     if mode=='SG':
#         # Biased as well
#         return fits.open(fname)[4].header['SIGMA_G']
#     if mode=='SKW':
#         # Approximation 2: Take the skewers (biased when QSOs are present)
#         skewers = fits.open(fname)[2].data
#         return np.std(skewers,axis=0)

def flag_DLA(zq,z_cells,deltas,nu_arr,sigma_g,zlow,dz_of_z, rand=False):
    """ Flag the pixels in a skewer where DLAs are possible"""
    # find cells with density above threshold
    if not rand:
        flag = deltas > nu_arr*sigma_g  # (nspec, npix)
    else:
        flag = np.bool_(np.ones_like(deltas))  # (nspec, npix)
    # mask cells with z > z_qso, where DLAs would not be observed
    Nq=len(zq)
    for i in range(Nq):
        dz = dz_of_z(zq[i])  # avoid drawing DLA in same cell as QSO
        low_z = (z_cells < zq[i]-dz) & (z_cells > zlow)
        flag[i,:] *= low_z
    return flag

#number per unit redshift from minimum lg(N) in file (17.2) to argument
# Reading file from https://arxiv.org/pdf/astro-ph/0407378.pdf

def dnHD_dz_cumlgN(z,logN):
    tab = astropy.table.Table.read(os.path.abspath('LyaCoLoRe/example_data/zheng_cumulative.overz'),format='ascii')
    y = interp2d(tab['col1'],tab['col2'],tab['col3'],fill_value=None)
    return y(z,logN)

# def dNdz(z, Nmin=20.0, Nmax=22.5):
#     """ Get the column density distribution as a function of z,
#     for a given range in N"""
#     if use_pyigm:
#         # get incidence rate per path length dX (in comoving coordinates)
#         dNdX = fN_default.calculate_lox(z,Nmin,Nmax)
#         # convert dX to dz
#         dXdz = fN_cosmo.abs_distance_integrand(z)
#         return dNdX * dXdz
#     else:
#         return dnHD_dz_cumlgN(z,Nmax)-dnHD_dz_cumlgN(z,Nmin)


def dNdz(z, Nmin=20.0, Nmax=22.5, nsamp=100):
    """ Get the column density distribution as a function of z,
    for a given range in N"""
    # get incidence rate per path length dX (in comoving coordinates)
    nn = np.linspace(Nmin,Nmax,nsamp)
    aux = fN_default.evaluate(nn, z)
    dNdz = np.sum(np.exp(aux)*(nn[1]-nn[0]))
    return dNdz


def get_N(z, Nmin=20.0, Nmax=22.5, nsamp=100):
    """ Get random column densities for a given z
    """

    # number of DLAs we want to generate
    Nz = len(z)
    nn = np.linspace(Nmin,Nmax,nsamp)
    probs = np.zeros([Nz,nsamp])
    if use_pyigm:
        auxfN = fN_default.evaluate(nn,z)
        #auxfN = (np.cumsum(10**auxfN, axis=0)/np.sum(10**auxfN, axis=0)).T
        probs = (np.exp(auxfN)/np.sum(np.exp(auxfN), axis=0)).T
        #plt.plot(nn,auxfN.T)
    else:
        probs_low = dnHD_dz_cumlgN(z,nn[:-1]).T
        probs_high = dnHD_dz_cumlgN(z,nn[1:]).T
        probs[:,1:] = probs_high-probs_low
    NHI = np.zeros(Nz)
    for i in range(Nz):
        #if use_pyigm:
        #    nfunc = interp1d(auxfN[i],nn,fill_value='extrapolate')
        #    NHI[i] = nfunc(np.random.uniform())
        #else:
        #    NHI[i] = np.random.choice(nn,size=1,p=probs[i]/np.sum(probs[i]))+(nn[1]-nn[0])*np.random.random(size=1)
        NHI[i] = np.random.choice(nn,size=1,p=probs[i]/np.sum(probs[i]))+(nn[1]-nn[0])*np.random.random(size=1)
    return NHI


def add_DLA_table_to_object_Saclay(hdulist,dNdz_arr,dz_of_z,dla_bias=2.0,extrapolate_z_down=None,Nmin=20.0,Nmax=22.5,zlow=1.8, rand=False):
    qso = hdulist['METADATA'].read() # Read the QSO table
    lam = hdulist['LAMBDA'].read() # Read the vector with the wavelenghts corresponding to each cell
    deltas = hdulist['DELTA'].read()  # (nspec, npix)
    velocity = hdulist['VELO_PAR'].read()  # (nspec, npix)
    #Linear growth rate of each cell in the skewer
    D_cell = hdulist['GROWTHF'].read()  # (npix)
    hdulist.close()
    #Quasar redshift for each skewer
    zq = qso['Z']  # (nspec)
    #Redshift of each cell in the skewer
    z_cell = lam / constant.lya - 1  # (npix)
    # # Not use
    # # Read cosmo
    # cosmo_hdu = fitsio.read_header(fname_cosmo, ext=1) # Reading the cosmological parameters used for the simulation
    # Oc = cosmo_hdu['OM']-cosmo_hdu['OB'] # Omega_c
    # Ob = cosmo_hdu['OB'] # Omega_b
    # h = cosmo_hdu['H'] # h
    # Ok = cosmo_hdu['OK'] # Omega_k
    #Setup bias as a function of redshift
    # y = interp1d(z_cell,D_cell)
    # bias = dla_bias/(D_cell)*y(2.25)  # (npix)
    # sigma_g = fitsio.FITS(fname_sigma)[0].read_header()['SIGMA']
    sigma_g = constant.sigma_g
    # Gaussian field threshold:
    nu_arr = nu_of_bD(dla_bias*sigma_g*D_cell)  # (npix)
    #Figure out cells that could host a DLA, based on Gaussian fluctuation
    flagged_cells = flag_DLA(zq,z_cell,deltas,nu_arr,sigma_g,zlow, dz_of_z, rand)
    flagged_cells[deltas==-1e6]=False  # don't draw DLA outside forest
    #Edges of the z bins
    if extrapolate_z_down and extrapolate_z_down<z_cell[0]:
        zedges = np.concatenate([[extrapolate_z_down],(z_cell[1:]+z_cell[:-1])*0.5,[z_cell[-1]+(-z_cell[-2]+z_cell[-1])*0.5]]).ravel()
    else:
        zedges = np.concatenate([[z_cell[0]],(z_cell[1:]+z_cell[:-1])*0.5,[z_cell[-1]+(-z_cell[-2]+z_cell[-1])*0.5]]).ravel()
    z_width = zedges[1:]-zedges[:-1]

    #Get the average number of DLAs per cell, from the column density dist.
    mean_N_per_cell = z_width*dNdz_arr  # (npix)
    #For a given z, probability of having the density higher than the threshold
    p_nu_z = 1.0-norm.cdf(nu_arr)

    #Define mean of the Poisson distribution (per cell)
    mu = mean_N_per_cell/p_nu_z * np.ones_like(flagged_cells)
    # mu *= 20000  # incrase number of DLA
    # mu *= 6.4
    # mu = mean_N_per_cell*(1+bias*deltas)

    mu[~flagged_cells]=0
    #Select cells that will hold a DLA, drawing from the Poisson distribution
    pois = np.random.poisson(mu)#,size=(len(zq),len(mu)))
    #Number of DLAs in each cell (mostly 0, several 1, not many with >1)
    dlas_in_cell = pois*flagged_cells
    ndlas = np.sum(dlas_in_cell)
    #Store information for each of the DLAs that will be added
    dla_z = np.zeros(ndlas)
    dla_skw_id = np.zeros(ndlas, dtype='int64')
    dla_rsd_dz = np.zeros(ndlas)
    dla_count = 0
    dla_z, dla_skw_id, dla_rsd_dz, dla_count = doloop(dlas_in_cell, velocity, zedges, dla_z, dla_skw_id, dla_rsd_dz, dla_count)
    dla_NHI = get_N(dla_z,Nmin=Nmin,Nmax=Nmax)

    #global id for the skewers
    MOCKIDs = qso['THING_ID'][dla_skw_id]
    ZQSO = zq[dla_skw_id]
    ra = qso['RA'][dla_skw_id]
    dec = qso['DEC'][dla_skw_id]
    z_norsd = qso['Z_noRSD'][dla_skw_id]
    #Make the data into a table HDU
    dla_table = astropy.table.Table([MOCKIDs,dla_z,dla_rsd_dz,dla_NHI,ZQSO, z_norsd, ra, dec],names=('MOCKID','Z_DLA','DZ_DLA','N_HI_DLA','Z_QSO', 'Z_QSO_NO_RSD', 'RA', 'DEC'))

    return dla_table, ndlas

######

# Options and main

######

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--input_path', type = str, default = None, required = True,
                    help='Path to input directory tree to explore, e.g., /global/cscratch1/sd/*/spectra/*')
parser.add_argument('--output_path', type = str, default = None, required = True,
                    help='Output path')
parser.add_argument('--input_pattern', type = str, default = 'spectra_merged*.fits',
                    help='Filename pattern')
parser.add_argument('--nmin', type = float, default=17.2,
                    help='Minimum value of log(NHI) to consider')
parser.add_argument('--nmax', type = float, default=22.5,
                    help='Maximum value of log(NHI) to consider')
parser.add_argument('--dla_bias', type = float, default=2.,
                    help='DLA bias at z=2.25')
parser.add_argument('--cell_size', type = float, default=2.19,
                    help='size of voxcell')
parser.add_argument('-seed', type = int, default=None,
                    help='set seed')
parser.add_argument("-random",type = str, default='False',
                    help="If True, generate randoms")
parser.add_argument("--random_factor",type = float, default=3.,
                    help="Factor x thus that n_rand = x * n_data")
args = parser.parse_args()

t0 = time.time()
random_cond = util.str2bool(args.random)
seed = args.seed
if seed is None:
    seed = np.random.randint(2**31 -1, size=1)[0]
    np.random.seed(seed)
    print("Seed has not been specified. Seed is set to {}".format(seed))
else:
    np.random.seed(seed)
    print("Specified seed is {}".format(seed))

print("Files will be read from {}".format(args.input_path))
print("Output will be written in {}".format(args.output_file))
flist = glob.glob(os.path.join(args.input_path,args.input_pattern))
print('Will read', len(flist),' files')
hdulist = fitsio.FITS(flist[0])
lam = hdulist[2].read()
# cosmo_hdu = fitsio.FITS(args.fname_cosmo)[1].read_header()
z_cell = lam / constant.lya - 1.
dNdz_arr = dNdz(z_cell, Nmin=args.nmin, Nmax=args.nmax)
dNdz_arr *= 20000.
dNdz_arr *= 6.4
if random_cond:
    dNdz_arr *= args.random_factor
dNdz_arr /= (-0.01534254*z_cell + 0.0597803)*6.4 / 0.186  # correct the z dependency
dz_of_z = dz_of_z(args.cell_size)
ndlas = 0

for i, fname in enumerate(flist):
    try:
        hdulist = fitsio.FITS(fname)
        aux, n = add_DLA_table_to_object_Saclay(hdulist, dNdz_arr,dz_of_z, args.dla_bias, Nmin=args.nmin, Nmax=args.nmax, rand=random_cond)
        hdulist.close()
    except IOError:
        print("WARNING: can't read fname")
    ndlas += n
    if i==0:
        out_table = aux
    else:
        out_table = astropy.table.vstack([out_table, aux])
    if i%500==0:
        print('Read %d of %d' %(i,len(flist)))

if not random_cond:
    filename = args.output_path + "/dla.fits"
else:
    filename = args.output_path + "/dla_randoms.fits"
out_table.write(filename, overwrite=True)
print("Fits table written.")
print("Draw {} DLAs".format(ndlas))
print("Took {} s".format(time.time() - t0))

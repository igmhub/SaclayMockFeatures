import fitsio
import picca.wedgize
import argparse
import matplotlib.pyplot as plt
import numpy as np
import h5py


# Plot options
SMALL_SIZE = 18
MEDIUM_SIZE = 20
BIGGER_SIZE = 22
plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize

plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title
plt.rc('figure', figsize=(9,7))

parser = argparse.ArgumentParser()
parser.add_argument("-i", type=str, nargs="*", help="list of files")
parser.add_argument("--labels", type=str, nargs='*', help='list of labels', default=None)
parser.add_argument("--rt-min", type=float, default=0.)
parser.add_argument("--rt-max", type=float, default=200.)
parser.add_argument("--nrt", type=int, default=50)
parser.add_argument("--rp-min", type=float, default=0.)
parser.add_argument("--rp-max", type=float, default=200.)
parser.add_argument("--nrp", type=int, default=50)
parser.add_argument("--mu-min", type=float, default=-1.)
parser.add_argument("--mu-max", type=float, default=1.)
parser.add_argument("--r-pow", type=int, default=2)
parser.add_argument("--error-bar", action='store_true')
parser.add_argument("--title", default="")

args = parser.parse_args()

files = args.i
labels = args.labels
rpmin = args.rp_min
rpmax = args.rp_max
nrp = args.nrp
rtmin = args.rt_min
rtmax = args.rt_max
nrt = args.nrt
mumin = args.mu_min
mumax = args.mu_max
r_pow = args.r_pow

if labels is None:
    labels = np.arange(len(files))

# fmt = ['.', '.', '.', 'x', '+', 'o', '.', 'x', 'o', '-.', ':']
fmt = ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.']
# colors = ['black', 'darkblue', 'darkgreen', 'red', 'darkorange', 'darkviolet', 'saddlebrown', 'dodgerblue', 'deeppink']
# colors = ['b', 'darkorange', 'r']
colors = ['tab:blue', 'tab:orange', 'tab:green']
# colors = ['black', 'royalblue', 'r']
# colors = ['darkblue', 'darkblue', 'r', 'r']
# colors = ['royalblue', 'royalblue', 'r', 'r', 'green', 'green']
linestyles = ['-', '--', '-', '--', '-', '--']

mu0, mu1, mu2, mu3, mu4 = 0, 0.5, 0.8, 0.95, 1
w = picca.wedgize.wedge(mumin=mumin,mumax=mumax, rtmax=rtmax, rpmax=rpmax, rtmin=rtmin, rpmin=rpmin, nrt=nrt, nrp=nrp,absoluteMu=True)
w1 = picca.wedgize.wedge(mumin=mu0,mumax=mu1, rtmax=rtmax, rpmax=rpmax, rtmin=rtmin, rpmin=rpmin, nrt=nrt, nrp=nrp,absoluteMu=True)
w2 = picca.wedgize.wedge(mumin=mu1,mumax=mu2, rtmax=rtmax, rpmax=rpmax, rtmin=rtmin, rpmin=rpmin, nrt=nrt, nrp=nrp,absoluteMu=True)
w3 = picca.wedgize.wedge(mumin=mu2,mumax=mu3, rtmax=rtmax, rpmax=rpmax, rtmin=rtmin, rpmin=rpmin, nrt=nrt, nrp=nrp,absoluteMu=True)
w4 = picca.wedgize.wedge(mumin=mu3,mumax=mu4, rtmax=rtmax, rpmax=rpmax, rtmin=rtmin, rpmin=rpmin, nrt=nrt, nrp=nrp,absoluteMu=True)

# f1, ax1 = plt.subplots(figsize=(12,8))
# f2, ax2 = plt.subplots(figsize=(12,8))
f1, ax1 = plt.subplots()
f2, ax2 = plt.subplots()
for i, f in enumerate(files):
    if '.fits' in f:
        h5_flag = False
        data = fitsio.FITS(f)
        da = data[1]['DA'][:]
        co = data[1]['CO'][:]
    if '.h5' in f:
        print("Reading {} file ; using cov mat from {}".format(f, files[i-1]))
        h5_flag = True
        ff = h5py.File(f, 'r')
        if "LYA(LYA)xLYA(LYA)" in ff.keys():
            da = ff["LYA(LYA)xLYA(LYA)/fit"][...]
        elif "cf_z_0_10" in ff.keys():
            da = ff["cf_z_0_10/fit"][...]
        else:
            idx1 = int(f.rfind("/"))+1
            idx2 = int(f.find(".h5"))
            da = ff[f[idx1:idx2]+"/fit"][...]
        ff.close()

    data_wedge = w.wedge(da,co)
    coef = data_wedge[0]**r_pow
    data_wedge1 = w1.wedge(da,co)
    coef1 = data_wedge1[0]**r_pow
    data_wedge2 = w2.wedge(da,co)
    coef2 = data_wedge2[0]**r_pow
    data_wedge3 = w3.wedge(da,co)
    coef3 = data_wedge3[0]**r_pow
    data_wedge4 = w4.wedge(da,co)
    coef4 = data_wedge4[0]**r_pow
    if h5_flag:
        ax1.plot(data_wedge[0],coef*data_wedge[1], label=labels[i], color=colors[i], linestyle=linestyles[i])
        ax2.plot(data_wedge1[0],coef1*data_wedge1[1], label=labels[i], color=colors[i], linestyle=linestyles[i])
        ax2.plot(data_wedge2[0],coef2*data_wedge2[1], color=colors[i], linestyle=linestyles[i])
        ax2.plot(data_wedge3[0],coef3*data_wedge3[1], color=colors[i], linestyle=linestyles[i])
        ax2.plot(data_wedge4[0],coef4*data_wedge4[1], color=colors[i], linestyle=linestyles[i])
    elif args.error_bar:
        ax1.errorbar(data_wedge[0],coef*data_wedge[1],yerr=coef*np.sqrt(np.diag(data_wedge[2])), label=labels[i], color=colors[i], fmt=fmt[i])
        ax2.errorbar(data_wedge1[0],coef1*data_wedge1[1],yerr=coef1*np.sqrt(np.diag(data_wedge1[2])), label=labels[i], color=colors[i], fmt=fmt[i])
        ax2.errorbar(data_wedge2[0],coef2*data_wedge2[1],yerr=coef2*np.sqrt(np.diag(data_wedge2[2])), color=colors[i], fmt=fmt[i])
        ax2.errorbar(data_wedge3[0],coef3*data_wedge3[1],yerr=coef3*np.sqrt(np.diag(data_wedge3[2])), color=colors[i], fmt=fmt[i])
        ax2.errorbar(data_wedge4[0],coef4*data_wedge4[1],yerr=coef4*np.sqrt(np.diag(data_wedge4[2])), color=colors[i], fmt=fmt[i])
    else:
        ax1.plot(data_wedge[0],coef*data_wedge[1], label=labels[i], color=colors[i], marker=fmt[i])
        ax2.plot(data_wedge1[0],coef1*data_wedge1[1], label=labels[i], color=colors[i], marker=fmt[i])
        ax2.plot(data_wedge2[0],coef2*data_wedge2[1], color=colors[i], marker=fmt[i])
        ax2.plot(data_wedge3[0],coef3*data_wedge3[1], color=colors[i], marker=fmt[i])
        ax2.plot(data_wedge4[0],coef4*data_wedge4[1], color=colors[i], marker=fmt[i])

for ax in [ax1, ax2]:
    ax.grid()
    ax.legend()
    ax.set_title("CF - {}".format(args.title), fontsize=20)
    ax.set_xlabel(r"$r \, [\mathrm{Mpc \, h^{-1}}]$",fontsize=20)
    if r_pow == 2:
        ax.set_ylabel(r"$r^{2}\xi(r) \, [\mathrm{Mpc \, h^{-1}}]$",fontsize=20)
    if r_pow == 1:
        ax.set_ylabel(r"$r\xi(r) \, [\mathrm{Mpc \, h^{-1}}]$",fontsize=20)
    if r_pow == 0:
        ax.set_ylabel(r"$\xi(r) \, [\mathrm{Mpc \, h^{-1}}]$",fontsize=20)
    plt.tight_layout()

plt.show()

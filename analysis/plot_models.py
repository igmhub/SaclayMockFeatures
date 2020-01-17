import h5py
import fitsio
import numpy as np
import matplotlib.pyplot as plt
import picca.wedgize


'''
This code plots the various models used in the DR16 analysis,
starting with the one with less complexity to the one of the DR16 paper
'''

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

model_dir = "/global/cscratch1/sd/tetourne/Analysis/redo_dr16/Fits/cf/Model_effect"
cf_dir = "/global/cscratch1/sd/tetourne/Analysis/redo_dr16/Correlations"
print("Reading correlation function in {}".format(cf_dir))
print("Reading fits in {}".format(model_dir))

toplot = ['kaiser', 'kaiser_nl', 'kaiser_nl_met', 'kaiser_nl_met_hcd', 'kaiser_nl_met_hcd_sky']
labels = toplot
# labels = ['kaiser', 'kaiser_nl', 'kaiser_nl_hcd', 'kaiser_nl_hcd_met', 'kaiser_nl_hcd_met_sky']
fit_name = 'cf_z_0_10'
colors = ['royalblue', 'green', 'darkorange', 'r', 'purple']

# Read the fits from picca
files = {}
for item in toplot:
    files[item] = h5py.File(model_dir+"/"+item+".h5")

# ### List of files :
# fit1 = h5py.File(model_dir+"/kaiser.h5")
# fit2 = h5py.File(model_dir+"/kaiser_nl.h5")
# fit3 = h5py.File(model_dir+"/kaiser_nl_met.h5")
# fit3 = h5py.File(model_dir+"/kaiser_nl_hcd.h5")
# fit4 = h5py.File(model_dir+"/kaiser_nl_met_hcd.h5")
# fit5 = h5py.File(model_dir+"/kaiser_nl_met_hcd_sky.h5")

# Read the correlation function
fits = fitsio.FITS(cf_dir+"/cf_z_0_10-exp.fits")
da = fits[1].read()['DA']
co = fits[1].read()['CO']
fits.close()

# extract the correlation in the whole mu range
w = picca.wedgize.wedge(mumin=0.,mumax=1., rtmax=200, rpmax=200, rtmin=0, rpmin=0, nrt=50, nrp=50,absoluteMu=True)
data_wedge_cf = w.wedge(da,co)
data_wedge_fit = {}
for item in toplot:
    data_wedge_fit[item] = w.wedge(files[item][fit_name+"/fit"][...],co)

# extract the correlation in wedges
w1 = picca.wedgize.wedge(mumin=0.,mumax=0.5, rtmax=200, rpmax=200, rtmin=0, rpmin=0, nrt=50, nrp=50,absoluteMu=True)
w2 = picca.wedgize.wedge(mumin=0.5,mumax=0.8, rtmax=200, rpmax=200, rtmin=0, rpmin=0, nrt=50, nrp=50,absoluteMu=True)
w3 = picca.wedgize.wedge(mumin=0.8,mumax=0.95, rtmax=200, rpmax=200, rtmin=0, rpmin=0, nrt=50, nrp=50,absoluteMu=True)
w4 = picca.wedgize.wedge(mumin=0.95,mumax=1., rtmax=200, rpmax=200, rtmin=0, rpmin=0, nrt=50, nrp=50,absoluteMu=True)
data_wedge_cf1 = w1.wedge(da,co)
data_wedge_cf2 = w2.wedge(da,co)
data_wedge_cf3 = w3.wedge(da,co)
data_wedge_cf4 = w4.wedge(da,co)
data_wedge_fit_1 = {}
data_wedge_fit_2 = {}
data_wedge_fit_3 = {}
data_wedge_fit_4 = {}
for item in toplot:
    data_wedge_fit_1[item] = w1.wedge(files[item][fit_name+"/fit"][...],co)
    data_wedge_fit_2[item] = w2.wedge(files[item][fit_name+"/fit"][...],co)
    data_wedge_fit_3[item] = w3.wedge(files[item][fit_name+"/fit"][...],co)
    data_wedge_fit_4[item] = w4.wedge(files[item][fit_name+"/fit"][...],co)

print("Plotting...")
# Plot Xi_0
fig, ax = plt.subplots()
ax.errorbar(data_wedge_cf[0], data_wedge_cf[1]*data_wedge_cf[0]**2, yerr=np.sqrt(np.diag(data_wedge_cf[2]))*data_wedge_cf[0]**2, fmt='+', color='black')
for i, item in enumerate(toplot):
    ax.plot(data_wedge_fit[item][0], data_wedge_fit[item][1]*data_wedge_fit[item][0]**2, label=labels[i], color=colors[i])
ax.legend()
ax.set_xlabel('r [Mpc/h]')
ax.grid()
ax.set_title(r'$0 < \mu < 1$')
plt.tight_layout()


# Plot wedges
fig1, ax1 = plt.subplots()
ax1.errorbar(data_wedge_cf1[0], data_wedge_cf1[1]*data_wedge_cf1[0]**2, yerr=np.sqrt(np.diag(data_wedge_cf1[2]))*data_wedge_cf1[0]**2, fmt='+', color='black')
for i, item in enumerate(toplot):
    ax1.plot(data_wedge_fit_1[item][0], data_wedge_fit_1[item][1]*data_wedge_fit_1[item][0]**2, label=labels[i], color=colors[i])
ax1.legend()
ax1.set_xlabel('r [Mpc/h]')
ax1.grid()
ax1.set_title(r'$0 < \mu < 0.5$')
plt.tight_layout()

fig2, ax2 = plt.subplots()
ax2.errorbar(data_wedge_cf2[0], data_wedge_cf2[1]*data_wedge_cf2[0]**2, yerr=np.sqrt(np.diag(data_wedge_cf2[2]))*data_wedge_cf2[0]**2, fmt='+', color='black')
for i, item in enumerate(toplot):
    ax2.plot(data_wedge_fit_2[item][0], data_wedge_fit_2[item][1]*data_wedge_fit_2[item][0]**2, label=labels[i], color=colors[i])
ax2.legend()
ax2.set_xlabel('r [Mpc/h]')
ax2.grid()
ax2.set_title(r'$0.5 < \mu < 0.8$')
plt.tight_layout()

fig3, ax3 = plt.subplots()
ax3.errorbar(data_wedge_cf3[0], data_wedge_cf3[1]*data_wedge_cf3[0]**2, yerr=np.sqrt(np.diag(data_wedge_cf3[2]))*data_wedge_cf3[0]**2, fmt='+', color='black')
for i, item in enumerate(toplot):
    ax3.plot(data_wedge_fit_3[item][0], data_wedge_fit_3[item][1]*data_wedge_fit_3[item][0]**2, label=labels[i], color=colors[i])
ax3.legend()
ax3.set_xlabel('r [Mpc/h]')
ax3.grid()
ax3.set_title(r'$0.8 < \mu < 0.95$')
plt.tight_layout()

fig4, ax4 = plt.subplots()
ax4.errorbar(data_wedge_cf4[0], data_wedge_cf4[1]*data_wedge_cf4[0]**2, yerr=np.sqrt(np.diag(data_wedge_cf4[2]))*data_wedge_cf4[0]**2, fmt='+', color='black')
for i, item in enumerate(toplot):
    ax4.plot(data_wedge_fit_4[item][0], data_wedge_fit_4[item][1]*data_wedge_fit_4[item][0]**2, label=labels[i], color=colors[i])
ax4.legend()
ax4.set_xlabel('r [Mpc/h]')
ax4.grid()
ax4.set_title(r'$0.95 < \mu < 1$')
plt.tight_layout()

plt.show()
print("Done.")

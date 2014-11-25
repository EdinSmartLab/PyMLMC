
# # # # # # # # # # # # # # # # # # # # # # # # # #
# Local configuration for Mira cluster
# BlueGene/Q @ Argonne National Laboratory
# More information: http://www.alcf.anl.gov/user-guides/blue-geneq-versus-blue-genep
#
# Jonas Sukys
# CSE Lab, ETH Zurich, Switzerland
# sukys.jonas@gmail.com
# All rights reserved.
# # # # # # # # # # # # # # # # # # # # # # # # # #

# name
name = 'Argonne Mira (BlueGene/Q)'

# Mira is a cluster
cluster = 1

# default configuration
cores     = 16
threads   = 16
walltime  = 1
memory    = 1024
rack      = 1024 # nodes

# constraints
walltime_min = 5

# simple run command
simple_job = 'runjob --np %(ranks)d -p %(tasks)d --envs OMP_NUM_THREADS=%(threads)d --verbose=INFO: %(cmd)s %(options)s'

# MPI run command
mpi_job = 'runjob --np %(ranks)d -p %(tasks)d --envs OMP_NUM_THREADS=%(threads)d --verbose=INFO: %(cmd)s %(options)s'

# batch run command
batch_job = '%(batch)s'

# submit command
# TODO: project
submit = 'qsub -A %(project)s -t=%(hours)d:%(minutes)d:00 -n %(nodes)d -O %(label)s --mode script %(xopts) %(script)s'

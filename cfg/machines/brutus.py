
# # # # # # # # # # # # # # # # # # # # # # # # # #
# Local configuration for Brutus cluster
# Intel Xeon cluster @ ETH Zurich, Switzerland
# More information: http://www.clusterwiki.ethz.ch/brutus/Brutus_wiki
# LSF job scheduling system
# For a detailed description of string mapping keys refer to documentation in 'cfg/local.txt'
#
# Jonas Sukys
# CSE Lab, ETH Zurich, Switzerland
# sukys.jonas@gmail.com
# All rights reserved.
# # # # # # # # # # # # # # # # # # # # # # # # # #

# name
name = 'ETH Brutus'

# Brutus is a cluster
cluster = 1

# default configuration
cores     = 48   # per node
threads   = 1    # per core
walltime  = 1    # hours
memory    = 1024 # GB per core
rack      = 1024 # nodes

# constraints

bootup       = 5  # minutes
min_cores    = 1
max_cores    = 2048

def min_walltime (cores):
  return 0 # hours

# could be more (7d) but then there is a limit on cores
def max_walltime (cores): # hours
  return 36

# theoretical performance figures per node
peakflops = 0.0 # TFLOP/s
bandwidth = 0.0 # GB/s

# core performance metric (normalized w.r.t. IBM BG/Q)
performance = 1

# scratch path
scratch = '/cluster/scratch_xp/public/sukysj/pymlmc'

# ensemble support
ensembles = 0

# default environment variables
envs = ''

# simple run command
simple_job = 'ulimit -c 0; export OMP_NUM_THREADS=%(threads)d; %(envs)s %(cmd)s'

# MPI run command
mpi_job = 'ulimit -c 0; %(envs)s mpirun -np %(ranks)d --npernode %(tasks)d --cpus-per-proc %(threads)d %(cmd)s'

# submission script template
script = None

# submit command
submit = 'ulimit -c 0; export OMP_NUM_THREADS=%(threads)d; bsub -n %(cores)d -R "span[ptile=%(threads)d]" -W %(hours).2d:%(minutes).2d -R "rusage[mem=%(memory)d]" -J %(label)s -oo %(reportfile)s %(xopts)s < %(jobfile)s'

# timer
timer = '(time -p (%(job)s)) 2>&1 | tee %(timerfile)s'

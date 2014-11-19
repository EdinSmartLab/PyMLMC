
# # # # # # # # # # # # # # # # # # # # # # # # # #
# Static scheduler class
# Load balancing is offloaded to the underlying job scheduling sub-system (LSF, SLURM, etc.)
# TODO: add paper, description and link           #
#                                                 #
# Jonas Sukys                                     #
# CSE Lab, ETH Zurich, Switzerland                #
# sukys.jonas@gmail.com                           #
# # # # # # # # # # # # # # # # # # # # # # # # # #

from scheduler import *
import local

class Static (Scheduler):
  
  def __init__ ( self, nodes=None, walltime=None, cores=None ):
    
    self.walltime = walltime
    self.nodes    = nodes
    self.cores    = cores
  
  def distribute (self):
    
    print
    print ' :: SCHEDULER: static'
    
    for level, type in self.levels_types:
      
      required = float(self.cores) / self.ratios [level - type]
      cores = max ( min ( local.threads, self.cores ), int ( round ( required ) ) )
      
      if cores > required:
        walltime = max ( local.walltime, self.walltime / ( cores / required ) )
      else:
        walltime = self.walltime
      
      self.parallelizations [level] [type] = Parallelization ( cores, walltime, self.sharedmem )

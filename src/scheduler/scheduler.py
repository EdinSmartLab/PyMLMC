
# # # # # # # # # # # # # # # # # # # # # # # # # #
# Scheduler base class
# TODO: add paper, description and link           #
#                                                 #
# Jonas Sukys                                     #
# CSE Lab, ETH Zurich, Switzerland                #
# sukys.jonas@gmail.com                           #
# # # # # # # # # # # # # # # # # # # # # # # # # #

import helpers
from math import modf, ceil
import local

class Parallelization (object):
  
  def __init__ (self, cores, walltime, sharedmem):
    
    # save configuration
    vars (self) .update ( locals() )
    
    # convert walltime to hours and minutes
    self.set_walltime (walltime)
    
    # if shared memory is not available, use one rank per core
    if not sharedmem:
      self.ranks   = cores
      self.threads = 1
      self.memory  = local.memory
    
    # otherwise, use one rank per node
    else:
      self.ranks   = max ( 1, cores / local.threads )
      self.threads = min ( local.threads, cores )
      self.memory  = local.memory * self.threads if local.memory else None
  
  # convert walltime to hours and minutes
  def set_walltime (self, walltime):
    
    if walltime:
      frac, whole  = modf ( walltime )
      self.hours   = int  ( whole )
      self.minutes = int  ( ceil ( 60 * frac ) )
    else:
      self.hours   = None
      self.minutes = None

class Scheduler (object):
  
  def setup (self, levels, levels_types, works, ratios, sharedmem):
    
    vars (self) .update ( locals() )
    
    self.L = len(levels) - 1
    self.parallelizations = helpers.level_type_list (levels)
    
    # if 'cores' is not provided
    if self.cores == None:

      # default value is used
      if self.nodes == None:
        self.cores = local.cores
        self.nodes = 1
      
      # or 'cores' is computed from 'nodes'
      else:
        self.cores = local.threads * self.nodes
    
    # if 'cores' is provided, 'nodes' is ignored and is computed from 'cores'
    else:
      self.nodes = max ( 1, self.cores / self.threads )
    
    # if 'walltime' is not provided, default value is used
    if self.walltime == None:
      self.walltime = local.walltime



# # # # # # # # # # # # # # # # # # # # # # # # # #
# Scheduler base class
# TODO: add paper, description and link           #
#                                                 #
# Jonas Sukys                                     #
# CSE Lab, ETH Zurich, Switzerland                #
# sukys.jonas@gmail.com                           #
# # # # # # # # # # # # # # # # # # # # # # # # # #

from parallelization import *

class Scheduler (object):

  dispatch = None
  limit    = None
  
  def setup (self, levels, levels_types, works, core_ratios, sharedmem):

    vars (self) .update ( locals() )
    if self.ratios == None:
      self.ratios = core_ratios
    
    self.L = len(levels) - 1
    self.parallelizations = helpers.level_type_list (levels)
    self.batch = helpers.level_type_list (levels)
    self.merge = helpers.level_type_list (levels)

    # if 'cores' is not provided
    if self.cores == None:

      # 'cores' is computed from 'nodes'
      if self.nodes != None:
        self.cores = local.cores * self.nodes
      
      # or 1 node is used
      else:
        self.nodes = 1
        self.cores = local.cores
    
    # if 'cores' is provided, 'nodes' is ignored and is computed from 'cores'
    else:
      self.nodes = max ( 1, self.cores / local.cores )
    
    # if 'walltime' is not provided, default value is used
    if self.walltime == None:
      self.walltime = local.walltime

    # set global walltime limit across all levels
    if self.limit == None:
      self.limit = self.walltime

    # dimensionalize work to CPU hours
    self.works = [ work * self.walltime * self.cores / float (works [self.L]) for work in works ]

  def report (self):

    print
    print ' :: SCHEDULER: %s' % self.name
    if len (self.ratios) > 1:
      print '  : Requested core ratios on each resolution level:'
      print '    %s' % str (self.ratios)
    if self.limit != None:
      print '  : Requested global walltime limit:'
      print '    %s hours' % str (self.limit)
    print '  : SPECIFICATIONS:'
    print '    Cores per node: %d' % local.cores
    print '    Threads per core: %d' % local.threads
    if local.memory:
      print '    Memory (MB) per core: %d' % local.memory
    print '  : CONSTRAINTS:'
    if local.min_cores:    print '    Min cores: %d' % local.min_cores
    if local.max_cores:    print '    Max cores: %d' % local.max_cores
    if local.min_cores:    print '    Min nodes: %d' % (local.min_cores / local.cores)
    if local.max_cores:    print '    Max nodes: %d' % (local.max_cores / local.cores)
    if local.min_walltime: print '    Min walltime (h): %s' % str(local.min_walltime ('default'))
    if local.max_walltime: print '    Max walltime (h): %s' % str(local.max_walltime ('default'))

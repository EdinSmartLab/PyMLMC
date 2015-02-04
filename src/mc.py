
# # # # # # # # # # # # # # # # # # # # # # # # # #
# General Monte Carlo (MC) classes
# TODO: add paper, description and link
#
# Jonas Sukys
# CSE Lab, ETH Zurich, Switzerland
# sukys.jonas@gmail.com
# All rights reserved.
# # # # # # # # # # # # # # # # # # # # # # # # # #

# === global imports

import os
import sys

# === local imports

from helpers import intf, pair
import local

# === classes

# configuration class for MC simulations
class MC_Config (object):
  
  def __init__ (self, mlmc_config, level, type, samples):
    vars (self) .update ( locals() )
    self.solver         = mlmc_config.solver
    self.discretization = mlmc_config.discretizations [level - type]
    self.id             = mlmc_config.id

class MC (object):
  
  # initialize MC
  def __init__ (self, config, params, parallelization):
    
    # store configuration
    vars (self) .update ( locals() )
    
    # setup parallelization based on the number of samples (affects only walltime)
    if self.parallelization:
      self.parallelization.setup ( len(config.samples) )
    
    # list of results
    self.results = [ None ] * len ( self.config.samples )
    
    # dictionary of stats
    self.stats = {}
  
  # validate all samples
  def validate (self): 
    
    self.config.solver.validate ( self.config.discretization, self.parallelization )
  
  # return the seed for the specified sample
  def seed (self, sample):
    
    return pair ( pair (self.config.level, sample), self.config.id )
  
  # return information string describing the MC run and the prescribed parallelization
  def info (self):
    
    config = self.config
    
    if self.parallelization.cores % local.cores:
      args = ( config.level, config.type, intf(len(config.samples)), intf(self.parallelization.cores/local.cores), 'nodes' )
    else:
      args = ( config.level, config.type, intf(len(config.samples)), intf(self.parallelization.cores), 'cores' )
    
    if self.parallelization.walltime:
      args += ( self.parallelization.hours, self.parallelization.minutes, self.parallelization.scope )
      return '  :  level %2d  |  type %d  |  %s sample(s)  |  %s %s  |  %2dh %2dm  |  (%s)' % args
    else:
      return '  :  level %2d  |  type %d  |  %s sample(s)  |  %s %s' % args
  
  # launch all samples
  def run (self):
    
    config = self.config
    
    # check if nothing is overwritten
    if not self.params.force:
      for sample in config.samples:
        config.solver.check ( config.level, config.type, sample )
    
    # report information of the MC run and the prescribed parallelization
    print self.info()
    
    # initialize solver
    config.solver.initialize (config.level, config.type, self.parallelization)
    
    # run all samples
    for sample in config.samples:
      config.solver.run ( config.level, config.type, sample, self.seed (sample), config.discretization, self.params, self.parallelization )
    
    # finalize solver
    config.solver.finalize (config.level, config.type, self.parallelization)
  
  # check if results are available
  def finished (self):
    
    config = self.config
    for sample in config.samples:
      if not config.solver.finished ( config.level, config.type, sample ):
        return 0
    return 1
  
  # load the results
  def load (self):
    
    config = self.config
    for i, sample in enumerate (config.samples):
      self.results [i] = config.solver.load ( config.level, config.type, sample )
  
  # assmble MC estimates
  def assemble (self, stats):
    
    self.stats = {}
    for stat in stats:
      self.stats [ stat.name ] = stat.compute_all ( self.results, self.config.solver.DataClass )
    return self.stats


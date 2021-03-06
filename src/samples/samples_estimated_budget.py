
# # # # # # # # # # # # # # # # # # # # # # # # # #
# Samples class (estimated number of samples for computational budget)
# TODO: add paper, description and link           #
#                                                 #
# Jonas Sukys                                     #
# CSE Lab, ETH Zurich, Switzerland                #
# sukys.jonas@gmail.com                           #
# # # # # # # # # # # # # # # # # # # # # # # # # #

from samples import *
import helpers
import local
import numpy
import math

# surpresses invalid division errors and simply returns 'nan' in such cases
numpy.seterr ( divide='ignore', invalid='ignore' )

# this Samples class updates the required number of samples based on the specified available computational budget

class Estimated_Budget (Samples):
  
  def __init__ (self, budget=8, warmup=1, finest='last'):
    
    # save configuration
    vars (self) .update ( locals() )
  
  def init (self):

    # set range for multiple warmup samples
    if   self.finest == 'last': self.finest = self.L
    elif self.finest == 'half': self.finest = ( self.L + 1 ) / 2
    
    # set warmup samples
    if hasattr ( self.warmup, '__iter__' ):
      counts = numpy.array ( self.warmup [0 : self.L+1] )
    
    # compute warmup samples based on works ensuring that total work does not exceed 2 * warmup * works [self.L]
    else:
      works = self.works if self.recycle else self.pairworks
      counts = numpy.array ( [ self.warmup * numpy.ceil ( float (works [self.L] / works [level]) / (2 ** (self.L - level)) ) for level in self.levels ], dtype=int )
    
    # adjust warmup samples w.r.t. set range for multiple warmup samples
    counts [0 : self.finest+1] = counts [self.L - self.finest : self.L+1]
    counts [self.finest : ]    = counts [self.L]

    self.counts.additional = counts

  def finished (self, errors):

    work = numpy.sum ( self.pairworks * self.counts.computed )
    return work >= 0.9 * self.budget

  def update (self, errors, indicators):

    # compute optimal number of samples
    # assuming that no samples were computed so far
    self.counts.optimal = self.optimal ( numpy.ones(len(self.levels)), self.budget, indicators )
    
    # compute optimal number of samples
    # assuming that self.counts.available() samples are already available on each level
    updated = self.optimal ( self.counts.available(), self.budget, indicators)
    
    # compute additional number of samples from updated
    self.counts.additional = numpy.maximum ( 0, updated - self.counts.available() )
    
    # compute overhead
    self.overhead = numpy.sum ( (self.counts.available() + self.counts.additional) * self.pairworks ) / numpy.sum ( self.counts.optimal * self.pairworks ) - 1.0

    # check if the current coarsest level is optimal
    #self.check_optimal_coarsest_level ()
    
    # check if the current finest level is optimal
    #self.check_optimal_finest_level ()

    # samples are now available
    self.available = 1

  def report_budget (self):

    print
    print ' :: BUDGET:'

    budget_used = float (sum ( [ self.pairworks [level] * self.counts.available() [level] for level in self.levels ] ))
    budget_left = float (self.budget - budget_used)
    if self.available:
      budget_reqd = float (sum ( [ self.pairworks [level] * self.counts.additional  [level] for level in self.levels ] ))

    print '  : -> Specified budget: %s CPU hours [%s NODE hours]' % (helpers.intf (numpy.ceil(self.budget), table=1), helpers.intf (numpy.ceil(self.budget/local.cores), table=1))
    print '  : -> Consumed  budget: %s CPU hours [%s NODE hours]' % (helpers.intf (numpy.ceil(budget_used), table=1), helpers.intf (numpy.ceil(budget_used/local.cores), table=1))
    print '  : -> Remaining budget: %s CPU hours [%s NODE hours]' % (helpers.intf (numpy.ceil(budget_left), table=1), helpers.intf (numpy.ceil(budget_left/local.cores), table=1))
    if self.available:
      print '  : -> Requested budget: %s CPU hours [%s NODE hours]' % (helpers.intf (numpy.ceil(budget_reqd), table=1), helpers.intf (numpy.ceil(budget_reqd/local.cores), table=1))

  def report (self):

    print
    print ' :: SAMPLES: (estimated for the specified budget)'

    # report computed and additional number of samples
    self.counts.report (self.available)

    # report budget status
    self.report_budget ()

  # query for budget
  def query (self):

    message  = 'specify the required computational budget'
    hint     = 'press ENTER to leave %s CPU hours' % helpers.intf (self.budget)
    default  = self.budget
    budget   = helpers.query (message, hint=hint, type=float, default=default, format='intf', exit=0)
    modified = budget != self.budget
    self.budget = budget
    return modified
  
  # computes the optimal number of samples if some samples are already computed
  def optimal (self, computed, budget, indicators):
    
    from numpy import sqrt, zeros, ceil
    
    updated = numpy.array ( computed, dtype=int, copy=True )

    # compute level fractions
    fractions = numpy.sqrt (indicators.variance_diff_opt ['infered'] / self.pairworks)
    
    # perform iterative optimization until valid number of samples is obtained
    optimize  = 1
    available = numpy.ones ( len (self.levels) )
    while optimize:
      
      # for the next step, by default optimization should not be needed
      optimize = 0
      
      # compute the new optimal number of samples for all levels
      # taking into account that some samples are already computed (unavailable)
      for level in self.levels:
        
        # continue if this level is not available
        if not available [level]:
          continue
        
        # compute optimal number of samples for specified level
        updated [level] = math.floor ( fractions [level] * budget / numpy.sum ( fractions * self.pairworks * available ) )
        
        # if the optimal number of samples is smaller than the already computed number of samples,
        # remove this level from the optimization problem (mark unavailable)
        if updated [level] < computed [level]:
          
          # leave the sample number unchanged
          updated [level] = computed [level]
          
          # declare this level as FIXED (no more optimization for this level)
          available [level] = 0
          
          # the remaining number of samples need to be recomputed
          optimize = 1

          # update budget
          budget -= updated [level] * self.pairworks [level]

          # restart the optimization for all levels
          break
    
    return updated

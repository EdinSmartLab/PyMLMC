
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
import numpy

# surpresses invalid division errors and simply returns 'nan' in such cases
numpy.seterr ( divide='ignore', invalid='ignore' )

# this Samples class updates the required number of samples based on the prescribed computational budget (in CPU hours)

from samples_estimated import Estimated

class Estimated_Budget (Estimated):
  
  def __init__ (self, budget=8, warmup=1, warmup_finest_level='last'):
    
    # save configuration
    vars (self) .update ( locals() )
  
  def init (self):
    
    print
    print ' :: SAMPLES: estimated for the specified budget'
    
    # default warmup samples
    if   self.warmup_finest_level == 'last': self.warmup_finest_level = self.L
    elif self.warmup_finest_level == 'half': self.warmup_finest_level = ( self.L + 1 ) / 2
    counts = numpy.array ( [ self.warmup * ( 4 ** max ( 0, self.warmup_finest_level - level) ) for level in self.levels ] )

    self.counts.computed   = numpy.zeros ( len(self.levels), dtype=int )
    self.counts.additional = numpy.array ( counts, copy=True )
    
    # set simulation type (deterministic or stochastic)
    #self.deterministic = ( self.warmup == 1 and self.L == 0 )
  
  def finished (self, errors):

    work = numpy.sum ( numpy.array(self.works) * numpy.array(self.counts.computed) )
    return work >= self.budget

  def update (self, errors, indicators):

    # check if indicators contain NaN's
    if indicators.nans: return
    
    # compute optimal number of samples
    # assuming that no samples were computed so far
    self.counts_optimal = self.optimal ( numpy.ones(len(self.levels)), self.budget, indicators )
    
    # compute optimal number of samples
    # assuming that self.counts.computed samples are already computed on each level
    self.counts_updated = self.optimal ( self.counts.computed, self.budget, indicators)
    
    # compute additional number of samples from counts_updated
    self.counts.additional = numpy.zeros ( len(self.levels), dtype=int )
    for level in self.levels:
     if self.counts_updated [level] > self.counts.computed [level]:
        self.counts.additional [level] = self.counts_updated [level] - self.counts.computed [level]

    # update counts [level] = 1 to counts [level] = 2 first, and only afterwards allow counts [level] > 2
    # this prevents assigning wrong number of samples based on _extrapolated_ indicators
    for level in self.levels:
      if self.counts.computed [level] == 1 and self.counts.additional [level] > 1:
        self.counts.additional [level] = 1;
    
    # compute optimal_work_fraction
    self.optimal_work_fraction = numpy.sum ( (self.counts.computed + self.counts.additional) * self.works ) / numpy.sum ( self.counts_optimal * self.works )
    
    # check if the current coarsest level is optimal
    #self.check_optimal_coarsest_level ()
    
    # check if the current finest level is optimal
    #self.check_optimal_finest_level ()
  
  def report (self):
    
    print
    print ' :: SAMPLES:'
    
    print '    -> Updated number of samples for each level:'
    print '      ',
    for level in self.levels:
      print '%d' % self.counts_updated [level],
    print
    
    print '    -> Additional number of samples for each level'
    print '      ',
    for level in self.levels:
      print '%d' % self.counts.additional [level],
    print
  
  # query for budget
  def query (self):
    
    print
    print ' :: QUERY: specify the required computational budget [press ENTER to leave %s CPU hours]: ' % helpers.intf (self.budget)
    budget = float ( raw_input ( '  : ' ) or str(self.budget) )
    modified = budget != self.budget
    self.budget = budget
    return modified
  
  # computes the optimal number of samples if some samples are already computed
  def optimal (self, computed, budget, indicators):
    
    from numpy import sqrt, zeros, ceil
    
    updated = numpy.array ( computed, dtype=int, copy=True )
    
    # compute the work-weighted sum of all variances
    variance_work_sum = sum ( sqrt ( [ indicators.variance_diff [level] * self.works [level] for level in self.levels ] ) )

    # perform iterative optimization until valid number of samples is obtained
    optimize = 1
    fixed = zeros (len(self.levels))
    while optimize:
      
      # for the next step, by default optimization should not be needed
      optimize = 0
      
      # compute the new required number of samples for all levels
      # taking into account that some samples are already computed
      for level in self.levels:
        
        # continue if this level is already fixed
        if fixed [level]:
          continue
        
        # compute new sample number
        updated [level] = ceil ( sqrt ( indicators.variance_diff [level] / self.works [level] ) * budget / variance_work_sum )

        # if the new sample number is smaller than the already computed sample number,
        # then remove this level from the optimization problem
        # remark: comparison must include '=' since the upper bound for optimal number of samples is used
        if updated [level] <= computed [level]:
          
          # leave the sample number unchanged
          updated [level] = computed [level]
          
          # declare this level as FIXED (no more optimization for this level)
          fixed [level] = 1
          
          # the remaining number of samples need to be recomputed
          optimize = 1
          
          # update variance_work_sum
          variance_work_sum -= sqrt ( indicators.variance_diff [level] * self.works [level] )

          # update budget
          budget -= self.works [level] * updated [level]
    
    return updated
 
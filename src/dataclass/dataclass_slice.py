
# # # # # # # # # # # # # # # # # # # # # # # # # #
# 2-D slices of multi-dimensional array-valued fields
# TODO: add paper, description and link           #
#                                                 #
# Jonas Sukys                                     #
# CSE Lab, ETH Zurich, Switzerland                #
# sukys.jonas@gmail.com                           #
# # # # # # # # # # # # # # # # # # # # # # # # # #

import numpy
from scipy import signal
import h5py
import copy, os
import linecache

class Slice (object):

  name       = 'slice'
  dimensions = 2

  def __init__ (self, qois=None, slices=1, dump=1, ranges=None, extent=[0,1], picker=None, eps=None):
    
    # save configuration
    vars (self) .update ( locals() )
    self.extent = copy.deepcopy (extent)
    
    self.filename = 'data_%06d-%s_slice%d.h5'
    self.qoinames = { 'p' : 'pressure', 'a' : 'alpha', 'm' : 'velocity', 'r' : 'density' }
    self.logsfile = 'dump.log'

    self.meta = {}
    self.data = {}

  def load (self, directory, verbosity):

    # create a copy of this class
    results = copy.deepcopy (self)

    # if picker is specified, get the dump
    if self.picker != None:
      self.dump = self.picker.pick (directory, verbosity)

    # read dump log
    step, time = self.read_dump (directory)

    # load all qois
    for qoi in self.qois:

      # single slices are loaded normally
      if not hasattr (self.slices, '__iter__'):
        filename = self.filename % ( step, self.qoinames [qoi], self.slices )
        with h5py.File ( os.path.join (directory, filename), 'r' ) as f:
          results.data [qoi] = f ['data'] [:]
      
      # for multiple specified files, compute arithmetic average
      else:
        filename = self.filename % ( step, self.qoinames [qoi], self.slices [0] )
        with h5py.File ( os.path.join (directory, filename), 'r' ) as f:
          results.data [qoi] = f ['data'] [:]
        for slice in self.slices [1:]:
          filename = self.filename % ( step, self.qoinames [qoi], slice )
          with h5py.File ( os.path.join (directory, filename), 'r' ) as f:
            results.data [qoi] += f ['data'] [:]
        results.data [qoi] /= len (self.slices)
      
      # remove trivial dimensions
      results.data [qoi] = numpy.squeeze (results.data [qoi])

      # compute magnitude of vector-valued elements
      if results.data [qoi] .ndim > 2:
        results.data [qoi] = numpy.linalg.norm (results.data [qoi], norm=2, axis=2)

      # smoothen data
      if self.eps != None:
        for qoi in self.qois:
          results.smoothen (qoi, self.eps)
    
    # load meta data
    results.meta = {}
    results.meta ['step'] = step
    results.meta ['t'] = time
    results.meta ['NX'] = results.data [qoi] .shape [0]
    results.meta ['NY'] = results.data [qoi] .shape [1]
    results.meta ['shape'] = results.data [qoi] .shape
    results.meta ['xlabel'] = 'x'
    results.meta ['ylabel'] = 'y'
    results.meta ['xrange'] = results.extent
    results.meta ['yrange'] = results.extent
    results.meta ['xunit'] = r'$mm$'
    results.meta ['yunit'] = r'$mm$'
    dx = float ( numpy.diff (results.meta ['xrange']) ) / results.meta ['NX']
    dy = float ( numpy.diff (results.meta ['yrange']) ) / results.meta ['NY']
    results.meta ['x'] = numpy.linspace (results.meta ['xrange'] [0] + 0.5 * dx, results.meta ['xrange'] [1] - 0.5 * dx, results.meta ['NX'] )
    results.meta ['y'] = numpy.linspace (results.meta ['yrange'] [0] + 0.5 * dy, results.meta ['yrange'] [1] - 0.5 * dy, results.meta ['NY'] )

    return results

  # read dump log
  def read_dump (self, directory):

    with open (os.path.join ( directory, self.logsfile ), 'r') as f:
      dumps = []
      steps = []
      times = []
      lines = f.readlines ()
      line = lines [self.dump - 1]
      entries = line.strip().split()
      step = int   ( entries [1] .split('=') [1] )
      time = float ( entries [2] .split('=') [1] )

    return step, time

  # serialized access to data
  def serialize (self, qoi):

    shape    = self.data [qoi] .shape
    elements = shape [0] * shape [1]
    size     = numpy.prod (shape) / elements
    return self.data [qoi] .reshape ( (elements, size) )
  
  # returns data for a requested qoi
  def __getitem__ (self, qoi):
    return self.data [qoi]
  
  # stores data for a requested qoi
  def __setitem__ (self, qoi, data):
    self.data [qoi] = data

  def resize (self, size):

    for key in self.data.keys():
      shape = self.data [key] .shape
      if size > 1:
        shape += tuple([size])
      self.data [key] = numpy.empty (shape)
      self.data [key] .fill (float ('nan'))

  def clip (self, range=None):

    if range:
      (lower, upper) = range
      for key in self.data.keys():
        if lower != None:
          self.data [key] = numpy.maximum ( lower, self.data [key] )
        if upper != None:
          self.data [key] = numpy.minimum ( upper, self.data [key] )

    if self.ranges and not range:
      for key in self.data.keys():
        for qoi, (lower, upper) in self.ranges.iteritems():
          if qoi in key:
            if lower != None:
              self.data [key] = numpy.maximum ( lower, self.data [key] )
            if upper != None:
              self.data [key] = numpy.minimum ( upper, self.data [key] )

  # check if the loaded result is invalid
  def invalid (self):

    for result in self.data.values():
      if numpy.isnan (result) .any() or numpy.isinf (result) .any():
        return 1

    return 0

  def smoothen (self, qoi, eps):

    length    = len (self [qoi])
    deviation = length * eps / float (self.extent [1] - self.extent [0])
    scaling   = 1.0 / float ( deviation * numpy.sqrt (2 * numpy.pi) )
    window    = 2 * deviation
    kernel    = scaling ** 2 * numpy.outer (signal.gaussian (window, deviation), signal.gaussian (window, deviation))

    self [qoi] = signal.fftconvolve (self [qoi], kernel, mode='same')
    #self [qoi] = signal.convolve (self [qoi], kernel, mode='same')

  def __rmul__ (self, a):
    result = copy.deepcopy (self)
    for key in result.data.keys():
      result.data [key] *= a
    return result

  def __lmul__ (self, a):
    return self * a

  def inplace (self, a, action):

    if self.meta ['shape'] == a.meta ['shape']:

      for key in self.data.keys():
        getattr (self.data [key], action) (a.data [key])

    if self.meta ['shape'] [0] > a.meta ['shape'] [0] and self.meta ['shape'] [1] > a.meta ['shape'] [1]:

      xfactor = self.meta ['shape'] [0] / a.meta ['shape'] [0]
      yfactor = self.meta ['shape'] [1] / a.meta ['shape'] [1]

      for key in self.data.keys():
        getattr (self.data [key], action) ( numpy.kron ( a.data [key], numpy.ones ((xfactor, yfactor)) ) )

    elif self.meta ['shape'] [0] < a.meta ['shape'] [0] and self.meta ['shape'] [1] < a.meta ['shape'] [1]:

      xfactor = a.meta ['shape'] [0] / self.meta ['shape'] [0]
      yfactor = a.meta ['shape'] [1] / self.meta ['shape'] [1]

      for key in self.data.keys():
        self.data [key] = numpy.kron ( self.data [key], numpy.ones ((xfactor, yfactor)) )
        getattr (self.data [key], action) (a.data [key])

      self.meta = copy.deepcopy (a.meta)

    else:
      print
      print ' :: ERROR [Slice.iadd]: shapes of arrays are incompatible.'
      print
      return None

    return self

  def __iadd__ (self, a):
    return self.inplace (a, '__iadd__')

  def __isub__ (self, a):
    return self.inplace (a, '__isub__')

  def __add__ (self, a):
    result = copy.deepcopy (self)
    result += a
    return result

  def __sub__ (self, a):
    result = copy.deepcopy (self)
    result -= a
    return result

  '''
  def __str__ (self):
    output = '\n' + 'meta:'
    for key in self.meta.keys():
      output += '\n %10s :%s' % ( str (key), ( '%8s' * len (self.meta [key]) ) % tuple ( [ '%1.1e' % value for value in self.meta [key] ] ) )
    output += '\n' + 'data:'
    for key in self.data.keys():
      output += '\n %10s :%s' % ( str (key), ( '%8s' * len (self.data [key]) ) % tuple ( [ '%1.1e' % value for value in self.data [key] ] ) )
    return output
  '''

class Picker (object):

  def __init__ (self, qoi):

    self.qoi = qoi

  # pick required dump
  def pick (self, directory, verbosity):

    from dataclass_series import Series
    series = Series (qois=[self.qoi], sampling=None)
    series = series.load (directory, verbosity)

    index = series [self.qoi] .argmax ()
    time  = series.meta ['t'] [index]

    dumps, steps, times = self.read_dump (directory)

    dump = dumps [ numpy.argmin ( numpy.abs (numpy.array (times) - time) ) ]

    return dump

  # read dump log
  def read_dump (self, directory):

    with open (os.path.join ( directory, 'dump.log' ), 'r') as f:
      dumps = []
      steps = []
      times = []
      for line in f.readlines ():
        entries = line.strip().split()
        dumps.append ( int   ( entries [0] .split('=') [1] ) )
        steps.append ( int   ( entries [1] .split('=') [1] ) )
        times.append ( float ( entries [2] .split('=') [1] ) )

    return dumps, steps, times

def get_max (params):

  dataclass, qoi, slices, dump, directory, verbosity, eps = params

  results = dataclass (qois = [qoi], slices = slices, dump = dump)
  results = results.load (directory, verbosity)
  results.smoothen (qoi, eps)
  return numpy.max (results [qoi])

class Smooth_Picker (Picker):

  def __init__ (self, qoi, slices, eps=None, dataclass=Slice):

    self.qoi       = qoi
    self.slices    = slices
    self.eps       = eps
    self.dataclass = dataclass
    self.cachefile = 'picker_%s_%.1f.cache' % (dataclass.name, eps)

  # pick required dump
  def pick (self, directory, verbosity):

    # laod cached dump, if exists
    if os.path.exists ( os.path.join (directory, self.cachefile) ):
      with open ( os.path.join (directory, self.cachefile), 'r' ) as f:
        return int ( f.readlines () [0] .strip () )

    # pick the specified dump

    import scipy

    dumps, steps, times = self.read_dump (directory)

    tasks = []
    for idx, dump in enumerate (dumps):
      tasks.append ( (self.dataclass, self.qoi, self.slices, dump, directory, verbosity, self.eps) )

    import multiprocessing
    if self.dataclass.dimensions == 1:
      workers = None
    else:
      workers = 1
    pool = multiprocessing.Pool (workers)
    max = pool.map (get_max, tasks)

    '''
    max = numpy.empty (len (dumps))
    for idx, dump in enumerate (dumps):

      results = self.dataclass (qois = [self.qoi], slices = self.slices, dump = dump)
      results = results.load (directory, verbosity)
      results.smoothen (self.qoi, self.eps)
      max [idx] = numpy.max (results [self.qoi])
    '''

    dump = dumps [ numpy.argmax (max) ]

    # cache dump for future reuse
    with open ( os.path.join (directory, self.cachefile), 'w' ) as f:
      f.write ( str (dump) )

    return dump


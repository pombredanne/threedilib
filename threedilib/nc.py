import netCDF4
import numpy


class Data(object):

    def __init__(self, datafile, step_divider=1, gridsize=None):
        ds = netCDF4.Dataset(datafile, 'r', format='NETCDF4')

        self.ds = ds

        # Data
        self.level = ds.variables['s1']
        self.depth = ds.variables['dep']
        self.time = ds.variables['time']

        # Corner points of the quadtrees
        self.x0 = ds.variables['FlowElemContour_x'][:].min(1)
        self.x1 = ds.variables['FlowElemContour_x'][:].max(1)
        self.y0 = ds.variables['FlowElemContour_y'][:].min(1)
        self.y1 = ds.variables['FlowElemContour_y'][:].max(1)

        # Center points of the quadtrees
        self.x = ds.variables['FlowElem_xcc'][:]
        self.y = ds.variables['FlowElem_ycc'][:]

        # Master contour
        self.X0 = self.x0.min() // 1000 * 1000
        self.X1 = numpy.ceil(self.x1.max() / 1000.) * 1000
        self.Y0 = self.y0.min() // 1250 * 1250
        self.Y1 = numpy.ceil(self.y1.max() / 1250.) * 1250

        # Grid steps
        if gridsize is None:
            print 'native gridsize x: %d' % (self.x1 - self.x0).min()
            print 'native gridsize y: %d' % (self.y1 - self.y0).min()
            self.XS = (self.x1 - self.x0).min() / step_divider
            self.YS = (self.y1 - self.y0).min() / step_divider
        else:
            self.XS = gridsize
            self.YS = gridsize

        # Grid size
        self.NY = (self.Y1 - self.Y0) / self.YS
        self.NX = (self.X1 - self.X0) / self.XS

        # Geotransform
        self.geotransform = (
            self.X0 + self.XS / 2.,
            self.XS,
            0,
            self.Y1 - self.YS / 2.,
            0,
            -self.YS,
        )

        self.num_timesteps, self.num_elements = self.depth.shape

    def to_index(self, x0, x1, y0, y1):
        """
        Return tuple of array indexes, ready for indexing master array
        """
        i = numpy.arange(
            (self.Y1 - y1) / self.YS,
            (self.Y1 - y0) / self.YS,
            dtype=numpy.int64,
        )
        j = numpy.arange(
            (x0 - self.X0) / self.XS,
            (x1 - self.X0) / self.XS,
            dtype=numpy.int64,
        )
        index = (
            (i * numpy.ones((j.size,1),
                            dtype=numpy.int64)).transpose().reshape(-1),
            (j * numpy.ones((i.size,1),
                            dtype=numpy.int64)).reshape(-1),
        )
        return index

    def to_masked_array(self, variable, i):
        """
        i.e. variable = data.depth, i is the timestep.
        """
        variable_i = variable[i]
        result = numpy.ma.zeros((self.NY, self.NX), fill_value=-999)
        result.mask = True
        count = 0
        for j in xrange(variable.shape[1]):
            count += 1
            # if count % 10000 == 0:
            #     print(count)
            index = self.to_index(
                self.x0[j],
                self.x1[j],
                self.y0[j],
                self.y1[j],
            )
            result[index] = variable_i[j]
        return result

#
# FitsImageCanvasGtk.py -- A FITS image widget with canvas drawing in Gtk
# 
# Eric Jeschke (eric@naoj.org)
#
# Copyright (c) Eric R. Jeschke.  All rights reserved.
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.txt for details.
#
from ginga import FitsImage
from ginga import Mixins
from ginga.gtkw import FitsImageGtk
from ginga.gtkw.FitsImageCanvasTypesGtk import *

    
class FitsImageCanvasError(FitsImageGtk.FitsImageGtkError):
    pass

class FitsImageCanvas(FitsImageGtk.FitsImageZoom,
                      DrawingMixin, CanvasMixin, CompoundMixin):

    def __init__(self, logger=None, rgbmap=None, settings=None,
                 bindmap=None, bindings=None):
        FitsImageGtk.FitsImageZoom.__init__(self, logger=logger,
                                            rgbmap=rgbmap,
                                            settings=settings,
                                            bindmap=bindmap,
                                            bindings=bindings)
        CompoundMixin.__init__(self)
        CanvasMixin.__init__(self)
        DrawingMixin.__init__(self, drawCatalog)

        self.setSurface(self)
        self.ui_setActive(True)

    def canvascoords(self, data_x, data_y, center=True):
        # data->canvas space coordinate conversion
        x, y = self.get_canvas_xy(data_x, data_y, center=center)
        return (x, y)

    def redraw_data(self, whence=0):
        super(FitsImageCanvas, self).redraw_data(whence=whence)

        if not self.surface:
            return
        self.draw()


#END

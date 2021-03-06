#
# Pick.py -- Pick plugin for Ginga fits viewer
# 
# Eric Jeschke (eric@naoj.org)
#
# Copyright (c) Eric R. Jeschke.  All rights reserved.
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.txt for details.
#
import gtk
from ginga.gtkw import GtkHelp
from ginga import iqcalc
from ginga.misc.plugins import PickBase

try:
    import matplotlib
    matplotlib.use('GTKCairo')
    from  matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo \
         as FigureCanvas
    have_mpl = True
except ImportError:
    have_mpl = False

from ginga.gtkw import FitsImageCanvasGtk


class Pick(PickBase.PickBase):

    def __init__(self, fv, fitsimage):
        # superclass defines some variables for us, like logger
        super(Pick, self).__init__(fv, fitsimage)

        self.w.tooltips = self.fv.w.tooltips
        self.have_mpl = have_mpl

    def build_gui(self, container):
        assert iqcalc.have_scipy == True, \
               Exception("Please install python-scipy to use this plugin")
        
        self.pickcenter = None

        vpaned = gtk.VPaned()

        nb = gtk.Notebook()
        #nb.set_group_id(group)
        #nb.connect("create-window", self.detach_page, group)
        nb.set_tab_pos(gtk.POS_RIGHT)
        nb.set_scrollable(True)
        nb.set_show_tabs(True)
        nb.set_show_border(False)
        self.w.nb1 = nb
        vpaned.pack1(nb, resize=True, shrink=True)
        
        cm, im = self.fv.cm, self.fv.im

        di = FitsImageCanvasGtk.FitsImageCanvas(logger=self.logger)
        di.enable_autozoom('off')
        di.enable_autocuts('off')
        di.zoom_to(3, redraw=False)
        settings = di.get_settings()
        settings.getSetting('zoomlevel').add_callback('set',
                               self.zoomset, di)
        di.set_cmap(cm, redraw=False)
        di.set_imap(im, redraw=False)
        di.set_callback('none-move', self.detailxy)
        di.set_bg(0.4, 0.4, 0.4)
        self.pickimage = di

        bd = di.get_bindings()
        bd.enable_pan(True)
        bd.enable_zoom(True)
        bd.enable_cuts(True)

        iw = di.get_widget()
        width, height = 200, 200
        iw.set_size_request(width, height)
        label = gtk.Label('Image')
        label.show()
        nb.append_page(iw, label)
        nb.set_tab_reorderable(iw, True)
        #nb.set_tab_detachable(iw, True)

        if have_mpl:
            self.w.fig = matplotlib.figure.Figure()
            self.w.ax = self.w.fig.add_subplot(111, axisbg='black')
            self.w.ax.set_aspect('equal', adjustable='box')
            self.w.ax.set_title('Contours')
            #self.w.ax.grid(True)
            canvas = FigureCanvas(self.w.fig)
            #canvas.set_size_request(width, height)
            self.w.canvas = canvas
            self.w.canvas.show_all()
            canvas.connect("scroll_event", self.plot_scroll)
            #canvas.connect("key_press_event", self.pan_plot)
            canvas.connect("motion_notify_event", self.plot_motion_notify)
            canvas.connect("button_press_event", self.plot_button_press)
            canvas.connect("button_release_event", self.plot_button_release)

            label = gtk.Label('Contour')
            label.show()
            nb.append_page(canvas, label)
            nb.set_tab_reorderable(canvas, True)
            #nb.set_tab_detachable(canvas, True)

            self.w.fig2 = matplotlib.figure.Figure()
            self.w.ax2 = self.w.fig2.add_subplot(111, axisbg='white')
            #self.w.ax2.set_aspect('equal', adjustable='box')
            self.w.ax2.set_ylabel('brightness')
            self.w.ax2.set_xlabel('pixels')
            self.w.ax2.set_title('FWHM')
            self.w.ax.grid(True)
            canvas = FigureCanvas(self.w.fig2)
            #canvas.set_size_request(width, height)
            self.w.canvas2 = canvas
            self.w.canvas2.show_all()

            label = gtk.Label('FWHM')
            label.show()
            nb.append_page(canvas, label)
            nb.set_tab_reorderable(canvas, True)
            #nb.set_tab_detachable(canvas, True)

        sw = gtk.ScrolledWindow()
        sw.set_border_width(2)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        vbox = gtk.VBox()
        sw.add_with_viewport(vbox)

        self.msgFont = self.fv.getFont("sansFont", 14)
        tw = gtk.TextView()
        tw.set_wrap_mode(gtk.WRAP_WORD)
        tw.set_left_margin(4)
        tw.set_right_margin(4)
        tw.set_editable(False)
        tw.set_left_margin(4)
        tw.set_right_margin(4)
        tw.modify_font(self.msgFont)
        self.tw = tw

        fr = gtk.Frame(" Instructions ")
        fr.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        fr.set_label_align(0.1, 0.5)
        fr.add(tw)
        vbox.pack_start(fr, padding=4, fill=True, expand=False)
        
        fr = gtk.Frame(" Pick ")
        fr.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        fr.set_label_align(0.1, 0.5)

        nb = gtk.Notebook()
        #nb.set_group_id(group)
        #nb.connect("create-window", self.detach_page, group)
        nb.set_tab_pos(gtk.POS_BOTTOM)
        nb.set_scrollable(True)
        nb.set_show_tabs(True)
        nb.set_show_border(False)
        self.w.nb2 = nb
        fr.add(nb)
        vbox.pack_start(fr, padding=4, fill=True, expand=False)

        # Build report panel
        captions = (('Zoom', 'label', 'Contour Zoom', 'label'),
            ('Object_X', 'label', 'Object_Y', 'label'),
            ('RA', 'label', 'DEC', 'label'),
            ('Equinox', 'label', 'Background', 'label'),
            ('Sky Level', 'label', 'Brightness', 'label'), 
            ('FWHM X', 'label', 'FWHM Y', 'label'),
            ('FWHM', 'label', 'Star Size', 'label'),
            ('Sample Area', 'label', 'Default Region', 'button'),
            )

        w, b = GtkHelp.build_info(captions)
        self.w.update(b)
        b.zoom.set_text(self.fv.scale2text(di.get_scale()))
        self.wdetail = b
        b.default_region.connect('clicked', lambda w: self.reset_region())
        self.w.tooltips.set_tip(b.default_region,
                                   "Reset region size to default")

        # Pick field evaluation status
        label = gtk.Label()
        label.set_alignment(0.05, 0.5)
        self.w.eval_status = label
        w.pack_start(self.w.eval_status, fill=False, expand=False, padding=2)

        # Pick field evaluation progress bar and stop button
        hbox = gtk.HBox()
        btn = gtk.Button("Stop")
        btn.connect('clicked', lambda w: self.eval_intr())
        btn.set_sensitive(False)
        self.w.btn_intr_eval = btn
        hbox.pack_end(btn, fill=False, expand=False, padding=2)
        self.w.eval_pgs = gtk.ProgressBar()
        # GTK3
        #self.w.eval_pgs.set_orientation(gtk.ORIENTATION_HORIZONTAL)
        #self.w.eval_pgs.set_inverted(False)
        hbox.pack_start(self.w.eval_pgs, fill=True, expand=True, padding=4)
        w.pack_start(hbox, fill=False, expand=False, padding=2)
        
        label = gtk.Label("Report")
        label.show()
        nb.append_page(w, label)
        nb.set_tab_reorderable(w, True)
        #nb.set_tab_detachable(w, True)

        # Build settings panel
        captions = (('Show Candidates', 'checkbutton'),
                    ('Radius', 'xlabel', '@Radius', 'spinbutton'),
                    ('Threshold', 'xlabel', '@Threshold', 'entry'),
                    ('Min FWHM', 'xlabel', '@Min FWHM', 'spinbutton'),
                    ('Max FWHM', 'xlabel', '@Max FWHM', 'spinbutton'),
                    ('Ellipticity', 'xlabel', '@Ellipticity', 'entry'),
                    ('Edge', 'xlabel', '@Edge', 'entry'),
                    ('Max side', 'xlabel', '@Max side', 'spinbutton'),
                    ('Redo Pick', 'button'),
                    )

        w, b = GtkHelp.build_info(captions)
        self.w.update(b)
        self.w.tooltips.set_tip(b.radius, "Radius for peak detection")
        self.w.tooltips.set_tip(b.threshold, "Threshold for peak detection (blank=default)")
        self.w.tooltips.set_tip(b.min_fwhm, "Minimum FWHM for selection")
        self.w.tooltips.set_tip(b.max_fwhm, "Maximum FWHM for selection")
        self.w.tooltips.set_tip(b.ellipticity, "Minimum ellipticity for selection")
        self.w.tooltips.set_tip(b.edge, "Minimum edge distance for selection")
        self.w.tooltips.set_tip(b.show_candidates,
                                "Show all peak candidates")
        # radius control
        adj = b.radius.get_adjustment()
        b.radius.set_digits(2)
        b.radius.set_numeric(True)
        adj.configure(self.radius, 5.0, 200.0, 1.0, 10.0, 0)
        def chg_radius(w):
            self.radius = float(w.get_text())
            self.w.xlbl_radius.set_text(str(self.radius))
            return True
        b.xlbl_radius.set_text(str(self.radius))
        b.radius.connect('value-changed', chg_radius)

        # threshold control
        def chg_threshold(w):
            threshold = None
            ths = w.get_text().strip()
            if len(ths) > 0:
                threshold = float(ths)
            self.threshold = threshold
            self.w.xlbl_threshold.set_text(str(self.threshold))
            return True
        b.xlbl_threshold.set_text(str(self.threshold))
        b.threshold.connect('activate', chg_threshold)

        # min fwhm
        adj = b.min_fwhm.get_adjustment()
        b.min_fwhm.set_digits(2)
        b.min_fwhm.set_numeric(True)
        adj.configure(self.min_fwhm, 0.1, 200.0, 0.1, 1, 0)
        def chg_min(w):
            self.min_fwhm = w.get_value()
            self.w.xlbl_min_fwhm.set_text(str(self.min_fwhm))
            return True
        b.xlbl_min_fwhm.set_text(str(self.min_fwhm))
        b.min_fwhm.connect('value-changed', chg_min)

        # max fwhm
        adj = b.max_fwhm.get_adjustment()
        b.max_fwhm.set_digits(2)
        b.max_fwhm.set_numeric(True)
        adj.configure(self.max_fwhm, 0.1, 200.0, 0.1, 1, 0)
        def chg_max(w):
            self.max_fwhm = w.get_value()
            self.w.xlbl_max_fwhm.set_text(str(self.max_fwhm))
            return True
        b.xlbl_max_fwhm.set_text(str(self.max_fwhm))
        b.max_fwhm.connect('value-changed', chg_max)

        # Ellipticity control
        def chg_ellipticity(w):
            minellipse = None
            val = w.get_text().strip()
            if len(val) > 0:
                minellipse = float(val)
            self.min_ellipse = minellipse
            self.w.xlbl_ellipticity.set_text(str(self.min_ellipse))
            return True
        b.xlbl_ellipticity.set_text(str(self.min_ellipse))
        b.ellipticity.connect('activate', chg_ellipticity)

        # Edge control
        def chg_edgew(w):
            edgew = None
            val = w.get_text().strip()
            if len(val) > 0:
                edgew = float(val)
            self.edgew = edgew
            self.w.xlbl_edge.set_text(str(self.edgew))
            return True
        b.xlbl_edge.set_text(str(self.edgew))
        b.edge.connect('activate', chg_edgew)

        adj = b.max_side.get_adjustment()
        b.max_side.set_digits(0)
        b.max_side.set_numeric(True)
        adj.configure(self.max_side, 5, 10000, 10, 100, 0)
        def chg_max_side(w):
            self.max_side = int(w.get_value())
            self.w.xlbl_max_side.set_text(str(self.max_side))
            return True
        b.xlbl_max_side.set_text(str(self.max_side))
        b.max_side.connect('value-changed', chg_max_side)

        b.redo_pick.connect('clicked', lambda w: self.redo())
        b.show_candidates.set_active(self.show_candidates)
        b.show_candidates.connect('toggled', self.show_candidates_cb)

        label = gtk.Label("Settings")
        label.show()
        nb.append_page(w, label)
        nb.set_tab_reorderable(w, True)
        #nb.set_tab_detachable(w, True)

        # Build controls panel
        captions = (
            ('Sky cut', 'button', 'Delta sky', 'xlabel', '@Delta sky', 'entry'),
            ('Bright cut', 'button', 'Delta bright', 'xlabel', '@Delta bright', 'entry'),
            )

        w, b = GtkHelp.build_info(captions)
        self.w.update(b)
        self.w.tooltips.set_tip(b.sky_cut, "Set image low cut to Sky Level")
        self.w.tooltips.set_tip(b.delta_sky, "Delta to apply to low cut")
        self.w.tooltips.set_tip(b.bright_cut,
                                "Set image high cut to Sky Level+Brightness")
        self.w.tooltips.set_tip(b.delta_bright, "Delta to apply to high cut")

        b.sky_cut.set_sensitive(False)
        self.w.btn_sky_cut = b.sky_cut
        self.w.btn_sky_cut.connect('clicked', lambda w: self.sky_cut())
        self.w.sky_cut_delta = b.delta_sky
        b.xlbl_delta_sky.set_text(str(self.delta_sky))
        b.delta_sky.set_text(str(self.delta_sky))
        def chg_delta_sky(w):
            delta_sky = 0.0
            val = w.get_text().strip()
            if len(val) > 0:
                delta_sky = float(val)
            self.delta_sky = delta_sky
            self.w.xlbl_delta_sky.set_text(str(self.delta_sky))
            return True
        b.delta_sky.connect('activate', chg_delta_sky)
        
        b.bright_cut.set_sensitive(False)
        self.w.btn_bright_cut = b.bright_cut
        self.w.btn_bright_cut.connect('clicked', lambda w: self.bright_cut())
        self.w.bright_cut_delta = b.delta_bright
        b.xlbl_delta_bright.set_text(str(self.delta_bright))
        b.delta_bright.set_text(str(self.delta_bright))
        def chg_delta_bright(w):
            delta_bright = 0.0
            val = w.get_text().strip()
            if len(val) > 0:
                delta_bright = float(val)
            self.delta_bright = delta_bright
            self.w.xlbl_delta_bright.set_text(str(self.delta_bright))
            return True
        b.delta_bright.connect('activate', chg_delta_bright)

        label = gtk.Label("Controls")
        label.show()
        nb.append_page(w, label)
        nb.set_tab_reorderable(w, True)
        #nb.set_tab_detachable(w, True)

        btns = gtk.HButtonBox()
        btns.set_layout(gtk.BUTTONBOX_START)
        btns.set_spacing(3)
        btns.set_child_size(15, -1)

        btn = gtk.Button("Close")
        btn.connect('clicked', lambda w: self.close())
        btns.add(btn)
        vbox.pack_start(btns, padding=4, fill=True, expand=False)

        vpaned.pack2(sw, resize=True, shrink=True)
        vpaned.set_position(280)
        vpaned.show_all()
        
        container.pack_start(vpaned, padding=0, fill=True, expand=True)

    def _setText(self, w, text):
        w.set_text(text)
        
    def _setEnabled(self, w, tf):
        w.set_sensitive(tf)
        
    def instructions(self):
        buf = self.tw.get_buffer()
        buf.set_text("""Left-click to place region.  Left-drag to position region.  Redraw region with the right mouse button.""")
        self.tw.modify_font(self.msgFont)
            
    def update_status(self, text):
        self.fv.gui_do(self.w.eval_status.set_text, text)

    def init_progress(self):
        self.w.btn_intr_eval.set_sensitive(True)
        self.w.eval_pgs.set_fraction(0.0)
        self.w.eval_pgs.set_text("%.2f %%" % (0.0))
            
    def update_progress(self, pct):
        self.w.eval_pgs.set_fraction(pct)
        self.w.eval_pgs.set_text("%.2f %%" % (pct*100.0))
        
    def show_candidates_cb(self, w):
        self.show_candidates = w.get_active()
        if not self.show_candidates:
            # Delete previous peak marks
            objs = self.fitsimage.getObjectsByTagpfx('peak')
            self.fitsimage.deleteObjects(objs, redraw=True)
        
    def plot_scroll(self, widget, event):
        # event.button, event.x, event.y
        x = event.x; y = event.y
        if event.direction == gtk.gdk.SCROLL_UP:
            #delta = 0.9
            self.plot_zoomlevel += 1.0
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            #delta = 1.1
            self.plot_zoomlevel -= 1.0

        self.plot_panzoom()
        
        # x1, x2 = self.w.ax.get_xlim()
        # y1, y2 = self.w.ax.get_ylim()
        # self.w.ax.set_xlim(x1*delta, x2*delta)
        # self.w.ax.set_ylim(y1*delta, y2*delta)
        # self.w.canvas.draw()
        
    def plot_button_press(self, widget, event):
        # event.button, event.x, event.y
        x = event.x; y = event.y
        button = 0
        if event.button != 0:
            button |= 0x1 << (event.button - 1)
        self.logger.debug("button event at %dx%d, button=%x" % (x, y, button))

        self.plot_x, self.plot_y = x, y
        return True

    def plot_button_release(self, widget, event):
        # event.button, event.x, event.y
        x = event.x; y = event.y
        button = 0
        if event.button != 0:
            button |= 0x1 << (event.button - 1)
        self.logger.debug("button release at %dx%d button=%x" % (x, y, button))
            

    def plot_motion_notify(self, widget, event):
        button = 0
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x, y, state = event.x, event.y, event.state
        
        if state & gtk.gdk.BUTTON1_MASK:
            button |= 0x1
        elif state & gtk.gdk.BUTTON2_MASK:
            button |= 0x2
        elif state & gtk.gdk.BUTTON3_MASK:
            button |= 0x4
        # self.logger.debug("motion event at %dx%d, button=%x" % (x, y, button))

        if button & 0x1:
            xdelta = x - self.plot_x
            ydelta = y - self.plot_y
            self.pan_plot(xdelta, ydelta)
            

    def __str__(self):
        return 'pick'
    
#END

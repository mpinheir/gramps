#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2003-2006  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
# Copyright (C) 2010       Jakim Friant
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id$

"""
Show uncollected objects in a window.
"""

#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------
import sys
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.get_translation().gettext
from gramps.gen.config import config
if config.get('preferences.use-bsddb3') or sys.version_info[0] >= 3:
    from bsddb3.db import DBError
else:
    from bsddb.db import DBError

#------------------------------------------------------------------------
#
# GNOME/GTK modules
#
#------------------------------------------------------------------------
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
import gc

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from gramps.gui.plug import tool
from gramps.gui.managedwindow import ManagedWindow
from gramps.gui.dialog import InfoDialog
from gramps.gui.glade import Glade
from gramps.gui.utils import is_right_click

#-------------------------------------------------------------------------
#
# Actual tool
#
#-------------------------------------------------------------------------
class Leak(tool.Tool, ManagedWindow):
    def __init__(self,dbstate, uistate, options_class, name, callback=None):
        self.title = _('Uncollected Objects Tool')

        tool.Tool.__init__(self,dbstate, options_class, name)
        ManagedWindow.__init__(self,uistate,[],self.__class__)

        self.glade = Glade()

        self.window = self.glade.toplevel
        self.scroll = self.glade.get_object("scrolledwindow1")
        #add a listview to the scrollable
        self.list = Gtk.TreeView()
        self.list.set_headers_visible(True)
        self.list.connect('button-press-event', self._button_press)
        self.scroll.add(self.list)
        #make a model
        self.modeldata = []
        self.model = Gtk.ListStore(int, str)
        self.list.set_model(self.model)
        
        #set the colums
        self.renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_('Number'), self.renderer, text=0)
        column.set_resizable(True)
        column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.list.append_column(column)
        column = Gtk.TreeViewColumn(_('Uncollected object'), self.renderer,
                                    text=1)
        column.set_resizable(True)
        column.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        self.list.append_column(column)
        self.selection = self.list.get_selection()
        
        flags = gc.DEBUG_UNCOLLECTABLE|gc.DEBUG_SAVEALL
        if hasattr(gc, "DEBUG_OBJECTS"):
            flags = flags | gc.DEBUG_OBJECTS
        gc.set_debug(flags)

        self.set_window(self.window, self.glade.get_object('title'),
                        self.title)

        self.glade.connect_signals({
            "on_apply_clicked" : self.apply_clicked,
            "on_close_clicked" : self.close,
            "on_delete_event"  : self.close,
            })
        self.display()
        self.show()

    def build_menu_names(self, obj):
        return (self.title,None)

    def _button_press(self, obj, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS and event.button == 1:
            self.referenced_in()
            return True
        elif is_right_click(event):
            self.refers_to()
            return True

    def referenced_in(self):
        model, iter = self.selection.get_selected()
        if iter is not None:
            count = model.get_value(iter, 0)
            referrers = gc.get_referrers(self.modeldata[count])
            text = ""
            for referrer in referrers:
                try:
                    text += str(referrer) + '\n'
                except ReferenceError:
                    pass
            InfoDialog(_('Referrers of %d') % count, text, 
                        parent=self.window)

    def refers_to(self):
        model, iter = self.selection.get_selected()
        if iter is not None:
            count = model.get_value(iter, 0)
            referents = gc.get_referents(self.modeldata[count])
            text = ""
            for referent in referents:
                try:
                    text += str(referent) + '\n'
                except ReferenceError:
                    pass
            InfoDialog(_('%d refers to') % count, text, 
                        parent=self.window)

    def display(self):
        gc.collect(2)
        self.model.clear()
        count = 0
        if len(gc.garbage):
            for each in gc.garbage:
                try:
                    self.modeldata.append(each)
                    self.model.append((count, str(each)))
                except DBError:
                    self.modeldata.append(each)
                    self.model.append((count, 'db.DB instance at %s' % id(each)))
                except ReferenceError:
                    pass
                count += 1
        self.glade.get_object('label2').set_text(_('Uncollected Objects: %s') % str(len(gc.garbage)))

    def apply_clicked(self, obj):
        self.display()
        
#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class LeakOptions(tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self, name,person_id=None):
        tool.ToolOptions.__init__(self, name,person_id)

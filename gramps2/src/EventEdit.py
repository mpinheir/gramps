#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2004  Donald N. Allingham
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

from string import strip

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk
import gtk.glade
import gnome

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import Sources
import Witness
import const
import Utils
import GrampsCfg
import AutoComp
import Calendar
import RelLib
import Date

from DateEdit import DateEdit
from gettext import gettext as _

from QuestionDialog import WarningDialog
#-------------------------------------------------------------------------
#
# EventEditor class
#
#-------------------------------------------------------------------------
class EventEditor:

    def __init__(self,parent,name,list,trans,event,def_placename,read_only,cb,
                 def_event=None):
        self.parent = parent
        self.db = self.parent.db
        if event:
            if self.parent.child_windows.has_key(event.get_id()):
                self.parent.child_windows[event.get_id()].present(None)
                return
            else:
                self.win_key = event.get_id()
        else:
            self.win_key = self
        self.event = event
        self.child_windows = {}
        self.trans = trans
        self.callback = cb
        self.plist = []
        self.pmap = {}
        self.elist = list

        for key in self.parent.db.get_place_id_keys():
            p = self.parent.db.get_place_display(key)
            self.pmap[p[0]] = key

        if event:
            self.srcreflist = self.event.get_source_references()
            self.witnesslist = self.event.get_witness_list()
            if not self.witnesslist:
                self.witnesslist = []
            self.date = Date.Date(self.event.get_date_object())
            transname = const.display_event(event.get_name())
            # add the name to the list if it is not already there. This tends to occur
            # in translated languages with the 'Death' event, which is a partial match
            # to other events
            if not transname in list:
                list.append(transname)
        else:
            self.srcreflist = []
            self.witnesslist = []
            self.date = Date.Date(None)

        self.top = gtk.glade.XML(const.dialogFile, "event_edit","gramps")

        self.window = self.top.get_widget("event_edit")
        title_label = self.top.get_widget('title')

        if name == ", ":
            etitle = _('Event Editor')
        else:
            etitle = _('Event Editor for %s') % name

        Utils.set_titles(self.window,title_label, etitle,
                         _('Event Editor'))
        
        self.name_field  = self.top.get_widget("eventName")
        self.place_field = self.top.get_widget("eventPlace")
        self.cause_field = self.top.get_widget("eventCause")
        self.slist = self.top.get_widget("slist")
        self.wlist = self.top.get_widget("wlist")
        self.place_combo = self.top.get_widget("eventPlace_combo")
        self.date_field  = self.top.get_widget("eventDate")
        self.cause_field  = self.top.get_widget("eventCause")
        self.descr_field = self.top.get_widget("event_description")
        self.note_field = self.top.get_widget("eventNote")
        self.event_menu = self.top.get_widget("personalEvents")
        self.priv = self.top.get_widget("priv")
        self.calendar = self.top.get_widget("calendar")
        self.sources_label = self.top.get_widget("sourcesEvent")
        self.notes_label = self.top.get_widget("notesEvent")
        self.flowed = self.top.get_widget("eventflowed")
        self.preform = self.top.get_widget("eventpreform")
        self.witnesses_label = self.top.get_widget("witnessesEvent")

        if GrampsCfg.calendar:
            self.calendar.show()
        else:
            self.calendar.hide()
        
        if read_only:
            self.event_menu.set_sensitive(0)
            self.date_field.grab_focus()

        self.sourcetab = Sources.SourceTab(self.srcreflist,self,
                                           self.top,self.window,self.slist,
                                           self.top.get_widget('add_src'),
                                           self.top.get_widget('edit_src'),
                                           self.top.get_widget('del_src'))

        self.witnesstab = Witness.WitnessTab(self.witnesslist,self,
                                           self.top,self.window,self.wlist,
                                           self.top.get_widget('add_witness'),
                                           self.top.get_widget('edit_witness'),
                                           self.top.get_widget('del_witness'))

        AutoComp.AutoCombo(self.event_menu,list)
        AutoComp.AutoEntry(self.place_field,self.pmap.keys())

        if event != None:
            self.name_field.set_text(transname)
            if (def_placename):
                self.place_field.set_text(def_placename)
            else:
                place_id = event.get_place_id()
                if place_id:
                    place_name = u""
                else:
                    place_name = self.db.find_place_from_id(place_id).get_title()
                self.place_field.set_text(place_name)

            self.date_field.set_text(self.date.get_date())
            self.cause_field.set_text(event.get_cause())
            self.descr_field.set_text(event.get_description())
            self.priv.set_active(event.get_privacy())
            
            self.note_field.get_buffer().set_text(event.get_note())
            if event.get_note():
            	self.note_field.get_buffer().set_text(event.get_note())
                Utils.bold_label(self.notes_label)
            	if event.get_note_format() == 1:
                    self.preform.set_active(1)
            	else:
                    self.flowed.set_active(1)
        else:
            if def_event:
                self.name_field.set_text(def_event)
            if def_placename:
                self.place_field.set_text(def_placename)
        self.date_check = DateEdit(self.date_field,self.top.get_widget("date_stat"))

        self.top.signal_autoconnect({
            "on_switch_page" : self.on_switch_page,
            "on_help_event_clicked" : self.on_help_clicked,
            "on_ok_event_clicked" : self.on_event_edit_ok_clicked,
            "on_cancel_event_clicked" : self.close,
            "on_event_edit_delete_event" : self.on_delete_event,
            })

        menu = gtk.Menu()
        index = 0
        for cobj in Calendar.calendar_names():
            item = gtk.MenuItem(cobj.TNAME)
            item.set_data("d",cobj)
            item.connect("activate",self.on_menu_changed)
            item.show()
            menu.append(item)
            if self.date.get_calendar().NAME == cobj.NAME:
                menu.set_active(index)
                self.date_check.set_calendar(cobj())
            index = index + 1
        self.calendar.set_menu(menu)

        self.window.set_transient_for(self.parent.window)
        self.add_itself_to_menu()
        self.window.show()

    def on_delete_event(self,obj,b):
        self.close_child_windows()
        self.remove_itself_from_menu()

    def close(self,obj):
        self.close_child_windows()
        self.remove_itself_from_menu()
        self.window.destroy()

    def close_child_windows(self):
        for child_window in self.child_windows.values():
            child_window.close(None)
        self.child_windows = {}

    def add_itself_to_menu(self):
        self.parent.child_windows[self.win_key] = self
        if not self.event:
            label = _("New Event")
        else:
            label = self.event.get_name()
        if not label.strip():
            label = _("New Event")
        label = "%s: %s" % (_('Event'),label)
        self.parent_menu_item = gtk.MenuItem(label)
        self.parent_menu_item.set_submenu(gtk.Menu())
        self.parent_menu_item.show()
        self.parent.winsmenu.append(self.parent_menu_item)
        self.winsmenu = self.parent_menu_item.get_submenu()
        self.menu_item = gtk.MenuItem(_('Event Editor'))
        self.menu_item.connect("activate",self.present)
        self.menu_item.show()
        self.winsmenu.append(self.menu_item)

    def remove_itself_from_menu(self):
        del self.parent.child_windows[self.win_key]
        self.menu_item.destroy()
        self.winsmenu.destroy()
        self.parent_menu_item.destroy()

    def present(self,obj):
        self.window.present()

    def on_help_clicked(self,obj):
        """Display the relevant portion of GRAMPS manual"""
        gnome.help_display('gramps-manual','gramps-edit-complete')

    def on_menu_changed(self,obj):
        cobj = obj.get_data("d")
        self.date.set(unicode(self.date_field.get_text()))
        self.date.set_calendar(cobj)
        self.date_field.set_text(self.date.get_date())
        self.date_check.set_calendar(cobj())
        
    def get_place(self,field,makenew=0):
        text = strip(unicode(field.get_text()))
        if text:
            if self.pmap.has_key(text):
                return self.parent.db.get_place_id_map()[self.pmap[text]]
            elif makenew:
                place = RelLib.Place()
                place.set_title(text)
                self.parent.db.add_place(place)
                self.pmap[text] = place.get_id()
                self.plist.append(place)
                return place
            else:
                return None
        else:
            return None

    def on_event_edit_ok_clicked(self,obj):

        ename = unicode(self.name_field.get_text())
        self.date.set(unicode(self.date_field.get_text()))
        ecause = unicode(self.cause_field.get_text())
        eplace_obj = self.get_place(self.place_field,1)
        buf = self.note_field.get_buffer()

        enote = unicode(buf.get_text(buf.get_start_iter(),buf.get_end_iter(),gtk.FALSE))
        eformat = self.preform.get_active()
        edesc = unicode(self.descr_field.get_text())
        epriv = self.priv.get_active()

        if not ename in self.elist:
            WarningDialog(_('New event type created'),
                          _('The "%s" event type has been added to this database.\n'
                            'It will now appear in the event menus for this database') % ename)
            self.elist.append(ename)
            self.elist.sort()

        if self.event == None:
            self.event = RelLib.Event()
            self.db.add_event(self.event)
            self.event.set_source_reference_list(self.srcreflist)
            self.event.set_witness_list(self.witnesslist)
            self.parent.elist.append(self.event.get_id())
        
        self.update_event(ename,self.date,eplace_obj,edesc,enote,eformat,epriv,ecause)
        self.parent.redraw_event_list()
        self.callback(self.event)
        self.close(obj)

    def update_event(self,name,date,place,desc,note,format,priv,cause):
        if place:
            if self.event.get_place_id() != place.get_id():
                self.event.set_place_id(place.get_id())
                self.parent.lists_changed = 1
        else:
            if self.event.get_place_id():
                self.event.set_place_id("")
                self.parent.lists_changed = 1
        
        if self.event.get_name() != self.trans(name):
            self.event.set_name(self.trans(name))
            self.parent.lists_changed = 1
        
        if self.event.get_description() != desc:
            self.event.set_description(desc)
            self.parent.lists_changed = 1

        if self.event.get_note() != note:
            self.event.set_note(note)
            self.parent.lists_changed = 1

        if self.event.get_note_format() != format:
            self.event.set_note_format(format)
            self.parent.lists_changed = 1

        dobj = self.event.get_date_object()

        self.event.set_source_reference_list(self.srcreflist)
        self.event.set_witness_list(self.witnesslist)
        
        if Date.compare_dates(dobj,date) != 0:
            self.event.set_date_object(date)
            self.parent.lists_changed = 1

        if self.event.get_cause() != cause:
            self.event.set_cause(cause)
            self.parent.lists_changed = 1

        if self.event.get_privacy() != priv:
            self.event.set_privacy(priv)
            self.parent.lists_changed = 1
        trans = self.db.start_transaction()
        self.db.commit_event(self.event,trans)
        self.db.add_transaction(trans)

    def on_switch_page(self,obj,a,page):
        buf = self.note_field.get_buffer()
        text = unicode(buf.get_text(buf.get_start_iter(),buf.get_end_iter(),gtk.FALSE))
        if text:
            Utils.bold_label(self.notes_label)
        else:
            Utils.unbold_label(self.notes_label)

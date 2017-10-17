#!/usr/bin/env python3

""" pylaunch: Python quick launcher
    ----------------Authors----------------
    Lachlan de Waard <lachlan.00@gmail.com>
    ----------------Licence----------------
    GNU General Public License version 3

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import gi.repository
import configparser
import gi
import os
import subprocess
import sys

gi.require_version('Gtk', '3.0')
gi.require_version('Budgie', '1.0')
gi.require_version('Wnck', '3.0')
from gi.repository import Budgie, GObject, Wnck, Gtk, Gdk

from xdg.BaseDirectory import xdg_config_dirs

CONFIG = xdg_config_dirs[0] + '/quickwin.conf'
#UI_FILE = '/usr/share/quickwin/main.ui'
UI_FILE = 'main.ui'
#ICON_DIR = '/usr/share/icons/gnome/'
#TRAY_ICON = '/usr/share/pixmaps/quickwin.png'
#TRAY_ICON = '/usr/share/icons/gnome/scalable/actions/system-run-symbolic.svg'
#TRAY_ICON = '/usr/share/icons/gnome/32x32/actions/system-run.png'
#CUSTOM_ICON = None
USER_HOME = os.getenv('HOME')
QUICK_STORE = USER_HOME + '/.local/share/quicklaunch'
#CUSTOM_PATH = None
#CUSTOM_TITLE = None
WINDOWOPEN = False
WINDOWSPOSITION = None

class PyLaunch(GObject.GObject, Budgie.Plugin):
    """ This is simply an entry point into your Budgie Applet implementation.
        Note you must always override Object, and implement Plugin.
    """

    # Good manners, make sure we have unique name in GObject type system
    __gtype_name__ = "PyLaunch"

    def __init__(self):
        """ Initialisation is important.
        """
        GObject.Object.__init__(self)

    def do_get_panel_widget(self, uuid):
        """ This is where the real fun happens. Return a new Budgie.Applet
            instance with the given UUID. The UUID is determined by the
            BudgiePanelManager, and is used for lifetime tracking.
        """
        return PyLaunchApplet(uuid)

class PyLaunchApplet(Budgie.Applet):
    """ Budgie.Applet is in fact a Gtk.Bin """

    #wn_screen = None
    button = None

    def __init__(self, uuid):
        Budgie.Applet.__init__(self)

        # Add a button to our UI
        self.button = Gtk.ToggleButton.new()
        self.button.set_relief(Gtk.ReliefStyle.NONE)
        self.button.set_active(False)
        self.add(self.button)
        #self.wn_screen = Wnck.Screen.get_default()

        img = Gtk.Image.new_from_icon_name("start-here-symbolic", Gtk.IconSize.BUTTON)
        self.button.add(img)
        self.button.set_tooltip_text("Quicklauncher (from Python!)")


        # Hook up Wnck signals
        #self.wn_screen.connect_after('showing-desktop-changed', self.scr_changed)
        self.button.connect_after('clicked', self.status_clicked)
        self.button.connect_after('popup-menu', self.right_click_event)

        """ start pylaunch """
        self.builder = Gtk.Builder()
        self.builder.add_from_file(UI_FILE)
        self.builder.connect_signals(self)
        # get config info
        self.conf = configparser.RawConfigParser()
        self.checkconfig()
        self.conf.read(CONFIG)
        self.homefolder = self.conf.get('conf', 'home')
        # backwards compatability for new config options
        self.current_dir = self.homefolder
        self.current_files = None
        self.filelist = None
        # Make a status icon
        # Set custom icon
        #self.statusicon.connect('activate', self.status_clicked)
        #self.statusicon.connect('popup-menu', self.right_click_event)
        #self.statusicon.set_tooltip_text("pylaunch")
        # load main window items
        self.window = self.builder.get_object('main_window')
        #self.window.set_parent(self.statusicon)
        #self.window.set_modal(True)
        self.addbutton = self.builder.get_object('addbutton')
        self.addimage = self.builder.get_object('addimage')
        self.settingsbutton = self.builder.get_object('settingsbutton')
        self.closemain = self.builder.get_object('closemain')
        # self.fileview = self.builder.get_object('fileview')
        self.contentlist = self.builder.get_object('filestore')
        self.contenttree = self.builder.get_object('fileview')
        # load add connection window items
        self.addwindow = self.builder.get_object('add_window')
        self.addentry = self.builder.get_object('addentry')
        self.addcommand = self.builder.get_object('cmdentry')
        self.saveaddbutton = self.builder.get_object('saveaddbutton')
        self.closeaddbutton = self.builder.get_object('closeaddbutton')
        # load config window items
        self.confwindow = self.builder.get_object('config_window')
        self.homeentry = self.builder.get_object('homeentry')
        self.applybutton = self.builder.get_object('applyconf')
        self.closebutton = self.builder.get_object('closeconf')
        # load popup window items
        self.popwindow = self.builder.get_object('popup_window')
        self.popbutton = self.builder.get_object('closepop')
        # create lists and connect actions
        self.connectui()
        self.listfiles(self.current_dir)
        self.run()

    def checkconfig(self):
        """ create a default config if not available """
        if not os.path.isfile(CONFIG):
            conffile = open(CONFIG, "w")
            conffile.write('[conf]\nhome = ' + QUICK_STORE + '\n' +
                       'root_x = \n' +
                       'root_y = \n' +
                       'width = \n' +
                       'height = \n')
            conffile.close()
        else:
            conf = configparser.RawConfigParser()
            conf.read(CONFIG)
            if not conf.has_section('home'):
                conf.add_section('home')
            if not conf.has_section('root_x'):
                conf.add_section('root_x')
            if not conf.has_section('root_y'):
                conf.add_section('root_y')
            if not conf.has_section('width'):
                conf.add_section('width')
            if not conf.has_section('height'):
                conf.add_section('height')
        return

    def connectui(self):
        """ connect all the window wisgets """
        # main window actions
        self.window.connect('destroy', self.quit)
        # self.window.connect('key-release-event', self.shortcatch)
        self.settingsbutton.connect('clicked', self.showconfig)
        #self.addbutton.connect('clicked', self.showaddconnection)
        #self.closemain.connect('clicked', self.quit)
        # images
        #self.addimage.set_from_file(ICON_DIR + '16x16/actions/add.png')
        #self.addimage.add.Gtk.Image.new_from_icon_name("gtk-add", Gtk.IconSize.BUTTON)
        # config window actions
        self.applybutton.connect('clicked', self.saveconf)
        self.closebutton.connect('clicked', self.closeconf)
        # add window actions
        #self.saveaddbutton.connect('clicked', self.saveadd)
        #self.closeaddbutton.connect('clicked', self.closeadd)
        # popup window actions
        #self.popbutton.connect('clicked', self.closepop)
        # set up file and folder lists
        cell = Gtk.CellRendererText()
        filecolumn = Gtk.TreeViewColumn('PyLaunch Chortcuts', cell, text=0)
        self.contenttree.connect('row-activated', self.loadselection)
        self.contenttree.connect('button-release-event', self.buttonclick)
        self.contenttree.append_column(filecolumn)
        self.contenttree.set_model(self.contentlist)
        # list default dir on startup
        if not os.path.isdir(self.homefolder):
            os.makedirs(self.homefolder)
        return

    def run(self):
        """ show the main window and start the main GTK loop """
        #self.window.set_position(Gtk.Align.END)
        try:
            self.window.move(int(self.conf.get('conf', 'root_x')), int(self.conf.get('conf', 'root_y')))
            self.window.resize(int(self.conf.get('conf', 'width')), int(self.conf.get('conf', 'height')))
        except ValueError:
            # incorrect value for setting
            pass
        except configparser.NoOptionError:
            # config missing value
            pass
        #self.showme(self.window)
        self.show_all()
        #Gtk.main()

    def buttonclick(self, actor, event):
        """ Catch mouse clicks"""
        if actor == self.contenttree:
            if Gdk.ModifierType.BUTTON2_MASK == event.get_state():
                print('middle click')
                return actor
            elif Gdk.ModifierType.BUTTON3_MASK == event.get_state():
                print('right click')
                return actor
        return

    def showme(self, *args):
        """ show a Gtk.Window """
        self.listfiles(self.current_dir)
        args[0].show()

    def hideme(self, *args):
        """ hide a Gtk.Window """
        self.listfiles(self.current_dir)
        args[0].hide()

    def right_click_event(self, icon, button, time):
        #self.menu = Gtk.Menu()

        #quit = Gtk.MenuItem()
        #quit.set_label("Quit")

        #quit.connect("activate", Gtk.main_quit)

        #self.menu.append(quit)
        #self.menu.show_all()

        #def pos(self, button, menu, icon):
        #        return (Gtk.StatusIcon.position_menu(self, button, menu, icon))

        #self.menu.popup(None, None, pos, self.buttonclick, button, time)
        return

    def status_clicked(self, status):
        """ hide and unhide the window when clicking the status icon """
        global WINDOWOPEN
        # Unhide the window
        #print(dir(self.statusicon))
        if not WINDOWOPEN:
            self.window.show()
            #self.window.do_popup_menu()
            #self.window.popup()
            WINDOWOPEN = True
            # save window position
            self.conf.set('conf', 'root_x', self.window.get_position().root_x)
            self.conf.set('conf', 'root_y', self.window.get_position().root_y)
            self.conf.set('conf', 'width', self.window.get_size().width)
            self.conf.set('conf', 'height', self.window.get_size().height)
            self.writeconf()
        elif WINDOWOPEN:
            self.conf.set('conf', 'root_x', self.window.get_position().root_x)
            self.conf.set('conf', 'root_y', self.window.get_position().root_y)
            self.conf.set('conf', 'width', self.window.get_size().width)
            self.conf.set('conf', 'height', self.window.get_size().height)
            self.writeconf()
            self.delete_event(self, self.window)
        return status

    def delete_event(self, window, event):
        """ Hide the window then the close button is clicked """
        global WINDOWOPEN
        # Don't delete; hide instead
        #print(window)
        #print(event)
        self.window.hide_on_delete()
        WINDOWOPEN = False
        return True

    def showconfig(self, actor):
        """ fill and show the config window """
        if actor == self.settingsbutton:
            self.homeentry.set_text(self.homefolder)
            self.showme(self.confwindow)
        return actor

    def showaddconnection(self, actor):
        """ show the add connection window """
        self.homeentry.set_text(self.homefolder)
        self.showme(self.addwindow)
        return actor

    def writeconf(self):
        """ write to conf file """
        conffile = open(CONFIG, "w")
        self.conf.write(conffile)
        conffile.close()
        return

    def saveconf(self, actor):
        """ save any config changes and update live settings"""
        if actor == self.applybutton:
            self.conf.read(CONFIG)
            self.conf.set('conf', 'home', self.homeentry.get_text())
            self.homefolder = self.homeentry.get_text()
            self.writeconf()
        return

    def saveadd(self, *args):
        """ save any config changes and update live settings"""
        print("SAVE ADD")
        print(self.addentry.get_text())
        print(self.addcommand.get_text())
        return args

    def closeconf(self, actor):
        """ hide the config window """
        if actor == self.closebutton:
            self.hideme(self.confwindow)
        return

    def closeadd(self, actor):
        """ refresh the file list and hide the config window """
        self.listfiles(self.current_dir)
        if actor == self.closeaddbutton:
            self.hideme(self.addwindow)
        return

    def closepop(self, actor):
        """ hide the error popup window """
        if actor == self.popbutton:
            self.hideme(self.popwindow)
        return

    def loadselection(self, *args):
        """ load selected files into tag editor """
        contenttree = args[0]
        model, fileiter = contenttree.get_selection().get_selected_rows()
        self.current_files = []
        for files in fileiter:
            if model[files][0] == '[No files found]':
                self.current_files = []
            else:
                tmp_file = os.path.join(self.current_dir, model[files][0])
                if os.access(tmp_file, os.X_OK):
                    self.current_files.append(tmp_file)
                else:
                    print(tmp_file + '\nIs not executable')
        if not self.current_files == []:
            print("Opening selected file")
            print(self.current_files)
            subprocess.Popen(self.current_files)
        else:
            print('relisting directory')
            self.listfiles(self.current_dir)
        return

    # def shortcatch(self, actor, event):
    #    """ capture keys for shortcuts """
    #    test_mask = (event.state & Gdk.ModifierType.CONTROL_MASK ==
    #                 Gdk.ModifierType.CONTROL_MASK)
    #    #if event.get_state() and test_mask:

    def quit(self, *args):
        """ stop the process thread and close the program"""
        # destroy windows and quit
        self.addwindow.destroy()
        self.confwindow.destroy()
        self.window.destroy()
        Gtk.main_quit(*args)
        return False

    def listfiles(self, srcpath):
        """ function to fill the file list column """
        self.current_files = []
        try:
            files_dir = os.listdir(srcpath)
            files_dir.sort(key=lambda y: y.lower())
        except OSError:
            self.listfiles(self.homefolder)
            return
        # clear list if we have scanned before
        for items in self.contentlist:
            self.contentlist.remove(items.iter)
        # clear combobox before adding entries
        for items in self.contenttree:
            self.contenttree.remove(items.iter)
        # search the supplied directory for items
        for items in files_dir:
            test_executable = None
            tmp_file = self.current_dir + '/' + items
            test_file = os.path.isfile(tmp_file)
            if test_file:
                test_executable = os.access(tmp_file, os.X_OK)
            if not items[0] == '.' and test_file and test_executable:
                self.contentlist.append([items])
        if len(self.contentlist) == 0:
            self.contentlist.append(['[No files found]'])
        return

    def scr_changed(self, wscr, udata=None):
        """ WnckScreen changed, update button """
        self.button.set_active(self.wn_screen.get_showing_desktop())

    def on_clicked(self, widg, data=None):
        """ User clicked our button, update WnckScreen """
        self.wn_screen.toggle_showing_desktop(self.button.get_active())


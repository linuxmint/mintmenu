#!/usr/bin/python3

import locale
import gc
import gettext
import os
import sys
import traceback

import gi
gi.require_version("Gtk", "3.0")
gi.require_version('MatePanelApplet', '4.0')
gi.require_version('XApp', '1.0')
from gi.repository import Gtk, GdkPixbuf, Gdk, GObject
from gi.repository import MatePanelApplet
from gi.repository import Gio

import xdg.Config

import keybinding
import pointerMonitor
import setproctitle
from plugins.execute import Execute

# Rename the process
setproctitle.setproctitle('mintmenu')

# i18n
gettext.install("mintmenu", "/usr/share/linuxmint/locale")
locale.bindtextdomain("mintmenu", "/usr/share/linuxmint/locale")
locale.textdomain("mintmenu")

NAME = _("Menu")
PATH = os.path.abspath(os.path.dirname(sys.argv[0]))

sys.path.append(os.path.join(PATH , "plugins"))

windowManager = os.getenv("DESKTOP_SESSION")
if not windowManager:
    windowManager = "MATE"
xdg.Config.setWindowManager(windowManager.upper())


class MainWindow(object):
    """This is the main class for the application"""

    def __init__(self, toggleButton, settings, de):

        self.settings = settings
        self.path = PATH
        sys.path.append(os.path.join(self.path, "plugins"))

        self.de = de

        self.toggle = toggleButton
        builder = Gtk.Builder()
        builder.set_translation_domain("mintmenu")
        builder.add_from_file("/usr/share/linuxmint/mintmenu/main.ui")
        self.window     = builder.get_object("mainWindow")
        self.paneholder = builder.get_object("paneholder")

        builder.connect_signals(self)

        self.window.connect("key-press-event", self.onKeyPress)
        self.window.connect("focus-in-event", self.onFocusIn)
        self.loseFocusId = self.window.connect("focus-out-event", self.onFocusOut)
        self.loseFocusBlocked = False

        self.window.stick()

        plugindir = os.path.join(os.path.expanduser("~"), ".linuxmint/mintMenu/plugins")
        sys.path.append(plugindir)

        self.settings.connect("changed::plugins-list", self.RegenPlugins)
        self.settings.connect("changed::start-with-favorites", self.toggleStartWithFavorites)
        self.settings.connect("changed::tooltips-enabled", self.toggleTooltipsEnabled)

        self.getSetGSettingEntries()

        self.tooltipsWidgets = []

        self.PopulatePlugins()
        self.toggleTooltipsEnabled(self.settings, "tooltips-enabled")
        self.firstTime = True

    @classmethod
    def on_window1_destroy (widget, data=None):
        Gtk.main_quit()
        sys.exit(0)

    def wakePlugins(self):
        # Call each plugin and let them know we're showing up
        for plugin in self.plugins.values():
            if hasattr(plugin, "wake"):
                plugin.wake()

    def toggleTooltipsEnabled(self, settings, key, args=None):
        enableTooltips = settings.get_boolean(key)
        for widget in self.tooltipsWidgets:
            widget.set_has_tooltip(enableTooltips)

    def toggleStartWithFavorites(self, settings, key):
        self.startWithFavorites = settings.get_boolean(key)

    def getSetGSettingEntries(self):
        self.dottedfile          = os.path.join(self.path, "dotted.png")
        self.pluginlist           = self.settings.get_strv("plugins-list")
        self.offset               = self.settings.get_int("offset")
        self.enableTooltips       = self.settings.get_boolean("tooltips-enabled")
        self.startWithFavorites   = self.settings.get_boolean("start-with-favorites")

    def PopulatePlugins(self):
        PluginPane = Gtk.EventBox()
        PluginPane.show()
        PaneLadder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        PluginPane.add(PaneLadder)
        ImageBox = Gtk.EventBox()
        ImageBox.show()

        seperatorImage = GdkPixbuf.Pixbuf.new_from_file(self.dottedfile)

        self.plugins = {}

        for plugin in self.pluginlist:
            if plugin in self.plugins:
                print("Duplicate plugin in list: %s" % plugin)
                continue

            if plugin != "newpane":
                try:
                    X = __import__(plugin)
                    # If no parameter passed to plugin it is autonomous
                    if X.pluginclass.__init__.__code__.co_argcount == 1:
                        MyPlugin = X.pluginclass()
                    else:
                        # pass mintMenu and togglebutton instance so that the plugin can use it
                        MyPlugin = X.pluginclass(self, self.toggle, self.de)

                    if not MyPlugin.icon:
                        MyPlugin.icon = "mate-logo-icon.png"

                    #if hasattr(MyPlugin, "hideseparator") and not MyPlugin.hideseparator:
                    #    Image1 = Gtk.Image()
                    #    Image1.set_from_pixbuf(seperatorImage)
                    #    if not ImageBox.get_child():
                    #        ImageBox.add(Image1)
                    #        Image1.show()

                    #print u"Loading plugin '" + plugin + "' : sucessful"
                except Exception:
                    MyPlugin = Gtk.EventBox() #Fake class for MyPlugin
                    MyPlugin.heading = _("Couldn't load plugin:") + " " + plugin
                    MyPlugin.content_holder = Gtk.EventBox()

                    # create traceback
                    info = sys.exc_info()

                    errorLabel = Gtk.Label("\n".join(traceback.format_exception(info[0], info[1], info[2])).replace("\\n", "\n"))
                    errorLabel.set_selectable(True)
                    errorLabel.set_line_wrap(True)
                    errorLabel.set_alignment(0.0, 0.0)
                    errorLabel.set_padding(5, 5)
                    errorLabel.show()

                    MyPlugin.content_holder.add(errorLabel)
                    MyPlugin.add(MyPlugin.content_holder)
                    MyPlugin.width = 270
                    MyPlugin.icon = 'mate-logo-icon.png'
                    print("Unable to load %s plugin" % plugin)

                MyPlugin.content_holder.add_class(f"mint-{plugin}")
                MyPlugin.content_holder.show()

                VBox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                if MyPlugin.heading != "":
                    label1 = Gtk.Label()
                    label1.set_markup("<span size=\"12000\" weight=\"bold\">%s</span>" % MyPlugin.heading)
                    Align1 = Gtk.Alignment.new(0, 0, 0, 0)
                    Align1.set_padding(10, 5, 10, 0)
                    Align1.add(label1)
                    Align1.show()
                    label1.show()
                    heading = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                    heading.set_size_request(MyPlugin.width, -1)
                    heading.add_class("mint-title")
                    heading.add(Align1)
                    heading.show()
                    VBox1.pack_start(heading, False, False, 0)

                VBox1.show()
                #Add plugin to Plugin Box under heading button
                MyPlugin.content_holder.get_parent().remove(MyPlugin.content_holder)
                VBox1.add(MyPlugin.content_holder)

                #Add plugin to main window
                PaneLadder.pack_start(VBox1 , True, True, 0)
                PaneLadder.show()

                try:
                    MyPlugin.get_window().destroy()
                except AttributeError:
                    pass

                try:
                    if hasattr(MyPlugin, 'do_plugin'):
                        MyPlugin.do_plugin()
                    if hasattr(MyPlugin, 'height'):
                        MyPlugin.content_holder.set_size_request(-1, MyPlugin.height)
                except:
                    # create traceback
                    info = sys.exc_info()

                    error = _("Couldn't initialize plugin") + " " + plugin + " : " + "\n".join(traceback.format_exception(info[0], info[1], info[2])).replace("\\n", "\n")
                    msgDlg = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, error)
                    msgDlg.run()
                    msgDlg.destroy()

                self.plugins[plugin] = MyPlugin

            else:
                self.paneholder.pack_start(ImageBox, False, False, 0)
                self.paneholder.pack_start(PluginPane, False, False, 0)
                PluginPane = Gtk.EventBox()
                PaneLadder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                PluginPane.add(PaneLadder)
                ImageBox = Gtk.EventBox()
                ImageBox.show()
                PluginPane.show_all()

                if self.plugins and hasattr(MyPlugin, 'hideseparator') and not MyPlugin.hideseparator:
                    Image1 = Gtk.Image()
                    Image1.set_from_pixbuf(seperatorImage)
                    Image1.show()
                    #ImageBox.add(Image1)

                    Align1 = Gtk.Alignment.new(0, 0, 0, 0)
                    Align1.set_padding(0, 0, 6, 6)
                    Align1.add(Image1)
                    ImageBox.add(Align1)
                    ImageBox.show_all()


        self.paneholder.pack_start(ImageBox, False, False, 0)
        self.paneholder.pack_start(PluginPane, False, False, 0)

    def setTooltip(self, widget, tip):
        self.tooltipsWidgets.append(widget)
        widget.set_tooltip_text(tip)

    def RegenPlugins(self, *args, **kargs):
        #print u"Reloading Plugins..."
        for item in self.paneholder:
            item.destroy()

        for plugin in self.plugins.values():
            if hasattr(plugin, "destroy"):
                plugin.destroy()

        try:
            del plugin
        except:
            pass

        try:
            del self.plugins
        except:
            pass

        gc.collect()

        self.getSetGSettingEntries()
        self.PopulatePlugins()
        self.toggleTooltipsEnabled(self.settings, "tooltips-enabled")

        #print NAME+u" reloaded"

    def onKeyPress(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
            return True
        return False

    def show(self):
        self.window.present()

        # Hack for opacity not showing on first composited draw
        if self.firstTime:
            self.firstTime = False
            self.window.set_opacity(1.0)

        self.window.get_window().focus(Gdk.CURRENT_TIME)

        for plugin in self.plugins.values():
            if hasattr(plugin, "onShowMenu"):
                plugin.onShowMenu()

        if "applications" in self.plugins and hasattr(self.plugins["applications"], "focusSearchEntry"):
            if self.startWithFavorites:
                self.plugins["applications"].changeTab(0)
            self.plugins["applications"].focusSearchEntry()

    def hide(self):
        for plugin in self.plugins.values():
            if hasattr(plugin, "onHideMenu"):
                plugin.onHideMenu()

        self.window.hide()

    def onFocusIn(self, *args):
        if self.loseFocusBlocked:
            self.window.handler_unblock(self.loseFocusId)
            self.loseFocusBlocked = False

        return False

    def onFocusOut(self, *args):
        if self.window.get_visible():
            self.hide()
        return False

    def stopHiding(self):
        if not self.loseFocusBlocked:
            self.window.handler_block(self.loseFocusId)
            self.loseFocusBlocked = True

class MenuWin(object):

    def __init__(self, applet, iid):
        self.applet = applet
        self.detect_desktop_environment()
        self.settings = Gio.Settings.new("com.linuxmint.mintmenu")
        self.icon_theme = Gtk.IconTheme.get_default()
        self.button_icon = Gtk.Image(no_show_all=True)
        self.loadSettings()

        self.button_box = None
        self.updatePanelButton()

        self.mate_settings = Gio.Settings.new("org.mate.interface")
        self.mate_settings.connect("changed::gtk-theme", self.changeTheme)

        self.settings.connect("changed::applet-text", self.reloadSettings)
        self.settings.connect("changed::theme-name", self.changeTheme)
        self.settings.connect("changed::hot-key", self.reloadSettings)
        self.settings.connect("changed::applet-icon", self.reloadSettings)
        self.settings.connect("changed::show-applet-icon", self.reloadSettings)
        self.settings.connect("changed::applet-icon-size", self.reloadSettings)

        self.applet.set_flags(MatePanelApplet.AppletFlags.EXPAND_MINOR)
        self.applet.connect("button-press-event", self.showMenu)
        self.applet.connect("change-orient", self.updatePanelButton)
        self.applet.connect("enter-notify-event", self.enter_notify)
        self.applet.connect("leave-notify-event", self.leave_notify)

        self.mainwin = MainWindow(self.button_box, self.settings, self.de)
        self.mainwin.window.connect("map-event", self.onWindowMap)
        self.mainwin.window.connect("unmap-event", self.onWindowUnmap)
        self.mainwin.window.connect("size-allocate", lambda *args: self.positionMenu())

        self.mainwin.window.set_name("mintmenu") # Name used in Gtk RC files
        self.applyTheme()

        try:
            self.keybinder = keybinding.GlobalKeyBinding()
            if self.hotkeyText != "":
                self.keybinder.grab(self.hotkeyText)
            self.keybinder.connect("activate", self.onBindingPress)
            self.keybinder.start()
            self.settings.connect("changed::hot-key", self.hotkeyChanged)
            print("Binding to Hot Key: %s" % self.hotkeyText)
        except Exception as e:
            self.keybinder = None
            print("** WARNING ** - Keybinder Error")
            print("Error Report :\n", e)

        self.applet.set_can_focus(False)

        try:
            self.pointerMonitor = pointerMonitor.PointerMonitor()
            self.pointerMonitor.connect("activate", self.onPointerOutside)
            self.mainwin.window.connect("realize", self.onRealize)
        except Exception as e:
            print("** WARNING ** - Pointer Monitor Error")
            print("Error Report :\n", e)

    def onWindowMap(self, *args):
        self.applet.get_style_context().set_state(Gtk.StateFlags.SELECTED)
        self.button_box.get_style_context().set_state(Gtk.StateFlags.SELECTED)
        if self.keybinder is not None:
            self.keybinder.set_focus_window(self.mainwin.window.get_window())
        return False

    def onWindowUnmap(self, *args):
        self.applet.get_style_context().set_state(Gtk.StateFlags.NORMAL)
        self.button_box.get_style_context().set_state(Gtk.StateFlags.NORMAL)
        if self.keybinder is not None:
            self.keybinder.set_focus_window()
        return False

    def onRealize(self, *args):
        self.pointerMonitor.addWindowToMonitor(self.mainwin.window.get_window())
        self.pointerMonitor.addWindowToMonitor(self.applet.get_window())
        self.pointerMonitor.start()
        return False

    def onPointerOutside(self, *args):
        self.mainwin.hide()
        return True

    def onBindingPress(self, binder):
        self.toggleMenu()
        return True

    def enter_notify(self, applet, event):
        self.set_applet_icon(True)

    def leave_notify(self, applet, event):
        # Hack for mate-panel-test-applets focus issue (this can be commented)
        # if event.state & Gdk.ModifierType.BUTTON1_MASK and applet.get_style_context().get_state() & Gtk.StateFlags.SELECTED:
        #     if event.x >= 0 and event.y >= 0 and event.x < applet.get_window().get_width() and event.y < applet.get_window().get_height():
        #         self.mainwin.stopHiding()

        self.set_applet_icon()

    def set_applet_icon(self, saturate=False):
        if not self.symbolic:
            if saturate:
                self.button_icon.set_from_surface(self.saturated_surface)
            else:
                self.button_icon.set_from_surface(self.surface)

    def updatePanelButton(self):
        if self.button_box != None:
            self.button_box.destroy()

        self.set_applet_icon()
        self.systemlabel = Gtk.Label(label= "%s" % self.buttonText, no_show_all=True)

        if os.path.isfile("/etc/linuxmint/info"):
            with open("/etc/linuxmint/info") as info:
                for line in info:
                    if line.startswith("DESCRIPTION="):
                        tooltip = line.split("=",1)[1].strip('"\n')
                        self.systemlabel.set_tooltip_text(tooltip)
                        self.button_icon.set_tooltip_text(tooltip)
                        break

        self.button_icon.props.margin = 0
        self.systemlabel.props.margin = 0
        self.systemlabel.props.visible = show_text = self.buttonText != ""
        self.button_icon.props.visible = self.showIcon

        if self.applet.get_orient() == MatePanelApplet.AppletOrient.UP or self.applet.get_orient() == MatePanelApplet.AppletOrient.DOWN:
            self.button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            self.button_box.pack_start(self.button_icon, False, False, 0)
            self.button_box.pack_start(self.systemlabel, False, False, 0)
            if self.showIcon and not show_text:
                self.button_icon.props.margin_start = 5
                self.button_icon.props.margin_end = 5
            elif show_text and not self.showIcon:
                self.systemlabel.props.margin_start = 5
                self.systemlabel.props.margin_end = 5
            else:
                self.button_icon.props.margin_start = 5
                self.systemlabel.props.margin_end = 5
        # if we have a vertical panel
        elif self.applet.get_orient() == MatePanelApplet.AppletOrient.LEFT:
            self.button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            self.systemlabel.set_angle(270)
            self.button_box.pack_start(self.button_icon , False, False, 0)
            self.button_box.pack_start(self.systemlabel , False, False, 0)
            if self.showIcon and not show_text:
                self.button_icon.props.margin_top = 5
                self.button_icon.props.margin_bottom = 5
            elif show_text and not self.showIcon:
                self.systemlabel.props.margin_top = 5
                self.systemlabel.props.margin_bottom = 5
            else:
                self.button_icon.props.margin_top = 5
                self.systemlabel.props.margin_bottom = 5
        elif self.applet.get_orient() == MatePanelApplet.AppletOrient.RIGHT:
            self.button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            self.systemlabel.set_angle(90)
            self.button_box.pack_start(self.systemlabel , False, False, 0)
            self.button_box.pack_start(self.button_icon , False, False, 0)
            if self.showIcon and not show_text:
                self.button_icon.props.margin_top = 5
                self.button_icon.props.margin_bottom = 5
            elif show_text and not self.showIcon:
                self.systemlabel.props.margin_top = 5
                self.systemlabel.props.margin_bottom = 5
            else:
                self.button_icon.props.margin_bottom = 5
                self.systemlabel.props.margin_top = 5

        self.button_box.set_homogeneous(False)
        self.button_box.show_all()
        self.sizeButton()
        self.button_box.get_style_context().add_class('mintmenu')
        self.applet.add(self.button_box)
        self.applet.set_background_widget(self.applet)

    def loadSettings(self, *args, **kargs):
        self.showIcon   =  self.settings.get_boolean("show-applet-icon")
        self.buttonText =  self.settings.get_string("applet-text")
        self.theme_name =  self.settings.get_string("theme-name")
        self.hotkeyText =  self.settings.get_string("hot-key")

        applet_icon = self.settings.get_string("applet-icon")
        if not (os.path.exists(applet_icon) or self.icon_theme.has_icon(applet_icon)):
            self.settings.reset("applet-icon")
        self.scale = self.button_icon.get_scale_factor()
        self.symbolic = False
        self.pixbuf = None
        if "/" in applet_icon:
            if applet_icon.endswith(".svg"):
                self.pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(applet_icon, -1, 22 * self.scale)
            else:
                self.pixbuf = GdkPixbuf.Pixbuf.new_from_file(applet_icon)
        else:
            if applet_icon.endswith("symbolic"):
                self.button_icon.set_from_icon_name(applet_icon, Gtk.IconSize.DIALOG)
                self.button_icon.set_pixel_size(22)
                self.symbolic = True
            else:
                self.pixbuf = self.icon_theme.load_icon(applet_icon, 22 * self.scale, 0)
        if self.pixbuf is not None:
            self.surface = Gdk.cairo_surface_create_from_pixbuf(self.pixbuf, self.scale)
            self.saturated_pixbuf = self.pixbuf.copy()
            GdkPixbuf.Pixbuf.saturate_and_pixelate(self.saturated_pixbuf, self.saturated_pixbuf, 1.5, False)
            self.saturated_surface = Gdk.cairo_surface_create_from_pixbuf(self.saturated_pixbuf, self.scale)
        self.buttonIcon =  self.settings.get_string("applet-icon")
        self.iconSize = self.settings.get_int("applet-icon-size")

    def changeTheme(self, *args):
        self.reloadSettings()
        self.applyTheme()

    def applyTheme(self):
        style_settings = Gtk.Settings.get_default()
        desktop_theme = self.mate_settings.get_string('gtk-theme')
        if self.theme_name == "default":
            style_settings.set_property("gtk-theme-name", desktop_theme)
        else:
            try:
                style_settings.set_property("gtk-theme-name", self.theme_name)
            except:
                style_settings.set_property("gtk-theme-name", desktop_theme)

    def hotkeyChanged (self, schema, key):
        self.hotkeyText =  self.settings.get_string("hot-key")
        self.keybinder.rebind(self.hotkeyText)

    def sizeButton(self):
        # This code calculates width and height for the button_box
        # and takes the orientation and scale factor in account
        bi_req = self.button_icon.get_preferred_size()[1]
        bi_scale = self.button_icon.get_scale_factor()
        sl_req = self.systemlabel.get_preferred_size()[1]
        sl_scale = self.systemlabel.get_scale_factor()
        if self.applet.get_orient() == MatePanelApplet.AppletOrient.UP or self.applet.get_orient() == MatePanelApplet.AppletOrient.DOWN:
            if self.showIcon:
                self.applet.set_size_request(sl_req.width / sl_scale + bi_req.width / bi_scale, bi_req.height)
            else:
                self.applet.set_size_request(sl_req.width / sl_scale, bi_req.height)
        else:
            if self.showIcon:
                self.applet.set_size_request(bi_req.width, sl_req.height / sl_scale + bi_req.height / bi_scale)
            else:
                self.applet.set_size_request(bi_req.width, sl_req.height / sl_scale)

    def reloadSettings(self, *args):
        self.loadSettings()
        self.updatePanelButton()

    def showAboutDialog(self, action, userdata = None):
        about = Gtk.AboutDialog()
        about.set_program_name("mintMenu")
        about.set_version("__DEB_VERSION__")
        about.set_license_type(Gtk.License.GPL_3_0)
        about.set_comments(_("Advanced MATE Menu"))
        # about.set_authors(["Clement Lefebvre <clem@linuxmint.com>", "Lars-Peter Clausen <lars@laprican.de>"])
        about.set_translator_credits(("translator-credits"))
        # about.set_copyright(_("Based on USP from S.Chanderbally"))
        about.set_logo(GdkPixbuf.Pixbuf.new_from_file("/usr/lib/linuxmint/mintMenu/icon.svg"))
        about.connect("response", lambda dialog, r: dialog.destroy())
        about.show()

    def showPreferences(self, action, userdata = None):
        Execute("/usr/lib/linuxmint/mintMenu/preferences.py")

    def showMenuEditor(self, action, userdata = None):
        if os.path.exists("/usr/bin/mozo"):
            Execute("mozo")
        elif os.path.exists("/usr/bin/menulibre"):
            Execute("menulibre")

    def showMenu(self, widget=None, event=None):
        if event == None or event.button == 1:
            self.toggleMenu()
        # show right click menu
        elif event.button == 3:
            self.create_menu()
        # allow middle click and drag
        elif event.button == 2:
            self.mainwin.hide()

    def toggleMenu(self):
        if self.applet.get_style_context().get_state() & Gtk.StateFlags.SELECTED:
            self.mainwin.hide()
        else:
            self.positionMenu()
            self.mainwin.show()
            self.wakePlugins()

    def wakePlugins(self):
        self.mainwin.wakePlugins()

    def positionMenu(self):
        # Get our own dimensions & position
        ourWidth  = self.mainwin.window.get_size()[0]
        ourHeight = self.mainwin.window.get_size()[1] + self.mainwin.offset

        # Get the dimensions/position of the widgetToAlignWith
        try:
            entryX = self.applet.get_window().get_origin().x
            entryY = self.applet.get_window().get_origin().y
        except:
            # In Betsy get_origin returns an unamed tuple so the code above fails
            entryX = self.applet.get_window().get_origin()[1]
            entryY = self.applet.get_window().get_origin()[2]

        entryWidth, entryHeight =  self.applet.get_allocation().width, self.applet.get_allocation().height
        entryHeight = entryHeight + self.mainwin.offset

        # Get the monitor dimensions
        display = self.applet.get_display()
        if (Gtk.MAJOR_VERSION, Gtk.MINOR_VERSION) >= (3, 22):
            monitor = display.get_monitor_at_window(self.applet.get_window())
            monitorGeometry = monitor.get_geometry()
        else:
            screen = display.get_default_screen()
            monitor = screen.get_monitor_at_window(self.applet.get_window())
            monitorGeometry = screen.get_monitor_geometry(monitor)

        applet_orient = self.applet.get_orient()
        if applet_orient == MatePanelApplet.AppletOrient.UP:
            newX = entryX
            newY = entryY - ourHeight
        elif applet_orient == MatePanelApplet.AppletOrient.DOWN:
            newX = entryX
            newY = entryY + entryHeight
        elif applet_orient == MatePanelApplet.AppletOrient.RIGHT:
            newX = entryX + entryWidth
            newY = entryY
        elif applet_orient == MatePanelApplet.AppletOrient.LEFT:
            newX = entryX - ourWidth
            newY = entryY

        # Adjust for offset if we reach the end of the screen
        # Bind to the right side
        if newX + ourWidth > (monitorGeometry.x + monitorGeometry.width):
            newX = (monitorGeometry.x + monitorGeometry.width) - ourWidth
            if applet_orient == MatePanelApplet.AppletOrient.LEFT:
                newX -= entryWidth

        # Bind to the left side
        if newX < monitorGeometry.x:
            newX = monitorGeometry.x
            if applet_orient == MatePanelApplet.AppletOrient.RIGHT:
                newX -= entryWidth

        # Bind to the bottom
        if newY + ourHeight > (monitorGeometry.y + monitorGeometry.height):
            newY = (monitorGeometry.y + monitorGeometry.height) - ourHeight
            if applet_orient == MatePanelApplet.AppletOrient.UP:
                newY -= entryHeight

        # Bind to the top
        if newY < monitorGeometry.y:
            newY = monitorGeometry.y
            if applet_orient == MatePanelApplet.AppletOrient.DOWN:
                newY -= entryHeight

        # Move window
        self.mainwin.window.move(newX, newY)

    # this callback is to create a context menu
    def create_menu(self):
        menu_file = "popup-without-edit.xml"
        action_group = Gtk.ActionGroup(name="context-menu")
        action = Gtk.Action(name="MintMenuPrefs", label=_("Preferences"), tooltip=None)
        action.connect("activate", self.showPreferences)
        action_group.add_action(action)
        if os.path.exists("/usr/bin/menulibre") or os.path.exists("/usr/bin/mozo"):
            action = Gtk.Action(name="MintMenuEdit", label=_("Edit menu"), tooltip=None)
            action.connect("activate", self.showMenuEditor)
            action_group.add_action(action)
            menu_file = "popup.xml"
        action = Gtk.Action(name="MintMenuReload", label=_("Reload plugins"), tooltip=None)
        action.connect("activate", self.mainwin.RegenPlugins)
        action_group.add_action(action)
        action = Gtk.Action(name="MintMenuAbout", label=_("About"), tooltip=None)
        action.connect("activate", self.showAboutDialog)
        action_group.add_action(action)
        action_group.set_translation_domain ("mintmenu")

        xml = os.path.join(os.path.join(os.path.dirname(__file__)), menu_file)
        self.applet.setup_menu_from_file(xml, action_group)

    def detect_desktop_environment (self):
        self.de = "mate"
        try:
            de = os.environ["XDG_CURRENT_DESKTOP"].lower()
            if de in ["gnome", "gnome-shell", "mate", "kde", "xfce"]:
                self.de = de
            elif de in ['cinnamon', 'x-cinnamon']:
                self.de = 'cinnamon'
            else:
                if os.path.exists("/usr/bin/caja"):
                    self.de = "mate"
                elif os.path.exists("/usr/bin/thunar"):
                    self.de = "xfce"
        except Exception as e:
            print(e)

def applet_factory(applet, iid, data):
    MenuWin(applet, iid)
    applet.show()
    return True

def quit_all(widget):
    Gtk.main_quit()
    sys.exit(0)

MatePanelApplet.Applet.factory_main("MintMenuAppletFactory", True,
                                    MatePanelApplet.Applet.__gtype__,
                                    applet_factory, None)

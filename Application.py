import yaybu.core.main
import os

import objc
from Foundation import NSObject, NSLog
from Cocoa import NSOpenPanel, NSOKButton
from ScriptingBridge import SBApplication

PYTHON_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "MacOS", "python"))
print PYTHON_PATH

CUSTOM_WINDOW_TITLE = u"\u2063" + "Yaybu"


def find_existing_yaybu_terminals():
    term = SBApplication.applicationWithBundleIdentifier_("com.apple.Terminal")
    for window in term.windows():
        for tab in window.tabs():
            if CUSTOM_WINDOW_TITLE == tab.customTitle():
                yield window, tab

def find_best_yaybu_terminal():
    for window, tab in find_existing_yaybu_terminals():
        if window.frontmost() and tab.selected():
            return window, tab
    for window, tab in find_existing_yaybu_terminals():
        if window.frontmost():
            return window, tab

    terminals = find_existing_yaybu_terminals()
    try:
        return terminals.next()
    except StopIteration:
        return None, None


class ApplicationDelegate(NSObject):

    def init(self):
        self = super(ApplicationDelegate, self).init()
        return self

    def application_openFile_(self, ns_app, path):
        terminal = SBApplication.applicationWithBundleIdentifier_("com.apple.Terminal")
        tab = terminal.doScript_in_("clear; %s -m yaybu.core.main -C %s; exit 0;" % (PYTHON_PATH, path), None)
        tab.setCustomTitle_(CUSTOM_WINDOW_TITLE )
        tab.setTitleDisplaysCustomTitle_(True)
        tab.setTitleDisplaysDeviceName_(False)
        tab.setTitleDisplaysFileName_(False)
        tab.setTitleDisplaysShellPath_(False)
        tab.setTitleDisplaysWindowSize_(False)

    def applicationDidFinishLaunching_(self, _):
        NSLog("applicationDidFinishLaunching_")

    def applicationWillTerminate_(self, sender):
        pass

    def applicationOpenUntitledFile_(self, _):
        window, tab = find_best_yaybu_terminal()
        if window and tab:
            tab.setSelected_(True)
            window.setFrontmost_(True)
            return

        panel = NSOpenPanel.openPanel()
        panel.setAllowsMultipleSelection_(False)
        panel.setCanCreateDirectories_(False)
        panel.setCanChooseDirectories_(False)
        panel.setCanChooseFiles_(True)

        yaybufile = None
        while not yaybufile or os.path.basename(yaybufile) != "Yaybufile":
            if panel.runModal() != NSOKButton:
                return
            yaybufile = panel.filename()

        self.application_openFile_(None, yaybufile)

    def quit_(self, notification):
        NSLog('quit...')

def setup_menus(app, delegate, updater):
   mainmenu = NSMenu.alloc().init()
   app.setMainMenu_(mainmenu)
   appMenuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Yaybu', '', '')
   mainmenu.addItem_(appMenuItem)

   appMenu = NSMenu.alloc().init()
   appMenuItem.setSubmenu_(appMenu)

   aboutItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('About My Sample App...', 'about', '')
   aboutItem.setTarget_(delegate)
   appMenu.addItem_(aboutItem)

   appMenu.addItemWithTitle_action_keyEquivalent_('Preferences...', 'prefs', '')

   cfu = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Check for updates...', 'checkForUpdates:', '')
   cfu.setTarget_(updater)
   appMenu.addItem_(cfu)

   quitItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'quit:', 'q')
   quitItem.setTarget_(delegate)
   appMenu.addItem_(quitItem)


if __name__ == '__main__':
    import os
    import objc
    base_path = os.path.join(os.path.dirname(os.getcwd()), 'Frameworks')
    bundle_path = os.path.abspath(os.path.join(base_path, 'Sparkle.framework'))
    objc.loadBundle('Sparkle', globals(), bundle_path=bundle_path)

    s = SUUpdater.sharedUpdater()

    app = NSApplication.sharedApplication()
    delegate = ApplicationDelegate.alloc().init()
    app.setDelegate_(delegate)

    setup_menus(app, delegate, s)

    from PyObjCTools import AppHelper
    AppHelper.runEventLoop()


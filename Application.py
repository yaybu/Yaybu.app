import os
import objc
from Foundation import NSObject, NSLog, NSAppleScript
from Foundation import NSUserDefaults, NSBundle
from Cocoa import NSInformationalAlertStyle, NSAlert, NSOpenPanel, NSOKButton
from ScriptingBridge import SBApplication

ARGV0 = os.environ['ARGVZERO']
YAYBUC = os.path.join(os.path.dirname(ARGV0), "YaybuShell")
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


def install_command_line_tools():
    target = '/usr/local/bin/yaybu'
    if os.path.exists(target):
        if os.path.islink(target) and os.readlink(target) == YAYBUC:
            NSLog("Command line tools already installed")
            return

    alert = NSAlert.alloc().init()
    alert.setMessageText_("Enable command line support?")
    alert.setInformativeText_("Yaybu can install a symlink at '/usr/local/bin/yaybu' allowing you to run yaybu from a terminal via the 'yaybu' command.")
    alert.setAlertStyle_(NSInformationalAlertStyle)
    alert.addButtonWithTitle_("Yes")
    alert.addButtonWithTitle_("No")

    if alert.runModal() == "No":
        return

    source = 'do shell script "test ! -d /usr/local/bin && mkdir -p /usr/local/bin; rm -f %s; ln -s %s %s" with administrator privileges' % (target, YAYBUC, target)
    script = NSAppleScript.alloc().initWithSource_(source)
    script.executeAndReturnError_(None)


class ApplicationDelegate(NSObject):

    def init(self):
        self = super(ApplicationDelegate, self).init()
        return self

    def application_openFile_(self, ns_app, path):
        terminal = SBApplication.applicationWithBundleIdentifier_("com.apple.Terminal")
        tab = terminal.doScript_in_("clear; %s; exit 0;" % (YAYBUC,), None)
        tab.setCustomTitle_(CUSTOM_WINDOW_TITLE )
        tab.setTitleDisplaysCustomTitle_(True)
        tab.setTitleDisplaysDeviceName_(False)
        tab.setTitleDisplaysFileName_(False)
        tab.setTitleDisplaysShellPath_(False)
        tab.setTitleDisplaysWindowSize_(False)

    def applicationDidFinishLaunching_(self, _):
        currentVersion = NSBundle.mainBundle().infoDictionary()["CFBundleVersion"]
        NSLog("Starting Yaybu version %s" % currentVersion)

        userDefaults = NSUserDefaults.standardUserDefaults()
        lastVersion = userDefaults.stringForKey_("version")

        if not lastVersion:
            NSLog("Detected that this is a first run!")
            self.applicationFirstRun()

        if not lastVersion or lastVersion != currentVersion:
            NSLog("Version changed from %s to %s" % (lastVersion, currentVersion))
            self.applicationVersionChanged(lastVersion, currentVersion)
            userDefaults.setObject_forKey_(currentVersion, "version")

    def applicationFirstRun(self):
        install_command_line_tools()

    def applicationVersionChanged(self, lastVersion, currentVersion):
        pass

    def applicationWillTerminate_(self, sender):
        pass

    def applicationOpenUntitledFile_(self, _):
        window, tab = find_best_yaybu_terminal()
        if window and tab:
            tab.setSelected_(True)
            window.setFrontmost_(True)
            term = SBApplication.applicationWithBundleIdentifier_("com.apple.Terminal")
            term.activate()
            return
        self.openYaybufile_(None)

    def openYaybufile_(self, notification):
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

    def installCommandLineTools_(self, notification):
        install_command_line_tools()

    def quit_(self, notification):
        NSLog('User request application close...')
        NSApplication.sharedApplication().terminate_(None)

def setup_menus(app, delegate, updater):
    mainmenu = NSMenu.alloc().init()
    app.setMainMenu_(mainmenu)
    appMenuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Yaybu', '', '')
    mainmenu.addItem_(appMenuItem)

    appMenu = NSMenu.alloc().init()
    appMenuItem.setSubmenu_(appMenu)

    # aboutItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('About Yaybu...', 'about', '')
    # aboutItem.setTarget_(delegate)
    # appMenu.addItem_(aboutItem)

    # appMenu.addItemWithTitle_action_keyEquivalent_('Preferences...', 'prefs', '')

    openFile = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        'Open...',
        'openYaybufile:',
        '',
        )
    openFile.setTarget_(delegate)
    appMenu.addItem_(openFile)


    iclt = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        'Install command line tools...',
        'installCommandLineTools:',
        '',
        )
    iclt.setTarget_(delegate)
    appMenu.addItem_(iclt)

    cfu = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        'Check for updates...',
        'checkForUpdates:',
        '')
    cfu.setTarget_(updater)
    appMenu.addItem_(cfu)

    quitItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        'Quit', 'quit:', 'q',
        )
    quitItem.setTarget_(delegate)
    appMenu.addItem_(quitItem)


if __name__ == '__main__':
    base_path = os.path.join(os.path.dirname(os.environ['RESOURCEPATH']), 'Frameworks')
    bundle_path = os.path.abspath(os.path.join(base_path, 'Sparkle.framework'))
    objc.loadBundle('Sparkle', globals(), bundle_path=bundle_path)

    s = SUUpdater.sharedUpdater()

    app = NSApplication.sharedApplication()
    delegate = ApplicationDelegate.alloc().init()
    app.setDelegate_(delegate)

    setup_menus(app, delegate, s)

    from PyObjCTools import AppHelper
    AppHelper.runEventLoop()


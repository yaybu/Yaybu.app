VERSION = "0.0.0"

import glob
import itertools
import os
import shutil
import StringIO
import subprocess
import sys

from setuptools import setup, find_packages
import pkg_resources
from py2app.util import strip_files
from py2app.build_app import py2app


setuptools_sitefix = """
import site
site.USER_BASE = None
site.USER_SITE = None

import os
os.environ['PATH'] = '%s:%s' % (
    os.path.join(os.environ['RESOURCEPATH'], 'bin'),
    os.environ['PATH'],
    )
"""

def system(command, cwd=os.getcwd()):
    p = subprocess.Popen(
        command,
        cwd = cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
        )
    stdout, stderr = p.communicate()
    return stdout


class YaybuAppBuild(py2app):

    user_options = py2app.user_options + [
        ("build-number=",       "b", "build number"),
        ("signing-identity=",        "s", "identity to sign app with"),
        ]

    def setup_distribution(self):
        #self.distribution.app = ['Application.py']
        #self.distribution.packages = [
        #    'yaybu.core.main',
        #    ]
        pass

    def initialize_options(self):
        self.signing_identity = None
        self.build_number = 0
        py2app.initialize_options(self)

    def finalize_options(self):
        py2app.finalize_options(self)
        self.setup_distribution()

    def recipe_distutils(self, py2app, mf):
        if not mf.findNode('distutils.command.install'):
            return None
        return {"prescripts": [StringIO.StringIO(setuptools_sitefix)]}

    def recipe_egg_info(self, py2app, mf):
        loader_files = []
        for d in pkg_resources.working_set:
            node = mf.findNode(d.project_name)
            if not node:
                node = mf.findNode(d.project_name.lower())
            if node:
                print "  -> %s.egg-info" % d.project_name
                with open("/tmp/%s.egg-info" % d.project_name, "w") as fp:
                    fp.write("Metadata-Version: 1.0\n")
                    fp.write("Name: %s\n" % d.project_name)
                    fp.write("Version: %s\n" % d.version)
                loader_files.append('/tmp/%s.egg-info'% d.project_name)
        self.egg_info_files = loader_files
        return None

    def recipe_yaybu(self, py2app, mf):
        m = mf.findNode('yaybu')
        if not m:
            return None
        mf.import_hook("yaybu.provisioner.resources", m, ['*'])
        mf.import_hook("yaybu.provisioner.providers", m, ['*'])
        return {}

    def collect_recipedict(self):
        dict = py2app.collect_recipedict(self)
        dict.update({
            "egg_info": self.recipe_egg_info,
            "yaybu": self.recipe_yaybu,
            "distutils": self.recipe_distutils,
            })
        return dict

    def strip_files(self, files):
        # This method is originally defined in py2app, but we have to bodge it to not strip Sparkle.framework :-/
        unstripped = 0
        stripfiles = []
        for fn in files:
            if "Sparkle.framework" in fn and "relaunch" in fn:
                print "not stripping '%s'" % fn
                continue
            unstripped += os.stat(fn).st_size
            stripfiles.append(fn)
            print 'stripping %s' % os.path.basename(fn)
        strip_files(stripfiles, dry_run=self.dry_run, verbose=self.verbose)
        stripped = 0
        for fn in stripfiles:
            stripped += os.stat(fn).st_size
        print 'stripping saved %d bytes (%d / %d)', unstripped - stripped, stripped, unstripped

    def update_binary_wrappers(self):
        bindir = os.path.realpath(os.path.join(self.resdir, "../MacOS"))
        for b in os.listdir(bindir):
            if b == "python":
                continue
            system(["gcc", "main.c", "-o", os.path.join(bindir, b)])

    def sort_out_egg_metadata(self):
        print "Generating fake egg metadata..."
        site_packages = os.path.join(self.resdir, "lib", "python2.7", "site-packages")
        if not os.path.exists(site_packages):
            os.makedirs(site_packages)
        for egg_info in self.egg_info_files:
            self.copy_file(
                egg_info,
                os.path.join(site_packages, os.path.basename(egg_info)),
                )
    def fix_bin_permissions(self):
        os.chmod(os.path.join(self.resdir, "../Frameworks/Sparkle.framework/Versions/A/Resources/relaunch"), 0755)

    def fix_sparkle(self):
        print "Fixing sparkle install name"
        path = os.path.join(self.resdir, "..", "Frameworks/Sparkle.framework/Versions/A/Sparkle")
        # old_install_name = "@executable_path/../Frameworks/Sparkle.framework/Versions/A/Sparkle"
        new_install_name = "@loader_path/../Frameworks/Sparkle.framework/Versions/A/Sparkle"
        # system(['install_name_tool', '-change', old_install_name, new_install_name, path])
        system(['install_name_tool', '-id', new_install_name, path])

    def sign_path(self, path):
        print "Signing '%s'" % path
        bundle_root = os.path.abspath(os.path.join(self.resdir, "..", ".."))
        print system([
            'codesign',
            '--force', '--verify', '--verbose',
            '--sign', self.signing_identity,
            # '--entitlements', 'path/to/entitlements',
            os.path.abspath(os.path.join(bundle_root, path)),
            ])

    def sign(self):
        if not self.signing_identity:
            return
        self.sign_path('Contents/Frameworks/Sparkle.framework/Versions/A')
        self.sign_path('Contents/Frameworks/Python.framework/Versions/2.7')
        self.sign_path('Contents/MacOS/python')
        self.sign_path('Contents/MacOS/Yaybu')
        self.sign_path('Contents/MacOS/YaybuShell')
        self.sign_path('.')

    def build_dmg(self):
        print "Building DMG staging..."
        name = self.distribution.get_name()

        image_staging = os.path.join(self.dist_dir, "dmg-staging")
        image_path = os.path.join(self.dist_dir, "%s.dmg" % name)
        image_raw = os.path.join(self.dist_dir, "raw.%s.dmg" % name)
        image_tmp = os.path.join(self.dist_dir, "tmp.%s.dmg" % name)

        if os.path.exists(image_path):
            os.unlink(image_path)

        if os.path.exists(image_staging):
            shutil.rmtree(image_staging)

        os.mkdir(image_staging)
        os.mkdir(os.path.join(image_staging, ".background"))
        shutil.copyfile("background.png", os.path.join(image_staging, ".background", "background.png"))
        shutil.copyfile("DS_Store", os.path.join(image_staging, ".DS_Store"))
        system(["SetFile", "-a", "V", os.path.join(image_staging, ".DS_Store")])
        os.symlink("/Applications", os.path.join(image_staging, "Applications"))
        shutil.copytree(
            os.path.join(self.dist_dir, "%s.app" % name),
            os.path.join(image_staging, "%s.app" % name),
            symlinks=True,
            )
        # Set up volume icon as per http://endrift.com/page/dmg-files-volume-icons-cli
        shutil.copyfile("Resources/Yaybu.icns", os.path.join(image_staging, ".VolumeIcon.icns"))
        system(["SetFile", "-c", "icnC", os.path.join(image_staging, ".VolumeIcon.icns")])

        print "Building DMG image..."
        system(["hdiutil", "create", "-srcfolder", image_staging, "-volname", name, "-format", "UDRW", image_tmp])
        system(["hdiutil", "attach", image_tmp, "-mountpoint", image_raw])
        system(["SetFile", "-a", "C", image_raw])
        system(["hdiutil", "detach", image_raw])
        system(["hdiutil", "convert", image_tmp, "-format", "UDBZ", "-o", image_path])
        system(["hdiutil", "internet-enable", "-yes", image_path])
        os.unlink(image_tmp)

    def build_zip(self):
        print "Building ZIP image (for Sparkle updates)"
        p = os.path.join(self.dist_dir, "Yaybu.zip")
        if os.path.exists(p):
            os.unlink(p)

        system(["zip", "-ry9", "Yaybu.zip", "Yaybu.app"], cwd=self.dist_dir)
        signature = system(["sh", "-c", "cat Yaybu.zip | openssl dgst -sha1 -binary | openssl dgst -dss1 -sign ~/dsa_priv.pem | openssl enc -base64"], cwd=self.dist_dir)
        signature = signature.strip()

        print "Sparkle signature =", signature
        with open(p + ".sig", "w") as fp:
            fp.write(signature)

    def setup_plist(self):
        version = pkg_resources.get_distribution('Yaybu').version

        self.plist = {
            "CFBundleVersion": self.build_number,
            "CFBundleShortVersionString": "%s (%s)" % (version, self.build_number),
            "CFBundleIdentifier" : "com.yaybu.Yaybu",
            "CFBundleDocumentTypes": [{
                "LSItemContentTypes": ["public.data"],
                "LSHandlerRank": "Owner",
                }],
            "SUFeedURL": "http://yaybu.com/nightlies/osx/appcast.xml",
            "SUPublicDSAKeyFile": "dsa_pub.pem",
            }

    def run(self):
        self.iconfile = "Resources/Yaybu.icns"

        self.setup_plist()
        py2app.run(self)

    def run_normal(self):
        py2app.run_normal(self)

        self.update_binary_wrappers()
        self.sort_out_egg_metadata()
        self.fix_bin_permissions()
        self.fix_sparkle()
        self.sign()
        self.build_dmg()
        self.build_zip()

        print "Yaybu.app = ", system(["du", "-sh", os.path.join(self.dist_dir, "Yaybu.app")]).strip().split()[0]
        print "Yaybu.dmg = ", system(["du", "-sh", os.path.join(self.dist_dir, "Yaybu.dmg")]).strip().split()[0]
        print "Yaybu.zip = ", system(["du", "-sh", os.path.join(self.dist_dir, "Yaybu.zip")]).strip().split()[0]


setup(
    name = "Yaybu",
    version = VERSION,
    packages = find_packages(),
    author = "John Carr",
    author_email = "john.carr@unrouted.co.uk",
    description = "Yaybu service orchestration + deployment",
    license = "Apache",
    keywords = "python",
    app=["Application.py"],
    data_files = [
        "Resources/Yaybu.icns",
        "Resources/dsa_pub.pem",
        "Resources/cacert.pem",
        ],
    cmdclass = {
            'py2app': YaybuAppBuild,
    },
    options=dict(py2app=dict(
        frameworks=["Sparkle.framework"],
        extra_scripts=['YaybuShell.py'],
        no_chdir=True,
    )),
)


import json
import os
import sys
import ConfigParser
import StringIO
from docutils.core import publish_parts
from lxml import etree
import pkg_resources

from jinja2 import Environment, FileSystemLoader
from libcloud.storage.types import Provider
from libcloud.storage.providers import get_driver
import libcloud.security

def get_changelog():
    output = []
    for heading, filename in [("Yaybu", "src/yaybu/CHANGES"), ("Yay", "src/yay/CHANGES")]:
        output.append("<h1>%s</h1>\n" % heading)
        source = open(filename).read()
        parts = publish_parts(
            source=source,
            writer_name="html",
            settings_overrides={
                'initial_header_level': 2,
                },
            )
        html = parts['html_body']
        root = etree.parse(StringIO.StringIO(html), parser=etree.HTMLParser())
        elem = root.xpath("/html/body/div/div")[0]
        output.extend(etree.tostring(e) for e in elem)
    return "\n".join(output)


if not os.path.exists("dist") or not os.path.exists("nightlies"):
    print "cwd wrong? cannot continue."
    sys.exit(1)

# Gather any keys and container details
config = ConfigParser.ConfigParser()
config.read(os.path.expanduser("~/yaybu-%s.cfg" % sys.argv[2]))

base_directory = config.get("container", "directory").rstrip("/")
base_url = config.get("container", "url").rstrip("/")

# Collect metadata about this release
release = {}
release['number'] = sys.argv[1]
release['name'] = base_directory + "/Yaybu-%s.zip" % release['number']
release['version'] = pkg_resources.get_distribution('Yaybu').version
release['url'] = base_url + "/Yaybu-%s.zip" % release['number']
release['size'] = os.stat("dist/Yaybu.zip").st_size
release['changelog'] = get_changelog()

with open("dist/Yaybu.zip.sig") as fp:
    release['signature'] = fp.read()

# Load up metadata about existing releases and add new release
# Releases are sorted newest first
releases = []
if os.path.exists("%s.json" % sys.argv[2]):
    releases = json.load(open("%s.json" % sys.argv[2]))
releases.insert(0, release)

# Only keep the past 10 releases
releases = releases[:10]

# Ensure we can fill in teh template before we connect to cloud storage service
env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
template = env.get_template('appcast.xml.j2')
appcast = template.render(
    url = config.get("container", "url"),
    releases = releases,
    )

# OSX doesn't have certs in a format libcloud can use directly
libcloud.security.CA_CERTS_PATH = [
    os.path.abspath("Resources/cacert.pem"),
    ]

# Connect to cloud storage service
Driver = get_driver(getattr(Provider, config.get("storage", "driver")))
driver = Driver(config.get("storage", "key"), config.get("storage", "secret"))
container = driver.get_container(config.get("container", "name"))

# Upload the latest dmg
print "Uploading latest dmg as %s/Yaybu-latest.dmg" % config.get("container", "url").rstrip("/")
with open("dist/Yaybu.dmg", "rb") as fp:
    driver.upload_object_via_stream(iterator=fp, container=container, object_name=base_directory + "/Yaybu-latest.dmg")

# Upload the latest build
print "Uploading latest dmg as %s" % release['url']
with open("dist/Yaybu.zip", "rb") as fp:
    driver.upload_object_via_stream(iterator=fp, container=container, object_name=release['name'])

# Workaround libcloud 378
driver.supports_chunked_encoding = False
driver.supports_s3_multipart_upload = False

# Publish an updated appcast
print "Uploading appcast"
appcast_name = base_directory + "/appcast.xml"
driver.upload_object_via_stream(iterator=StringIO.StringIO(appcast), container=container, object_name=appcast_name)

objects_to_keep = set(r['name'] for r in releases)
objects_to_keep.add('%s/appcast.xml' % base_directory)
objects_to_keep.add('%s/Yaybu-latest.dmg' % base_directory)

for obj in container.list_objects():
    if not obj.name.startswith(base_directory + "/"):
        continue
    if obj.name in objects_to_keep:
        continue
    print "Deleting %s" % obj.name
    obj.delete()

# Remember this release so the appcast contains past releases
with open("%s.json" % sys.argv[2], "w") as fp:
    json.dump(releases, fp, indent=4)


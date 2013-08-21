
import json
import os
import sys
import ConfigParser
import StringIO

from jinja2 import Environment, FileSystemLoader
from libcloud.storage.types import Provider
from libcloud.storage.providers import get_driver
import libcloud.security


if not os.path.exists("dist") or not os.path.exists("nightlies"):
    print "cwd wrong? cannot continue."
    sys.exit(1)

# Gather any keys and container details
config = ConfigParser.ConfigParser()
config.read(os.path.expanduser("~/yaybu-nightlies.cfg"))

# Collect metadata about this release
release = {}
release['number'] = sys.argv[1]
release['name'] = config.get("container", "directory").rstrip("/") + "/" + "Yaybu-%s.zip" % release['number']
release['url'] = config.get("container", "url").rstrip("/") + "/" + "Yaybu-%s.zip" % release['number']
release['size'] = os.stat("dist/Yaybu.zip").st_size

with open("dist/Yaybu.zip.sig") as fp:
    release['signature'] = fp.read()

# Load up metadata about existing releases and add new release
# Releases are sorted newest first
releases = []
if os.path.exists("nightlies.json"):
    releases = json.load(open("nightlies.json"))
releases.insert(0, release)

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

# Upload the latest build
with open("dist/Yaybu.zip", "rb") as fp:
    driver.upload_object_via_stream(iterator=fp, container=container, object_name=release['name'])

# Workaround libcloud 378
driver.supports_chunked_encoding = False
driver.supports_s3_multipart_upload = False

# Publish an updated appcast
appcast_name = config.get("container", "directory").rstrip("/") + "/" + "appcast.xml"
driver.upload_object_via_stream(iterator=StringIO.StringIO(appcast), container=container, object_name=appcast_name)

# Remember this release so the appcast contains past releases
with open("nightlies.json", "w") as fp:
    json.dump(releases, fp, indent=4)


from yaybu.core.main import main

# These imports are to force modules into site-packages.zip
# (yay py2app)
from yay import lextab
from yay import parsetab

# CA certs on darwin are in the system keyring - they can be readily accessed with commands like:
#   security export -k /System/Library/Keychains/SystemCACertificates.keychain -t certs
# However i'm not sure how libcloud/python can take a stream of certs - it looks like the certs have to exist on disk!!
# So tell libcloud where our bundled certs are
import os
import libcloud.security
libcloud.security.CA_CERTS_PATH.append(
    os.path.join(os.environ["RESOURCEPATH"], "cacert.pem")
        )

# yaybu/yaybu#117 - pricing.json is loaded in a naive way by libcloud that
# doesnt allow for the objects in PYTHONPATH to be zips. So ship it out of
# library.zip in RESOURCEPATH
import libcloud.pricing
def get_pricing_file_path(file_path=None):
    return os.path.join(os.environ["RESOURCEPATH"], "pricing.json")
libcloud.pricing.get_pricing_file_path = get_pricing_file_path


if __name__ == "__main__":
    main()


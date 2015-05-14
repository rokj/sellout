# -*- coding:utf-8 -*-
import os

import django
import regex
import requests
import zipfile, os.path
from contact.models import ContactRegistry
import settings

import common.globals as g

django.setup()

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webpos.settings")

download_dir = '/home/rokj/tmp/durs'

files = {
    'durs': {
        'fizicne_osebe': {'url': 'http://datoteke.durs.gov.si/DURS_zavezanci_FO.zip', 'filename': 'DURS_zavezanci_FO.txt'},
        'dejavnosti': {'url': 'http://datoteke.durs.gov.si/DURS_zavezanci_DEJ.zip', 'filename': 'DURS_zavezanci_DEJ.txt'},
        'pravne_osebe': {'url': 'http://datoteke.durs.gov.si/DURS_zavezanci_PO.zip', 'filename': 'DURS_zavezanci_PO.txt'}
    }
}

def unzip(source_filename, dest_dir):
    with zipfile.ZipFile(source_filename) as zf:
        for member in zf.infolist():
            # Path traversal defense copied from
            # http://hg.python.org/cpython/file/tip/Lib/http/server.py#l789
            words = member.filename.split('/')
            path = dest_dir
            for word in words[:-1]:
                drive, word = os.path.splitdrive(word)
                head, word = os.path.split(word)
                if word in (os.curdir, os.pardir, ''): continue
                path = os.path.join(path, word)
            zf.extract(member, path)

def download(url, to_file):
    """
    downloads and unzips files
    """
    filename = url.split("/")[-1]
    filename = download_dir + "/" + filename

    with open(filename, 'wb') as handle:
        response = requests.get(url, stream=True)

        if not response.ok:
            return False

        for block in response.iter_content(1024):
            if not block:
                break

            handle.write(block)

    unzip(filename, download_dir)

    return True

def import_durs_fo(filename):
    with open(filename) as f:
        lines = f.readlines()

    for line in lines:
        davcna_stevilka = line[2:9]
        ime_priimek = line[11:72].strip()
        if settings.DEBUG:
            print("ime priimek: |%s|" % (ime_priimek))

        __naslov = line[72:184].split(',')
        naslov = __naslov[0].strip()
        if settings.DEBUG:
            print("naslov: |%s|" % (naslov))

        postna_stevilka = ""
        posta = ""

        if naslov != "":
            postna_stevilka = regex.findall(r'\d+', __naslov[-1])[0]
            if settings.DEBUG:
                print("postna stevilka: |%s|" % (postna_stevilka))

            posta = __naslov[1].replace(postna_stevilka, "").strip()
            if settings.DEBUG:
                print("posta: |%s|" % (posta))

        try:
            contact_registry = ContactRegistry.objects.get(vat=davcna_stevilka)
            contact_registry.first_name = ime_priimek.split(" ")[0]
            contact_registry.last_name = ime_priimek.split(" ")[1]
            contact_registry.postcode = postna_stevilka,
            contact_registry.city = posta
            contact_registry.country = "SI"
            contact_registry.save()
        except ContactRegistry.DoesNotExist:
            contact_registry = ContactRegistry(
                type=g.CONTACT_TYPES[0][0],
                first_name=ime_priimek.split(" ")[0],
                last_name=ime_priimek.split(" ")[1],
                postcode=postna_stevilka,
                city=posta,
                country="SI",
                vat=davcna_stevilka
            )
            contact_registry.save()




def import_durs_dej(filename):
    pass

def import_durs_po(filename):
    pass

for key, fileinfo in files['durs'].iteritems():
    if key == 'fizicne_osebe':
        download(fileinfo['url'], fileinfo['filename'])
        import_durs_fo(download_dir + "/" + fileinfo['filename'])
    elif key == 'dejavnosti':
        import_durs_dej(fileinfo['filename'])
    elif key == 'pravne_osebe':
        import_durs_po(fileinfo['filename'])




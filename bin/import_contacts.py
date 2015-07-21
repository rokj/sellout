# -*- coding:utf-8 -*-
import json
import os

import django
import regex
import requests
import zipfile, os.path

django.setup()

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webpos.settings")

from registry.models import ContactRegistry
import settings

import common.globals as g

download_dir = '/home/rokj/tmp/durs'

files = {
    'durs': {
        'fizicne_osebe': {'url': 'http://datoteke.durs.gov.si/DURS_zavezanci_FO.zip', 'filename': 'DURS_zavezanci_FO.txt'},
        'dejavnosti': {'url': 'http://datoteke.durs.gov.si/DURS_zavezanci_DEJ.zip', 'filename': 'DURS_zavezanci_DEJ.txt'},
        'pravne_osebe': {'url': 'http://datoteke.durs.gov.si/DURS_zavezanci_PO.zip', 'filename': 'DURS_zavezanci_PO.txt'}
    }
}

settings.DEBUG = False

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
            postna_stevilka = regex.findall(r'\d+', __naslov[-1])

            if len(postna_stevilka) > 0:
                postna_stevilka = postna_stevilka[0]
                posta = __naslov[1].replace(postna_stevilka, "").strip()

                if settings.DEBUG:
                    print("posta: |%s|" % (posta))
                    print("postna stevilka: |%s|" % (postna_stevilka))

        try:
            contact_registry = ContactRegistry.objects.get(vat=davcna_stevilka)
            contact_registry.first_name = ime_priimek.split(" ")[0]
            contact_registry.last_name = ime_priimek.split(" ")[1]
            contact_registry.street_address = naslov.decode("utf-8", "replace")
            contact_registry.postcode = postna_stevilka
            contact_registry.city = posta
            contact_registry.country = "SI"
            contact_registry.vat = davcna_stevilka
            contact_registry.save()
        except ContactRegistry.DoesNotExist:
            contact_registry = ContactRegistry(
                type=g.CONTACT_TYPES[0][0],
                first_name=ime_priimek.split(" ")[0],
                last_name=ime_priimek.split(" ")[1],
                street_address=naslov.decode("utf-8", "replace"),
                postcode=postna_stevilka,
                city=posta,
                country="SI",
                vat=davcna_stevilka
            )
            contact_registry.save()

def import_durs_dej(filename):
    with open(filename) as f:
        lines = f.readlines()

    for line in lines:
        davcna_stevilka = line[0:8]
        if settings.DEBUG:
            print("davcna stevilka: |%s|" % (davcna_stevilka))

        maticna_stevilka = line[9:19]
        if settings.DEBUG:
            print("maticna stevilka: |%s|" % (maticna_stevilka))

        dejavnost = line[20:26]
        if settings.DEBUG:
            print("dejavnost: |%s|" % (dejavnost))

        podjetje = line[27:128].strip()
        if settings.DEBUG:
            print("podjetje: |%s|" % (podjetje.decode("utf-8", "replace")))

        __naslov = line[129:242].strip().split(',')
        naslov = __naslov[0].strip()
        if settings.DEBUG:
            print("naslov: |%s|" % (naslov))

        postna_stevilka = ""
        posta = ""

        if naslov != "":
            postna_stevilka = regex.findall(r'\d+', __naslov[-1])

            if len(postna_stevilka) > 0:
                postna_stevilka = postna_stevilka[0]
                posta = __naslov[1].replace(postna_stevilka, "").strip()

                if settings.DEBUG:
                    print("postna stevilka: |%s|" % (postna_stevilka))
                    print("posta: |%s|" % (posta))

        additional_info = {
            'maticna_stevilka': maticna_stevilka,
            'dejavnost': dejavnost
        }

        try:
            contact_registry = ContactRegistry.objects.get(vat=davcna_stevilka)
            contact_registry.company_name = podjetje.decode("utf-8", "replace")
            contact_registry.street_address = naslov.decode("utf-8", "replace")
            contact_registry.postcode = postna_stevilka
            contact_registry.city = posta
            contact_registry.country = "SI"
            contact_registry.vat = davcna_stevilka
            contact_registry.additional_info = json.dumps(additional_info)
            contact_registry.save()
        except ContactRegistry.DoesNotExist:
            contact_registry = ContactRegistry(
                type=g.CONTACT_TYPES[0][1],
                company_name=podjetje.decode("utf-8", "replace"),
                postcode=postna_stevilka,
                street_address=naslov.decode("utf-8", "replace"),
                city=posta,
                country="SI",
                vat=davcna_stevilka,
                additional_info=json.dumps(additional_info)
            )
            contact_registry.save()

def import_durs_po(filename):
    with open(filename) as f:
        lines = f.readlines()

    for line in lines:
        davcni_zavezanec = line[0:3]
        if "*" in davcni_zavezanec:
            davcni_zavezanec = "yes"
        else:
            davcni_zavezanec = "no"

        if settings.DEBUG:
            print("davcni zavezanec: |%s|" % (davcni_zavezanec))

        davcna_stevilka = line[4:11]
        if settings.DEBUG:
            print("davcna stevilka: |%s|" % (davcna_stevilka))

        maticna_stevilka = line[13:22]
        if settings.DEBUG:
            print("maticna stevilka: |%s|" % (maticna_stevilka))

        dejavnost = line[35:41]
        if settings.DEBUG:
            print("dejavnost: |%s|" % (dejavnost))

        podjetje = line[42:143].strip()
        if settings.DEBUG:
            print("podjetje: |%s|" % (podjetje.decode("utf-8", "replace")))

        __naslov = line[144:257].strip().split(',')
        naslov = __naslov[0].strip()
        if settings.DEBUG:
            print("naslov: |%s|" % (naslov))

        postna_stevilka = ""
        posta = ""

        if naslov != "":
            postna_stevilka = regex.findall(r'\d+', __naslov[-1])

            if len(postna_stevilka) > 0:
                postna_stevilka = postna_stevilka[0]
                posta = __naslov[1].replace(postna_stevilka, "").strip()

                if settings.DEBUG:
                    print("postna stevilka: |%s|" % (postna_stevilka))
                    print("posta: |%s|" % (posta))

        additional_info = {
            'maticna_stevilka': maticna_stevilka,
            'dejavnost': dejavnost
        }

        try:
            contact_registry = ContactRegistry.objects.get(vat=davcna_stevilka)
            contact_registry.company_name = podjetje.decode("utf-8", "replace")
            contact_registry.street_address = naslov.decode("utf-8", "replace")
            contact_registry.postcode = postna_stevilka
            contact_registry.city = posta
            contact_registry.country = "SI"
            contact_registry.vat = davcna_stevilka
            contact_registry.tax_payer = davcni_zavezanec
            contact_registry.additional_info = json.dumps(additional_info)
            contact_registry.save()
        except ContactRegistry.DoesNotExist:
            contact_registry = ContactRegistry(
                type=g.CONTACT_TYPES[0][1],
                company_name=podjetje.decode("utf-8", "replace"),
                street_address=naslov.decode("utf-8", "replace"),
                postcode=postna_stevilka,
                city=posta,
                country="SI",
                vat=davcna_stevilka,
                tax_payer = davcni_zavezanec,
                additional_info=json.dumps(additional_info),
            )
            contact_registry.save()

for key, fileinfo in files['durs'].iteritems():
    if key == 'fizicne_osebe':
        print "Doing fizicne osebe"
        download(fileinfo['url'], fileinfo['filename'])
        import_durs_fo(download_dir + "/" + fileinfo['filename'])
        print "Finished fizicne osebe"
    elif key == 'dejavnosti':
        print "Doing po dejavnostih"
        download(fileinfo['url'], fileinfo['filename'])
        import_durs_dej(download_dir + "/" + fileinfo['filename'])
        print "Finished po dejavnostih"
    elif key == 'pravne_osebe':
        print "Doing pravne osebe"
        download(fileinfo['url'], fileinfo['filename'])
        import_durs_po(download_dir + "/" + fileinfo['filename'])
        print "Finished pravne osebe"




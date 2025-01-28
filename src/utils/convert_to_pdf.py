import sys
import subprocess
import re


def convert_to_pdf(folder, source, timeout=None):
    args = [
        libreoffice_exec(),
        '--headless',
        '--convert-to', 'pdf',
        '--outdir', folder,
        source
    ]

    process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    re.search('-> (.*?) using filter', process.stdout.decode())


def libreoffice_exec():
    if sys.platform == 'darwin':
        return '/Applications/LibreOffice.app/Contents/MacOS/soffice'

    elif sys.platform == "linux":
        return '/usr/bin/soffice'

    return 'libreoffice'

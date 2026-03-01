import os
from pypdf import PdfWriter, PdfReader

def merge(pwd):
    pdfs = [
        'media/input/fic1.pdf',
        'media/input/fic2.pdf',
        'media/input/fic3.pdf',
        'media/input/fic4.pdf',
        ]


    merger = PdfWriter()

    for pdf in pdfs:
        merger.append(pdf)

    output_filename = "media/output/merged.pdf"

    merger.write(output_filename)
    merger.close()

    reader = PdfReader(output_filename)
    writer = PdfWriter(clone_from=reader)

    writer.encrypt(pwd, algorithm="AES-256")

    encrypt_filename = "media/output/merged-encrypt.pdf"

    writer.write(encrypt_filename)

def crypt(pwd,indirname):
    
    outdirname =  indirname + "output2/"
    ficnum = 1
    for filename in os.listdir(indirname):
        if filename.endswith(".pdf"):
            reader = PdfReader(indirname + filename)
            writer = PdfWriter(clone_from=reader)
            writer.encrypt(pwd, algorithm="AES-256")
            encrypt_filename = f"{outdirname}{ficnum:02}.pdf"
            ficnum += 1
            writer.write(encrypt_filename)

if __name__ == "__main__":
    # merge('12345')
    indirname = "/home/"
    crypt('12345',indirname)
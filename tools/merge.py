from pypdf import PdfWriter, PdfReader

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

writer.encrypt("vplWta", algorithm="AES-256")

encrypt_filename = "media/output/merged-encrypt.pdf"

writer.write(encrypt_filename)

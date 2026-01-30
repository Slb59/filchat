#filchat.views.py

import os
import zipfile
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse
from django.conf import settings

from .models import FilChat
from .utils import decoupe_chat, creer_archive_output

def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        chat_file = FilChat(file=request.FILES['file'])
        chat_file.save()
        return redirect('process_file', file_id=chat_file.id)
    return render(request, 'filchat/upload.html', {'current_year': datetime.now().year})

def process_file(request, file_id):
    chat_file = FilChat.objects.get(id=file_id)
    if not chat_file.processed:
        try:
            file_path = chat_file.file.path
            output_dir = os.path.join(settings.MEDIA_ROOT, 'output', str(chat_file.id))
            os.makedirs(output_dir, exist_ok=True)

            # decoupe le fichier de chat
            decoupe_chat(file_path, output_dir)
            # cree une archive
            archive_path = creer_archive_output(output_dir)
            chat_file.processed = True
            chat_file.save()
            return render(
                request, 
                'filchat/results.html', 
                {'file_id': file_id, 'archive_path': archive_path}
            )
        except Exception as e:
            return HttpResponse(f"Erreur lors du traitement: {str(e)}", status=500)
    return render(request, 'filchat.results.html',
        {'file_id': file_id, 'current_year': datetime.now().year}
    )

def download_file(request, file_id):
    chat_file = FilChat.objects.get(id=file_id)
    archive_path = os.path.join(settings.MEDIA_ROOT, 'output', str(chat_file.id), 'archive.zip')
    return FileResponse(open(archive_path, 'rb'), as_attachment=True) 
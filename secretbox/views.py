from datetime import datetime

from django.shortcuts import render


def home(request):
    return render(request, 'secretbox/secretbox_page.html', {'current_year': datetime.now().year})


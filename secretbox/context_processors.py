from django.conf import settings

def environment_context(request):
    return {
        'DEBUG': settings.DEBUG,
        'ENVIRONMENT': getattr(settings, 'ENVIRONMENT', 'dev'),
    }

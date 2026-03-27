from django.shortcuts import render

from .models import Custom404Page, Custom500Page


def custom_error_view(request, exception, error_code=404, page=None):
    """
    Returns a different error view depending on the site.
    """
    return render(
        request,
        f"{error_code}.html",
        {'page': page},
        status=error_code,
    )


def custom_403_view(request, exception=None):
    """
    Returns a different 403 view depending on the site.
    """
    return custom_error_view(request, exception, error_code=403)


def custom_404_view(request, exception=None):
    """
    Returns a different 404 view depending on the site.
    """    
    custom_404_page = Custom404Page.objects.first()
    return custom_error_view(request, exception, error_code=404, page = custom_404_page)


def custom_500_view(request, exception=None):
    """
    Returns a different 500 view depending on the site.
    """
    custom_500_page = Custom500Page.objects.first()
    return custom_error_view(request, exception, error_code=500, page = custom_500_page)
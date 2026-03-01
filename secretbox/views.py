from django.shortcuts import render
from datetime import datetime

def home(request):
    return render(request, 'secretbox/secretbox_page.html', {'current_year': datetime.now().year})

def custom_error_view(request, exception, error_code=404):
    """
    Returns a different error view depending on the site.
    """
    # portfolio_site = Site.objects.filter(site_name="Portfolio pro").first()

    # if portfolio_site:
    #     portfolio_hostname = portfolio_site.hostname
    #     # We can't use request.site, which is not served on an error view.
    #     if portfolio_hostname in request.environ.get("HTTP_HOST", ""):
    #         return render(
    #             request,
    #             f"portfolio/{error_code}.html",
    #             context={"exception": exception},
    #             status=error_code,
    #         )

    # Render the standard error page by default
    return render(
        request,
        f"{error_code}.html",
        context={"exception": exception},
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
    return custom_error_view(request, exception, error_code=404)


def custom_500_view(request, exception=None):
    """
    Returns a different 500 view depending on the site.
    """
    return custom_error_view(request, exception, error_code=500)
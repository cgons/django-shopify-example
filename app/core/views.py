from django.shortcuts import render


def index(request):
    return render(request, 'core/esdk_home.jinja2')

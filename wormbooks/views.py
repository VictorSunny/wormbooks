from django.shortcuts import render


def handler404(request, exception):
    return render(request, "error_404.html")

def handler500(request):
    return render(request, "error_500.html")
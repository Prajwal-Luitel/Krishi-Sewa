from django.shortcuts import render

def detect(request):
    return render(request, "detect.html")
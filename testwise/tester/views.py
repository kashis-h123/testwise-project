from django.shortcuts import render, redirect
from .website_tester import test_website

def home(request):

    if request.method == "POST":
        url = request.POST.get("url")

        result = test_website(url)

        request.session["result"] = result

        return redirect("home")

    result = request.session.pop("result", None)

    return render(request, "home.html", {"result": result})


def index(request):
    return render(request, "index.html")
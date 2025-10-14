from django.shortcuts import render, redirect
from . forms import RegistroForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def index(request):
    return render(request, 'index.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)  # inicia sesión
            return redirect("home")  # redirige a la página principal
        else:
            messages.error(request, "Usuario o contraseña incorrectos")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("home")

def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")  # redirige al login tras registrarse
    else:
        form = RegistroForm()
    return render(request, "registro.html", {"form": form})

def productos(request):
    return render(request, 'productos.html')

def verproducto(request):
    return render(request, 'verproducto.html')

def carrito(request):
    return render(request, 'carrito.html')

def gestionproducto(request):
    return render(request, 'gestionproducto.html')

def miperfil(request):
    return render(request, 'miperfil.html')

def recuperacion(request):
    return render(request, 'recuperacion.html')

def suscripcion(request):
    return render(request, 'suscripcion.html')

def error_404(request, exception=None):
    return render(request, '404.html', status=404)

from django.urls import path
from . import views

urlpatterns = [
    # Página principal
    path('', views.index, name='home'),
    

    # Autenticación
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro, name='registro'),
    path('recuperacion/', views.recuperacion, name='recuperacion'),
    path("logout/", views.logout_view, name="logout"),


    # Perfil y suscripción
    path('miperfil/', views.miperfil, name='miperfil'),
    path('suscripcion/', views.suscripcion, name='suscripcion'),

    # Productos
    path('productos/', views.productos, name='productos'),
    path('verproducto/', views.verproducto, name='verproducto'),
    path('carrito/', views.carrito, name='carrito'),
    path('gestionproducto/', views.gestionproducto, name='gestionproducto'),
]

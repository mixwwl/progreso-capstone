from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

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

    # Productos (Público)
    path('productos/', views.productos, name='productos'),
    path('producto/<int:producto_id>/', views.verproducto, name='verproducto'),  
    path('carrito/', views.carrito, name='carrito'),

    # 🔧 MANTENEDOR - CRUD 
    path('mantenedor/', views.mantenedor_lista_productos, name='mantenedor_lista_productos'),
    path('mantenedor/agregar/', views.mantenedor_agregar_producto, name='mantenedor_agregar_producto'),
    path('mantenedor/editar/<int:producto_id>/', views.mantenedor_editar_producto, name='mantenedor_editar_producto'),
    path('mantenedor/eliminar/<int:producto_id>/', views.mantenedor_eliminar_producto, name='mantenedor_eliminar_producto'),

    # 🔄 proveedor
    path('gestionproducto/', views.gestionproducto, name='gestionproducto'),
    
    # 🔥 SOLO ESTA URL NUEVA PARA LA REDIRECCIÓN
    path('lista-productos/', views.lista_productos, name='lista_productos'),
    
    # 🔥 AGREGAR ESTAS URLs PARA LOS ERRORES
    path('agregar-producto/', views.mantenedor_agregar_producto, name='agregar_producto'),
    path('editar-producto/<int:producto_id>/', views.mantenedor_editar_producto, name='editar_producto'),
    path('detalle-producto/<int:producto_id>/', views.verproducto, name='detalle_producto'),
    path('eliminar-producto/<int:producto_id>/', views.mantenedor_eliminar_producto, name='eliminar_producto'),
]

# 🔥 CORRECCIÓN: Agregar archivos media SOLO en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
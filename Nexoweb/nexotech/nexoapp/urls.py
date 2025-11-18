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
    path('mantenedor/productos/', views.productos, name='productos'),
    path('productos-cliente/', views.productos_cliente, name='productos_cliente'),  # Para clientes (productoC.html)
    path('lista-productos/', views.lista_productos, name='lista_productos'),
    path('producto/<int:producto_id>/', views.verproductoC, name='ver_producto_cliente'),
    
    
    # Carrito URLs
    path('carrito/', views.carrito, name='carrito'),
    path('agregar-carrito/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('eliminar-carrito/<int:item_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('actualizar-cantidad/<int:item_id>/', views.actualizar_cantidad_carrito, name='actualizar_cantidad_carrito'),
    path('vaciar-carrito/', views.vaciar_carrito, name='vaciar_carrito'),


    # 🔧 MANTENEDOR - CRUD 
    path('mantenedor/', views.indexM, name='indexM'),
    path('mantenedor/producto/<int:producto_id>/', views.verproducto, name='ver_producto'), #detalle producto
    path('mantenedor/listar', views.mantenedor_lista_productos, name='mantenedor_lista_productos'),
    path('mantenedor/agregar/', views.mantenedor_agregar_producto, name='mantenedor_agregar_producto'),
    path('mantenedor/editar/<int:producto_id>/', views.mantenedor_editar_producto, name='mantenedor_editar_producto'),
    path('mantenedor/eliminar/<int:producto_id>/', views.mantenedor_eliminar_producto, name='mantenedor_eliminar_producto'),

    # 🔄 proveedor
    path('gestionproducto/', views.gestionproducto, name='gestionproducto'),

    
]

# archivos media SOLO en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
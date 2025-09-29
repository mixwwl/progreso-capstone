from django.contrib import admin
from .models import Perfil, Empresa, Suscripcion, Proveedor, Cliente, Producto, Carrito, ProductoCarrito, Venta, LogVenta

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("user", "rol", "direccion", "telefono")
    list_filter = ("rol",)
    search_fields = ("user__username", "user__email")

# Registra los demás
admin.site.register([Empresa, Suscripcion, Proveedor, Cliente, Producto, Carrito, ProductoCarrito, Venta, LogVenta])

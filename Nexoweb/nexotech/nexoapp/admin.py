from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Perfil, Empresa, Suscripcion, Proveedor, Cliente, Categoria, Producto, Carrito, ProductoCarrito, Venta, ItemVenta, CompraSuscripcion

class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Perfil del Usuario'
    fields = ['rol', 'direccion', 'telefono']

class UserAdminCustom(UserAdmin):
    inlines = (PerfilInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_rol_display', 'is_staff', 'date_joined')
    list_filter = ('perfil__rol', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    def get_rol_display(self, obj):
        return obj.perfil.get_rol_display() if hasattr(obj, 'perfil') and obj.perfil.rol else 'Sin rol'
    get_rol_display.short_description = 'Rol'

admin.site.unregister(User)
admin.site.register(User, UserAdminCustom)

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol_id', 'rol_nombre', 'telefono', 'direccion', 'fecha_creacion')
    list_filter = ('rol', 'fecha_creacion')
    search_fields = ('user__username', 'user__email', 'telefono', 'direccion')
    list_select_related = ('user',)
    readonly_fields = ('fecha_creacion',)
    
    def rol_id(self, obj):
        return obj.rol
    rol_id.short_description = 'ID Rol'
    
    def rol_nombre(self, obj):
        return obj.get_rol_display()
    rol_nombre.short_description = 'Tipo de Cuenta'

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cantidad_proveedores', 'fecha_creacion')
    list_filter = ('fecha_creacion',)
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('fecha_creacion',)
    
    def cantidad_proveedores(self, obj):
        return obj.proveedor_set.count()
    cantidad_proveedores.short_description = 'N Proveedores'

@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'precio', 'duracion_dias', 'fecha_creacion')
    list_filter = ('tipo', 'fecha_creacion')
    search_fields = ('nombre', 'tipo', 'descripcion')
    list_editable = ('precio', 'duracion_dias')
    readonly_fields = ('fecha_creacion',)

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'empresa', 'total_productos', 'tiene_suscripcion_activa', 'fecha_registro')  # AÑADIDO: 'id'
    list_filter = ('empresa', 'fecha_registro')
    search_fields = ('user__username', 'user__email', 'empresa__nombre')
    list_select_related = ('user', 'empresa')
    readonly_fields = ('fecha_registro', 'id')  # AÑADIDO: 'id' en readonly_fields
    
    def total_productos(self, obj):
        return obj.total_productos
    total_productos.short_description = 'Total Productos'
    
    def tiene_suscripcion_activa(self, obj):
        return "✅ Sí" if obj.tiene_suscripcion_activa else "❌ No"
    tiene_suscripcion_activa.short_description = 'Suscripción Activa'

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_usuario', 'fecha_registro')
    list_filter = ('fecha_registro',)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    list_select_related = ('user',)
    readonly_fields = ('fecha_registro',)
    
    def email_usuario(self, obj):
        return obj.user.email
    email_usuario.short_description = 'Email'

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'total_productos', 'fecha_creacion')
    list_filter = ('fecha_creacion',)
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('fecha_creacion',)
    
    def total_productos(self, obj):
        return obj.total_productos
    total_productos.short_description = 'Total Productos'

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_producto', 'categoria', 'proveedor', 'precio', 'cantidad', 'tiene_stock', 'fecha_creacion')
    list_filter = ('categoria', 'proveedor', 'fecha_creacion')
    search_fields = ('nombre', 'codigo_producto', 'descripcion')
    list_select_related = ('categoria', 'proveedor')
    list_editable = ('precio', 'cantidad')
    readonly_fields = ('fecha_creacion',)
    
    def tiene_stock(self, obj):
        return obj.tiene_stock
    tiene_stock.short_description = 'Stock'
    tiene_stock.boolean = True

@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'total_items', 'subtotal', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('usuario__username',)
    readonly_fields = ('fecha_creacion',)
    
    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = 'Total Items'
    
    def subtotal(self, obj):
        return f"${obj.subtotal}"
    subtotal.short_description = 'Subtotal'

@admin.register(ProductoCarrito)
class ProductoCarritoAdmin(admin.ModelAdmin):
    list_display = ('carrito', 'producto', 'cantidad', 'subtotal', 'fecha_agregado')
    list_filter = ('fecha_agregado', 'carrito__usuario')
    search_fields = ('producto__nombre', 'carrito__usuario__username')
    
    def subtotal(self, obj):
        return f"${obj.subtotal}"
    subtotal.short_description = 'Subtotal'

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'proveedor', 'estado', 'total', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion', 'proveedor')
    search_fields = ('cliente__user__username', 'proveedor__user__username')
    readonly_fields = ('fecha_creacion',)
    list_editable = ('estado',)
    
    def total(self, obj):
        return f"${obj.total}"
    total.short_description = 'Total'

@admin.register(ItemVenta)
class ItemVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'producto', 'cantidad', 'precio_unitario', 'subtotal')
    list_filter = ('venta__fecha_creacion',)
    search_fields = ('producto__nombre', 'venta__id')
    
    def subtotal(self, obj):
        return f"${obj.subtotal}"
    subtotal.short_description = 'Subtotal'

@admin.register(CompraSuscripcion)
class CompraSuscripcionAdmin(admin.ModelAdmin):
    list_display = ('id', 'proveedor', 'suscripcion', 'estado', 'fecha_compra', 'fecha_expiracion', 'monto_pagado', 'dias_restantes', 'metodo_pago')
    list_filter = ('estado', 'suscripcion', 'fecha_compra', 'metodo_pago')
    search_fields = ('proveedor__user__username', 'proveedor__user__first_name', 'proveedor__user__last_name', 'id_transaccion')
    readonly_fields = ('fecha_compra', 'id_transaccion', 'dias_restantes')
    list_editable = ('estado',)
    
    def dias_restantes(self, obj):
        return obj.dias_restantes
    dias_restantes.short_description = 'Días Restantes'
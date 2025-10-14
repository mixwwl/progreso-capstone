from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Perfil, Empresa, Suscripcion, Proveedor, Cliente, Categoria, Producto, Carrito, ProductoCarrito, Venta, ItemVenta, LogVenta

# ==================================================
# CONFIGURACIÓN MEJORADA PARA USER ADMIN
# ==================================================
class PerfilInline(admin.StackedInline):
    """
    Inline para mostrar el Perfil dentro del User en el Admin.
    """
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Perfil del Usuario'
    fields = ['rol', 'direccion', 'telefono']

class UserAdminCustom(UserAdmin):
    """
    Admin personalizado para User que incluye el Perfil en línea.
    """
    inlines = (PerfilInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_rol_display', 'is_staff', 'date_joined')
    list_filter = ('perfil__rol', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    def get_rol_display(self, obj):
        """
        Muestra el nombre del rol en lugar del ID numérico.
        """
        return obj.perfil.get_rol_display() if hasattr(obj, 'perfil') and obj.perfil.rol else 'Sin rol'
    get_rol_display.short_description = 'Rol'

# Re-registrar User admin con la configuración personalizada
admin.site.unregister(User)
admin.site.register(User, UserAdminCustom)

# ==================================================
# ADMIN MEJORADO PARA PERFIL
# ==================================================
@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    """
    Admin mejorado para Perfil con IDs numéricos y display amigable.
    """
    list_display = ('user', 'rol_id', 'rol_nombre', 'telefono', 'direccion', 'fecha_creacion')
    list_filter = ('rol', 'fecha_creacion')
    search_fields = ('user__username', 'user__email', 'telefono', 'direccion')
    list_select_related = ('user',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    def rol_id(self, obj):
        return obj.rol
    rol_id.short_description = 'ID Rol'
    
    def rol_nombre(self, obj):
        return obj.get_rol_display()
    rol_nombre.short_description = 'Tipo de Cuenta'

# ==================================================
# ADMIN PARA EMPRESA
# ==================================================
@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    """
    Admin para Empresa con contador de proveedores.
    """
    list_display = ('nombre', 'cantidad_proveedores', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    list_editable = ('estado',)
    readonly_fields = ('fecha_creacion',)
    
    def cantidad_proveedores(self, obj):
        return obj.proveedores_activos.count()
    cantidad_proveedores.short_description = 'N° Proveedores Activos'

# ==================================================
# ADMIN PARA SUSCRIPCIÓN
# ==================================================
@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    """
    Admin para Suscripción con información relevante.
    """
    list_display = ('nombre', 'tipo', 'precio', 'duracion_dias', 'estado', 'fecha_creacion')
    list_filter = ('tipo', 'estado', 'fecha_creacion')
    search_fields = ('nombre', 'tipo', 'descripcion')
    list_editable = ('precio', 'duracion_dias', 'estado')
    readonly_fields = ('fecha_creacion',)
    
    def precio_formateado(self, obj):
        return f"${obj.precio:,.2f}"
    precio_formateado.short_description = 'Precio Formateado'

# ==================================================
# ADMIN PARA PROVEEDOR
# ==================================================
@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    """
    Admin para Proveedor con información completa.
    """
    list_display = ('user', 'empresa', 'valoracion', 'total_productos', 'tiene_suscripcion', 'estado', 'fecha_registro')
    list_filter = ('empresa', 'estado', 'suscripcion', 'fecha_registro')
    search_fields = ('user__username', 'user__email', 'empresa__nombre')
    list_select_related = ('user', 'empresa', 'suscripcion')
    readonly_fields = ('fecha_registro', 'fecha_actualizacion')
    list_editable = ('valoracion', 'estado')
    
    def total_productos(self, obj):
        return obj.total_productos
    total_productos.short_description = 'Total Productos'
    
    def tiene_suscripcion(self, obj):
        return "✅" if obj.suscripcion else "❌"
    tiene_suscripcion.short_description = 'Suscripción Activa'

# ==================================================
# ADMIN PARA CLIENTE - CORREGIDO
# ==================================================
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    """
    Admin para Cliente con información del usuario y perfil.
    """
    list_display = ('user', 'email_usuario', 'estado', 'fecha_registro')
    list_filter = ('estado', 'fecha_registro')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    list_select_related = ('user',)
    readonly_fields = ('fecha_registro', 'fecha_actualizacion')
    list_editable = ('estado',)
    
    def email_usuario(self, obj):
        return obj.user.email
    email_usuario.short_description = 'Email'

# ==================================================
# ADMIN PARA CATEGORÍA
# ==================================================
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """
    Admin para Categoría con contador de productos.
    """
    list_display = ('nombre', 'total_productos', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    list_editable = ('estado',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    def total_productos(self, obj):
        return obj.total_productos
    total_productos.short_description = 'Total Productos'

# ==================================================
# ADMIN PARA PRODUCTO
# ==================================================
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """
    Admin para Producto con información del proveedor.
    """
    list_display = ('nombre', 'codigo_producto', 'categoria', 'proveedor', 'precio', 'cantidad', 'tiene_stock', 'estado', 'fecha_creacion')
    list_filter = ('categoria', 'proveedor', 'estado', 'fecha_creacion')
    search_fields = ('nombre', 'codigo_producto', 'descripcion')
    list_select_related = ('categoria', 'proveedor')
    list_editable = ('precio', 'cantidad', 'estado')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    def tiene_stock(self, obj):
        return obj.tiene_stock
    tiene_stock.short_description = 'Stock'
    tiene_stock.boolean = True

# ==================================================
# ADMIN PARA CARRITO
# ==================================================
@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'total_items', 'subtotal_formateado', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('usuario__username',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = 'Total Items'
    
    def subtotal_formateado(self, obj):
        return obj.subtotal_formateado
    subtotal_formateado.short_description = 'Subtotal'

# ==================================================
# ADMIN PARA PRODUCTO CARRITO
# ==================================================
@admin.register(ProductoCarrito)
class ProductoCarritoAdmin(admin.ModelAdmin):
    list_display = ('carrito', 'producto', 'cantidad', 'subtotal_formateado', 'fecha_agregado')
    list_filter = ('fecha_agregado', 'carrito__usuario')
    search_fields = ('producto__nombre', 'carrito__usuario__username')
    
    def subtotal_formateado(self, obj):
        return obj.subtotal_formateado
    subtotal_formateado.short_description = 'Subtotal'

# ==================================================
# ADMIN PARA VENTA
# ==================================================
@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'proveedor', 'estado', 'total_formateado', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion', 'proveedor')
    search_fields = ('cliente__user__username', 'proveedor__user__username')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    list_editable = ('estado',)
    
    def total_formateado(self, obj):
        return obj.total_formateado
    total_formateado.short_description = 'Total'

# ==================================================
# ADMIN PARA ITEM VENTA
# ==================================================
@admin.register(ItemVenta)
class ItemVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'producto', 'cantidad', 'precio_unitario', 'subtotal')
    list_filter = ('venta__fecha_creacion',)
    search_fields = ('producto__nombre', 'venta__id')
    
    def subtotal(self, obj):
        return f"${obj.subtotal:,.2f}"
    subtotal.short_description = 'Subtotal'

# ==================================================
# ADMIN PARA LOG VENTA
# ==================================================
@admin.register(LogVenta)
class LogVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'accion', 'usuario', 'fecha')
    list_filter = ('accion', 'fecha', 'usuario')
    search_fields = ('venta__id', 'descripcion', 'usuario__username')
    readonly_fields = ('fecha',)
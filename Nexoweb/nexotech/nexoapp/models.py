from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# --------- PERFIL / ROLES ----------
class Perfil(models.Model):
    ROLES = [
        (1, 'Cliente'),
        (2, 'Proveedor'), 
        (3, 'Administrador'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    rol = models.IntegerField(choices=ROLES, default=1)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.user.username} ({self.get_rol_display()})"

    def clean(self):
        """Validación personalizada para el perfil"""
        if self.telefono and not self.telefono.isdigit():
            raise ValidationError({'telefono': 'El teléfono debe contener solo números.'})

    @property
    def es_proveedor(self):
        return self.rol == 2

    @property
    def es_cliente(self):
        return self.rol == 1

    @property
    def es_administrador(self):
        return self.rol == 3


# --------- ENTIDADES DE NEGOCIO ----------
class Empresa(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @property
    def proveedores_activos(self):
        return self.proveedor_set.filter(user__is_active=True)


class Suscripcion(models.Model):
    TIPOS_SUSCRIPCION = [
        ('basica', 'Básica'),
        ('premium', 'Premium'),
        ('empresa', 'Empresa'),
    ]
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=50, choices=TIPOS_SUSCRIPCION)
    duracion_dias = models.IntegerField(default=30)
    caracteristicas = models.TextField(blank=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'
        ordering = ['precio']

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"

    @property
    def precio_formateado(self):
        return f"${self.precio:,.2f}"


class Proveedor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="proveedor")
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.SET_NULL, null=True, blank=True)
    valoracion = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    descripcion = models.TextField(blank=True)
    sitio_web = models.URLField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

    @property
    def productos_activos(self):
        return self.producto_set.filter(estado=True)

    @property
    def total_productos(self):
        return self.producto_set.count()

    @property
    def valoracion_promedio(self):
        return f"{self.valoracion:.1f}"

    def clean(self):
        if self.valoracion < 0 or self.valoracion > 5:
            raise ValidationError({'valoracion': 'La valoración debe estar entre 0 y 5.'})


class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cliente")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

    @property
    def compras_realizadas(self):
        return self.venta_set.count()

    @property
    def total_gastado(self):
        from django.db.models import Sum
        total = self.venta_set.aggregate(Sum('total'))['total__sum']
        return total or 0


# --------- CATEGORÍAS ----------
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='categorias/', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @classmethod
    def get_default_categoria(cls):
        """Método para obtener la categoría por defecto"""
        categoria, created = cls.objects.get_or_create(
            nombre="General",
            defaults={'descripcion': 'Categoría general por defecto'}
        )
        return categoria

    @property
    def productos_activos(self):
        return self.producto_set.filter(estado=True)

    @property
    def total_productos(self):
        return self.producto_set.count()


# --------- PRODUCTOS ----------
class Producto(models.Model):
    codigo_producto = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    cantidad = models.IntegerField(default=0)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.PROTECT,
        default=Categoria.get_default_categoria
    )
    
    # CAMBIO: Proveedor opcional
    proveedor = models.ForeignKey(
        Proveedor, 
        on_delete=models.CASCADE,
        null=True,        # ← Permite NULL en BD
        blank=True,       # ← Permite campo vacío en formularios
        verbose_name="Proveedor"
    )
    
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['categoria']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.codigo_producto})"

    def clean(self):
        """Validaciones personalizadas"""
        if self.cantidad < 0:
            raise ValidationError({'cantidad': 'La cantidad no puede ser negativa.'})
        
        if self.precio <= 0:
            raise ValidationError({'precio': 'El precio debe ser mayor a 0.'})

    @property
    def tiene_stock(self):
        return self.cantidad > 0

    @property
    def stock_bajo(self):
        return self.cantidad <= 10

    @property
    def precio_formateado(self):
        return f"${self.precio:,.2f}"

    @property
    def imagen_url(self):
        if self.imagen and hasattr(self.imagen, 'url'):
            return self.imagen.url
        return '/static/img/producto-default.png'


# --------- CARRITO DE COMPRAS ----------
class Carrito(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Carrito'
        verbose_name_plural = 'Carritos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Carrito de {self.usuario.username}"

    @property
    def total_items(self):
        return self.items.aggregate(total=models.Sum('cantidad'))['total'] or 0

    @property
    def subtotal(self):
        from django.db.models import Sum, F
        subtotal = self.items.aggregate(
            total=Sum(F('cantidad') * F('producto__precio'))
        )['total'] or 0
        return subtotal

    @property
    def subtotal_formateado(self):
        return f"${self.subtotal:,.2f}"

    def limpiar_carrito(self):
        """Vacía el carrito"""
        self.items.all().delete()


class ProductoCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Producto en Carrito'
        verbose_name_plural = 'Productos en Carrito'
        unique_together = ['carrito', 'producto']

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"

    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a 0.'})
        
        if self.cantidad > self.producto.cantidad:
            raise ValidationError({
                'cantidad': f'Solo hay {self.producto.cantidad} unidades disponibles.'
            })

    @property
    def subtotal(self):
        return self.cantidad * self.producto.precio

    @property
    def subtotal_formateado(self):
        return f"${self.subtotal:,.2f}"


# --------- VENTAS ----------
class Venta(models.Model):
    ESTADOS_VENTA = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('enviada', 'Enviada'),
        ('entregada', 'Entregada'),
        ('cancelada', 'Cancelada'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    estado = models.CharField(max_length=20, choices=ESTADOS_VENTA, default='pendiente')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    comision = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    impuestos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_creacion']),
        ]

    def __str__(self):
        return f"Venta #{self.id} - {self.cliente}"

    def clean(self):
        if self.subtotal < 0:
            raise ValidationError({'subtotal': 'El subtotal no puede ser negativo.'})
        
        if self.comision < 0:
            raise ValidationError({'comision': 'La comisión no puede ser negativa.'})

    @property
    def total(self):
        return self.subtotal + self.comision + self.impuestos

    @property
    def total_formateado(self):
        return f"${self.total:,.2f}"

    @property
    def puede_cancelar(self):
        return self.estado in ['pendiente', 'confirmada']

    @property
    def items_count(self):
        return self.items.count()


class ItemVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Item de Venta'
        verbose_name_plural = 'Items de Venta'

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"

    def save(self, *args, **kwargs):
        # Calcular subtotal automáticamente
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a 0.'})
        
        if self.precio_unitario <= 0:
            raise ValidationError({'precio_unitario': 'El precio debe ser mayor a 0.'})


# --------- LOGS DE AUDITORÍA (OPCIONAL) ----------
class LogVenta(models.Model):
    TIPOS_ACCION = [
        ('creacion', 'Creación'),
        ('actualizacion', 'Actualización'),
        ('cancelacion', 'Cancelación'),
        ('estado', 'Cambio de Estado'),
    ]
    
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    accion = models.CharField(max_length=20, choices=TIPOS_ACCION)
    descripcion = models.TextField()
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    datos_anteriores = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = 'Log de Venta'
        verbose_name_plural = 'Logs de Ventas'
        ordering = ['-fecha']

    def __str__(self):
        return f"Log #{self.id} - {self.venta} - {self.accion}"


# --------- SEÑALES (SIGNALS) ----------
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crear perfil automáticamente cuando se crea un usuario"""
    if created:
        Perfil.objects.create(user=instance)

@receiver(pre_save, sender=Producto)
def generar_codigo_producto(sender, instance, **kwargs):
    """Generar código automático si no se proporciona"""
    if not instance.codigo_producto:
        from django.utils.text import slugify
        from datetime import datetime
        base_codigo = slugify(instance.nombre)[:50].upper()
        timestamp = datetime.now().strftime('%Y%m%d%H%M')
        instance.codigo_producto = f"{base_codigo}-{timestamp}"

@receiver(pre_save, sender=Venta)
def actualizar_stock_venta(sender, instance, **kwargs):
    """Actualizar stock cuando se confirma una venta"""
    if instance.estado == 'confirmada':
        for item in instance.items.all():
            producto = item.producto
            producto.cantidad -= item.cantidad
            producto.save()
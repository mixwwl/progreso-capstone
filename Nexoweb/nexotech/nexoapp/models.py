from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from datetime import timedelta

# =============================================================================
# MODELOS DE USUARIOS Y PERFILES
# =============================================================================

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

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'

    def __str__(self):
        return f"{self.user.username} ({self.get_rol_display()})"

    def clean(self):
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


# =============================================================================
# MODELOS DE NEGOCIO Y EMPRESAS
# =============================================================================

class Empresa(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'

    def __str__(self):
        return self.nombre


class Suscripcion(models.Model):
    TIPOS_SUSCRIPCION = [
        ('basica', 'Básica'),
        ('premium', 'Premium'),
        ('empresa', 'Empresa'),
    ]
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.IntegerField()
    tipo = models.CharField(max_length=50, choices=TIPOS_SUSCRIPCION)
    duracion_dias = models.IntegerField(default=30)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"


# =============================================================================
# NUEVO MODELO: COMPRA SUSCRIPCIÓN (TRACKING COMPLETO)
# =============================================================================

class CompraSuscripcion(models.Model):
    ESTADOS_SUSCRIPCION = [
        ('activa', 'Activa'),
        ('expirada', 'Expirada'), 
        ('cancelada', 'Cancelada'),
        ('pendiente_pago', 'Pendiente de Pago'),
        ('renovada', 'Renovada'),
    ]
    
    proveedor = models.ForeignKey('Proveedor', on_delete=models.CASCADE, related_name='compras_suscripcion')
    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.PROTECT)
    fecha_compra = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS_SUSCRIPCION, default='activa')
    monto_pagado = models.IntegerField()
    metodo_pago = models.CharField(max_length=50, blank=True, help_text="Método de pago utilizado")
    id_transaccion = models.CharField(max_length=100, blank=True, unique=True)
    notas = models.TextField(blank=True)
    
    # Campos para renovaciones
    compra_original = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                       related_name='renovaciones')
    es_renovacion = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Compra de Suscripción'
        verbose_name_plural = 'Compras de Suscripciones'
        ordering = ['-fecha_compra']

    def __str__(self):
        return f"Suscripción {self.suscripcion.nombre} - {self.proveedor} - {self.estado}"

    def clean(self):
        if self.monto_pagado <= 0:
            raise ValidationError({'monto_pagado': 'El monto debe ser mayor a 0.'})
        
        if self.fecha_expiracion <= self.fecha_compra:
            raise ValidationError({'fecha_expiracion': 'La fecha de expiración debe ser posterior a la compra.'})

    def save(self, *args, **kwargs):
        # Generar ID de transacción si no existe
        if not self.id_transaccion:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.id_transaccion = f"SUB_{self.proveedor.id}_{timestamp}"
        
        # Si es nueva compra (no renovación), calcular fecha de expiración
        if not self.pk and not self.fecha_expiracion:
            from django.utils import timezone
            duracion = timedelta(days=self.suscripcion.duracion_dias)
            self.fecha_expiracion = timezone.now() + duracion
        
        super().save(*args, **kwargs)

    @property
    def dias_restantes(self):
        """Calcula los días restantes de la suscripción"""
        from django.utils import timezone
        if self.estado != 'activa':
            return 0
        hoy = timezone.now()
        if hoy > self.fecha_expiracion:
            return 0
        return (self.fecha_expiracion - hoy).days

    @property
    def esta_activa(self):
        """Verifica si la suscripción está activa y no expirada"""
        from django.utils import timezone
        return self.estado == 'activa' and timezone.now() <= self.fecha_expiracion


class Proveedor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="proveedor")
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.TextField(blank=True)
    sitio_web = models.URLField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

    @property
    def total_productos(self):
        return self.producto_set.count()

    @property
    def suscripcion_activa(self):
        """Retorna la suscripción activa actual del proveedor"""
        compra_activa = self.compras_suscripcion.filter(estado='activa').first()
        return compra_activa.suscripcion if compra_activa else None

    @property
    def compra_suscripcion_activa(self):
        """Retorna la compra de suscripción activa actual"""
        return self.compras_suscripcion.filter(estado='activa').first()

    @property
    def tiene_suscripcion_activa(self):
        """Verifica si el proveedor tiene una suscripción activa"""
        compra_activa = self.compra_suscripcion_activa
        return compra_activa and compra_activa.esta_activa if compra_activa else False

    @property
    def historial_suscripciones(self):
        """Retorna el historial completo de suscripciones ordenado por fecha"""
        return self.compras_suscripcion.all().order_by('-fecha_compra')

    @property
    def total_gastado_suscripciones(self):
        """Calcula el total gastado en suscripciones"""
        return self.compras_suscripcion.aggregate(
            total=models.Sum('monto_pagado')
        )['total'] or 0


class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cliente")
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"


# =============================================================================
# MODELOS DE CATALOGO Y PRODUCTOS
# =============================================================================

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='categorias/', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre

    @property
    def total_productos(self):
        return self.producto_set.count()

    @classmethod
    def get_default_categoria(cls):
        categoria, created = cls.objects.get_or_create(
            nombre="General",
            defaults={'descripcion': 'Categoría general por defecto'}
        )
        return categoria


class Producto(models.Model):
    codigo_producto = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    cantidad = models.IntegerField(default=0)
    precio = models.IntegerField()
    
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.PROTECT,
        default=Categoria.get_default_categoria
    )
    
    proveedor = models.ForeignKey(
        Proveedor, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Proveedor"
    )
    
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return f"{self.nombre} ({self.codigo_producto})"

    def clean(self):
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


# =============================================================================
# MODELOS DE VENTAS Y CARRITO
# =============================================================================

class Carrito(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Carrito'
        verbose_name_plural = 'Carritos'

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
    subtotal = models.IntegerField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'

    def __str__(self):
        return f"Venta #{self.id} - {self.cliente}"

    @property
    def total(self):
        return self.subtotal

    @property
    def items_count(self):
        return self.items.count()


class ItemVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.IntegerField()
    subtotal = models.IntegerField()

    class Meta:
        verbose_name = 'Item de Venta'
        verbose_name_plural = 'Items de Venta'

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a 0.'})
        
        if self.precio_unitario <= 0:
            raise ValidationError({'precio_unitario': 'El precio debe ser mayor a 0.'})


# =============================================================================
# SEÑALES (SIGNALS)
# =============================================================================

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)

@receiver(pre_save, sender=Producto)
def generar_codigo_producto(sender, instance, **kwargs):
    if not instance.codigo_producto:
        from django.utils.text import slugify
        from datetime import datetime
        base_codigo = slugify(instance.nombre)[:50].upper()
        timestamp = datetime.now().strftime('%Y%m%d%H%M')
        instance.codigo_producto = f"{base_codigo}-{timestamp}"

@receiver(pre_save, sender=Venta)
def actualizar_stock_venta(sender, instance, **kwargs):
    if instance.estado == 'confirmada':
        for item in instance.items.all():
            producto = item.producto
            producto.cantidad -= item.cantidad
            producto.save()

# Nueva señal para manejar suscripciones
@receiver(post_save, sender=CompraSuscripcion)
def actualizar_suscripcion_proveedor(sender, instance, created, **kwargs):
    """
    Cuando se crea una nueva compra de suscripción activa,
    se marca como expirada la suscripción anterior del proveedor
    """
    if created and instance.estado == 'activa':
        # Marcar otras suscripciones activas del mismo proveedor como expiradas
        CompraSuscripcion.objects.filter(
            proveedor=instance.proveedor,
            estado='activa'
        ).exclude(id=instance.id).update(estado='expirada')
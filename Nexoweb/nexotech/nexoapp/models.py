from django.db import models
from django.contrib.auth.models import User  # usamos el usuario por defecto

# --------- PERFIL / ROLES ----------
class Perfil(models.Model):
    ROL_CHOICES = [
        ("cliente", "Cliente"),
        ("proveedor", "Proveedor"),
        ("admin", "Administrador"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default="cliente")
    direccion = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.rol})"


# --------- ENTIDADES DE NEGOCIO ----------
class Empresa(models.Model):
    nombre = models.CharField(max_length=200)

    def __str__(self):
        return self.nombre


class Suscripcion(models.Model):
    descripcion = models.CharField(max_length=150)
    precio = models.IntegerField()
    tipo = models.CharField(max_length=50)
    fecha_suscripcion = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField()

    def __str__(self):
        return f"{self.tipo} - {self.precio}"


class Proveedor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="proveedor")
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.SET_NULL, null=True, blank=True)
    valoracion = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username


class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cliente")

    def __str__(self):
        return self.user.username


# --------- PRODUCTOS Y CARRITO ----------
class Producto(models.Model):
    codigo_producto = models.CharField(max_length=100)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    cantidad = models.IntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    fecha_creacion = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class Carrito(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"


class ProductoCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"


# --------- VENTAS ----------
class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    comision = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def total(self):
        return self.subtotal + self.comision

    def __str__(self):
        return f"Venta #{self.id} - {self.fecha}"


class LogVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)

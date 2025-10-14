from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from .forms import RegistroForm, EmailAuthenticationForm, ProductoForm
from .models import Producto, Proveedor, Categoria

# ==================================================
# VISTAS PÚBLICAS (SIN LOGIN REQUERIDO)
# ==================================================

def index(request):
    """Página principal de NexoTech"""
    return render(request, 'index.html')

def productos(request):
    """Catálogo público de productos para clientes"""
    # Obtener productos con stock y activos
    productos = Producto.objects.filter(
        cantidad__gt=0, 
        estado=True
    ).select_related('categoria').order_by('-fecha_creacion')
    
    # Obtener categorías con conteo de productos activos
    categorias = Categoria.objects.filter(estado=True).annotate(
        productos_count=Count('producto', filter=Q(producto__estado=True, producto__cantidad__gt=0))
    ).order_by('nombre')
    
    # Filtrar por categoría si se especifica
    categoria_id = request.GET.get('categoria')
    categoria_actual = None
    
    if categoria_id and categoria_id != 'todos':
        productos = productos.filter(categoria_id=categoria_id)
        try:
            categoria_actual = Categoria.objects.get(id=categoria_id)
        except Categoria.DoesNotExist:
            pass
    
    context = {
        'productos': productos,
        'categorias': categorias,
        'categoria_actual': categoria_actual
    }
    return render(request, 'productos.html', context)

def verproducto(request, producto_id):
    """Detalle de producto para clientes"""
    producto = get_object_or_404(Producto, id=producto_id, estado=True)
    
    # Productos relacionados (misma categoría)
    productos_relacionados = Producto.objects.filter(
        categoria=producto.categoria,
        estado=True,
        cantidad__gt=0
    ).exclude(id=producto.id)[:4]
    
    return render(request, 'verproducto.html', {
        'producto': producto,
        'productos_relacionados': productos_relacionados
    })

def recuperacion(request):
    """Recuperación de contraseña"""
    return render(request, 'recuperacion.html')

# ==================================================
# VISTAS DE AUTENTICACIÓN
# ==================================================

def login_view(request):
    """Inicio de sesión con formulario personalizado"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == "POST":
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"¡Bienvenido {user.username}!")
            return redirect("home")
        else:
            messages.error(request, "Correo electrónico o contraseña incorrectos")
    else:
        form = EmailAuthenticationForm()
    
    return render(request, "login.html", {"form": form})

def logout_view(request):
    """Cierre de sesión"""
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect("home")

def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Registro exitoso. ¡Ahora puedes iniciar sesión!")
            return redirect("login")
        else:
            messages.error(request, "Por favor corrige los errores del formulario.")
    else:
        form = RegistroForm()

    # 🚨 Importante: pasar siempre 'request' al render
    return render(request, "registro.html", {"form": form})

# ==================================================
# VISTAS PROTEGIDAS (REQUIEREN LOGIN)
# ==================================================

@login_required
def carrito(request):
    """Carrito de compras del usuario"""
    return render(request, 'carrito.html')

@login_required
def miperfil(request):
    """Perfil del usuario"""
    return render(request, 'miperfil.html')

@login_required
def suscripcion(request):
    """Gestión de suscripciones"""
    return render(request, 'suscripcion.html')

# ==================================================
# MANTENEDOR GENERAL DE PRODUCTOS (NUEVO)
# ==================================================

@login_required
def mantenedor_lista_productos(request):
    """
    Vista para mostrar la lista de productos (productos.html)
    Esta es la vista a la que se redirige después de agregar un producto
    """
    productos = Producto.objects.all().select_related('categoria').order_by('-fecha_creacion')
    
    # Obtener categorías para el filtro
    categorias = Categoria.objects.filter(estado=True).annotate(
        productos_count=Count('producto', filter=Q(producto__estado=True))
    ).order_by('nombre')
    
    # Calcular estadísticas
    productos_activos = productos.filter(estado=True).count()
    productos_bajo_stock = productos.filter(cantidad__lt=5, cantidad__gt=0).count()
    categorias_count = Categoria.objects.count()
    
    context = {
        'productos': productos,
        'categorias': categorias,  # 🆕 AGREGAR ESTA LÍNEA
        'productos_activos': productos_activos,
        'productos_bajo_stock': productos_bajo_stock,
        'categorias_count': categorias_count,
        'titulo': 'Lista de Productos'
    }
    return render(request, 'productos.html', context)

@login_required
def mantenedor_agregar_producto(request):
    """
    Agregar nuevo producto - Mantenedor general
    """
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                producto = form.save()
                messages.success(request, f"✅ Producto '{producto.nombre}' agregado correctamente!")
                # 🔥 REDIRIGIR A LA NUEVA URL
                return redirect('lista_productos')
            except Exception as e:
                messages.error(request, f"❌ Error al guardar el producto: {str(e)}")
        else:
            messages.error(request, "❌ Por favor corrige los errores en el formulario")
    else:
        form = ProductoForm()
    
    return render(request, 'mantenedor/agregar_producto.html', {
        'form': form,
        'titulo': 'Agregar Producto'
    })

@login_required
def mantenedor_editar_producto(request, producto_id):
    """
    Editar producto existente - Mantenedor general
    """
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            # Manejar eliminación de imagen
            if 'eliminar_imagen' in request.POST:
                if producto.imagen:
                    producto.imagen.delete(save=False)
            
            producto_actualizado = form.save()
            messages.success(request, f"✅ Producto '{producto_actualizado.nombre}' actualizado correctamente!")
            return redirect('mantenedor_lista_productos')
        else:
            messages.error(request, "❌ Por favor corrige los errores en el formulario")
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'mantenedor/editar_producto.html', {
        'form': form,
        'producto': producto
    })

@login_required
def mantenedor_eliminar_producto(request, producto_id):
    """
    Eliminar producto - Mantenedor general
    """
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        nombre_producto = producto.nombre
        producto.delete()
        messages.success(request, f"✅ Producto '{nombre_producto}' eliminado correctamente!")
        return redirect('mantenedor_lista_productos')
    
    return render(request, 'mantenedor/eliminar_producto.html', {
        'producto': producto
    })

# ==================================================
# PROVEEDORES 
# ==================================================

@login_required
def proveedor_productos(request):
    """Lista de productos del proveedor logueado"""
    try:
        proveedor = request.user.proveedor
        productos = Producto.objects.filter(proveedor=proveedor).order_by('-fecha_creacion')
        return render(request, 'proveedor/productos.html', {
            'productos': productos,
            'proveedor': proveedor
        })
    except Proveedor.DoesNotExist:
        messages.error(request, "❌ Solo los proveedores pueden gestionar productos")
        return redirect('home')

@login_required
def proveedor_agregar_producto(request):
    """Agregar nuevo producto (proveedores)"""
    try:
        proveedor = request.user.proveedor
    except Proveedor.DoesNotExist:
        messages.error(request, "❌ Solo los proveedores pueden agregar productos")
        return redirect('home')
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.proveedor = proveedor
            producto.save()
            messages.success(request, f"✅ Producto '{producto.nombre}' agregado correctamente!")
            return redirect('proveedor_productos')
    else:
        form = ProductoForm()
    
    return render(request, 'proveedor/form_producto.html', {
        'form': form,
        'titulo': 'Agregar Producto'
    })

@login_required
def proveedor_editar_producto(request, producto_id):
    """Editar producto existente (proveedores)"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    try:
        if producto.proveedor != request.user.proveedor:
            messages.error(request, "❌ No tienes permisos para editar este producto")
            return redirect('proveedor_productos')
    except Proveedor.DoesNotExist:
        messages.error(request, "❌ Solo los proveedores pueden editar productos")
        return redirect('proveedor_productos')
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Producto actualizado correctamente!")
            return redirect('proveedor_productos')
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'proveedor/form_producto.html', {
        'form': form,
        'titulo': 'Editar Producto'
    })

@login_required
def proveedor_eliminar_producto(request, producto_id):
    """Eliminar producto (proveedores)"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    try:
        if producto.proveedor != request.user.proveedor:
            messages.error(request, "❌ No tienes permisos para eliminar este producto")
            return redirect('proveedor_productos')
    except Proveedor.DoesNotExist:
        messages.error(request, "❌ Solo los proveedores pueden eliminar productos")
        return redirect('proveedor_productos')
    
    if request.method == 'POST':
        nombre_producto = producto.nombre
        producto.delete()
        messages.success(request, f"✅ Producto '{nombre_producto}' eliminado correctamente!")
        return redirect('proveedor_productos')
    
    return render(request, 'proveedor/confirmar_eliminar.html', {'producto': producto})

# ==================================================
# PANEL DE ADMINISTRACIÓN (SUPERUSUARIOS)
# ==================================================

@login_required
def admin_panel_productos(request):
    """Panel de administración - TODOS los productos"""
    if not request.user.is_superuser:
        messages.error(request, "❌ No tienes permisos de administrador")
        return redirect('home')
    
    productos = Producto.objects.all().select_related('proveedor', 'categoria')
    return render(request, 'admin/panel_productos.html', {
        'productos': productos
    })

# ==================================================
# VISTA DE LISTA DE PRODUCTOS PARA REDIRECCIÓN
# ==================================================

def lista_productos(request):
    """
    Vista para mostrar la lista de productos (productos.html)
    Esta es la vista a la que se redirige después de agregar un producto
    """
    productos = Producto.objects.all().select_related('categoria').order_by('-fecha_creacion')
    
    # Calcular estadísticas
    productos_activos = productos.filter(estado=True).count()
    productos_bajo_stock = productos.filter(cantidad__lt=5, cantidad__gt=0).count()
    categorias_count = Categoria.objects.count()
    
    context = {
        'productos': productos,
        'productos_activos': productos_activos,
        'productos_bajo_stock': productos_bajo_stock,
        'categorias_count': categorias_count,
        'titulo': 'Lista de Productos'
    }
    return render(request, 'productos.html', context)

# ==================================================
# REDIRECCIONES PARA COMPATIBILIDAD (ACTUALIZADAS)
# ==================================================

def gestionproducto(request):
    """Redirección para compatibilidad - Ahora al mantenedor general"""
    return redirect('mantenedor_lista_productos')

def detalle_producto(request, producto_id):
    """Redirección para compatibilidad"""
    return redirect('verproducto', producto_id=producto_id)

def error_404(request, exception=None):
    """Página de error 404"""
    return render(request, '404.html', status=404)

# ==================================================
# VISTAS ADICIONALES PARA COMPLETAR EL SISTEMA
# ==================================================

@login_required
def editar_producto(request, producto_id):
    """
    Vista genérica para editar producto
    """
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            producto_actualizado = form.save()
            messages.success(request, f'✅ Producto "{producto_actualizado.nombre}" actualizado exitosamente!')
            return redirect('lista_productos')
    else:
        form = ProductoForm(instance=producto)
    
    context = {
        'form': form,
        'titulo': f'Editar Producto: {producto.nombre}',
        'producto': producto
    }
    return render(request, 'agregar_producto.html', context)

@login_required
def eliminar_producto(request, producto_id):
    """
    Vista genérica para eliminar producto
    """
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        nombre_producto = producto.nombre
        producto.delete()
        messages.success(request, f'✅ Producto "{nombre_producto}" eliminado exitosamente!')
        return redirect('lista_productos')
    
    # Si es GET, mostrar confirmación
    return render(request, 'confirmar_eliminar.html', {'producto': producto})

@login_required
def detalle_producto_admin(request, producto_id):
    """
    Vista de detalle de producto para administración
    """
    producto = get_object_or_404(Producto, id=producto_id)
    
    context = {
        'producto': producto,
        'titulo': f'Detalle: {producto.nombre}'
    }
    return render(request, 'detalle_producto.html', context)
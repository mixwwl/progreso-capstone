from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from .forms import RegistroForm, EmailAuthenticationForm, ProductoForm
from .models import Producto, Proveedor, Categoria,Carrito, ProductoCarrito

# ==================================================
# VISTAS PÚBLICAS (SIN LOGIN REQUERIDO)
# ==================================================

def index(request):
    """Página principal de NexoTech"""
    print("[DEBUG] EJECUTANDO: index view")
    print(f"[DEBUG] Usuario: {request.user}")
    print(f"[DEBUG] Autenticado: {request.user.is_authenticated}")
    
    if request.user.is_authenticated:
        print(f"[DEBUG] Tiene perfil: {hasattr(request.user, 'perfil')}")
        if hasattr(request.user, 'perfil'):
            print(f"[DEBUG] Rol: {request.user.perfil.rol}")
            print(f"[DEBUG] Es admin (rol 3): {request.user.perfil.rol == 3}")
            
            if request.user.perfil.rol == 3:
                print("[DEBUG] REDIRIGIENDO A INDEXM...")
                return redirect('indexM')
    
    print("[DEBUG] MOSTRANDO INDEX NORMAL")
    return render(request, 'index.html')

def productos(request):
    """Catálogo público de productos para clientes"""
    print("[DEBUG] EJECUTANDO: productos view (publico)")
    
    # SI ES ADMIN, REDIRIGIR AL MANTENEDOR
    if request.user.is_authenticated and hasattr(request.user, 'perfil'):
        if request.user.perfil.rol == 3:
            print("[DEBUG] Admin detectado, redirigiendo a mantenedor")
            return redirect('mantenedor_lista_productos')
    
    # Obtener productos con stock (sin filtro de estado)
    productos = Producto.objects.filter(
        cantidad__gt=0
    ).select_related('categoria').order_by('-fecha_creacion')
    
    # Obtener categorías con conteo de productos con stock
    categorias = Categoria.objects.all().annotate(
        productos_count=Count('producto', filter=Q(producto__cantidad__gt=0))
    ).order_by('nombre')
    
    # Filtrar por categoría si se especifica
    categoria_id = request.GET.get('categoria')
    categoria_actual = None
    
    if categoria_id and categoria_id != 'todos':
        print(f"[DEBUG] Filtrando por categoria ID: {categoria_id}")
        productos = productos.filter(categoria_id=categoria_id)
        try:
            categoria_actual = Categoria.objects.get(id=categoria_id)
        except Categoria.DoesNotExist:
            print("[DEBUG] Categoria no encontrada")
            pass
    
    print(f"[DEBUG] Productos encontrados: {productos.count()}")
    context = {
        'productos': productos,
        'categorias': categorias,
        'categoria_actual': categoria_actual
    }
    return render(request, 'mantenedor/productos.html', context)

def verproducto(request, producto_id):
    """Detalle de producto para TODOS los usuarios (incluye admins)"""
    print(f"[DEBUG] EJECUTANDO: verproducto view - ID: {producto_id}")
    
    producto = get_object_or_404(Producto, id=producto_id)
    print(f"[DEBUG] Producto encontrado: {producto.nombre}")
    
    productos_relacionados = Producto.objects.filter(
        categoria=producto.categoria
    ).exclude(id=producto.id)[:4]
    
    print(f"[DEBUG] Productos relacionados: {productos_relacionados.count()}")
    
    return render(request, 'mantenedor/verproducto.html', {
        'producto': producto,
        'productos_relacionados': productos_relacionados
    })

def recuperacion(request):
    """Recuperación de contraseña"""
    print("[DEBUG] EJECUTANDO: recuperacion view")
    return render(request, 'recuperacion.html')

# ==================================================
# VISTAS DE AUTENTICACIÓN
# ==================================================

def login_view(request):
    """Inicio de sesión con formulario personalizado"""
    print("[DEBUG] EJECUTANDO: login_view")
    
    if request.user.is_authenticated:
        print("[DEBUG] Usuario ya autenticado, redirigiendo...")
        # REDIRIGIR SEGÚN ROL SI YA ESTÁ AUTENTICADO
        if hasattr(request.user, 'perfil'):
            if request.user.perfil.rol == 3:
                return redirect('indexM')
            else:
                return redirect('productos_cliente')
        return redirect('home')
    
    if request.method == "POST":
        print("[DEBUG] Login POST request recibido")
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Bienvenido {user.username}!")
            print(f"[DEBUG] Login exitoso para: {user.username}")
            
            # REDIRIGIR SEGÚN ROL INMEDIATAMENTE DESPUÉS DEL LOGIN
            if hasattr(user, 'perfil'):
                if user.perfil.rol == 3:
                    print("[DEBUG] Redirigiendo admin a indexM")
                    return redirect('indexM')
                else:
                    print("[DEBUG] Redirigiendo usuario a productos_cliente")
                    return redirect('productos_cliente')
            
            return redirect("home")
        else:
            print("[DEBUG] Login fallido")
            messages.error(request, "Correo electronico o contrasena incorrectos")
    else:
        print("[DEBUG] Mostrando formulario de login")
        form = EmailAuthenticationForm()
    
    return render(request, "login.html", {"form": form})

def logout_view(request):
    """Cierre de sesión"""
    print("[DEBUG] EJECUTANDO: logout_view")
    print(f"[DEBUG] Cerrando sesion de: {request.user}")
    logout(request)
    messages.info(request, "Has cerrado sesion correctamente.")
    return redirect("home")

def registro(request):
    """Registro de nuevos usuarios"""
    print("[DEBUG] EJECUTANDO: registro view")
    
    if request.method == "POST":
        print("[DEBUG] Registro POST request recibido")
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            print(f"[DEBUG] Usuario registrado: {user.username}")
            messages.success(request, "Registro exitoso. Ahora puedes iniciar sesion!")
            return redirect("login")
        else:
            print("[DEBUG] Errores en formulario de registro")
            messages.error(request, "Por favor corrige los errores del formulario.")
    else:
        print("[DEBUG] Mostrando formulario de registro")
        form = RegistroForm()

    return render(request, "registro.html", {"form": form})

# ==================================================
# VISTAS PROTEGIDAS PARA CLIENTES 
# ==================================================

@login_required
def productos_cliente(request):
    """Catálogo público de productos para clientes logueados"""
    print("[DEBUG] EJECUTANDO: productos_cliente view")
    print(f"[DEBUG] Usuario autenticado: {request.user}")
    
    # Obtener productos con stock (sin filtro de estado)
    productos = Producto.objects.filter(
        cantidad__gt=0
    ).select_related('categoria').order_by('-fecha_creacion')
    
    # Obtener categorías con conteo de productos con stock
    categorias = Categoria.objects.all().annotate(
        productos_count=Count('producto', filter=Q(producto__cantidad__gt=0))
    ).order_by('nombre')
    
    # Filtrar por categoría si se especifica
    categoria_id = request.GET.get('categoria')
    categoria_actual = None
    
    if categoria_id and categoria_id != 'todos':
        print(f"[DEBUG] Filtrando por categoria ID: {categoria_id}")
        productos = productos.filter(categoria_id=categoria_id)
        try:
            categoria_actual = Categoria.objects.get(id=categoria_id)
        except Categoria.DoesNotExist:
            print("[DEBUG] Categoria no encontrada")
            pass
    
    print(f"[DEBUG] Productos encontrados: {productos.count()}")
    context = {
        'productos': productos,
        'categorias': categorias,
        'categoria_actual': categoria_actual
    }
    return render(request, 'productoC.html', context)

def verproductoC(request, producto_id):
    """Detalle de producto para CLIENTES (usa verproductoC.html)"""
    print(f"[DEBUG] EJECUTANDO: verproductoC view - ID: {producto_id}")
    print(f"[DEBUG] Usuario: {request.user}")
    
    producto = get_object_or_404(Producto, id=producto_id)
    print(f"[DEBUG] Producto encontrado: {producto.nombre}")
    
    # Productos relacionados de la misma categoría (solo con stock)
    productos_relacionados = Producto.objects.filter(
        categoria=producto.categoria,
        cantidad__gt=0  # Solo productos con stock
    ).exclude(id=producto.id)[:4]
    
    print(f"[DEBUG] Productos relacionados: {productos_relacionados.count()}")
    
    return render(request, 'verproductoC.html', {
        'producto': producto,
        'productos_relacionados': productos_relacionados
    })


# ==================================================
# VISTA CARRITO
# ==================================================
@login_required
def carrito(request):
    """Vista del carrito de compras"""
    print("[DEBUG] EJECUTANDO: carrito view")
    print(f"[DEBUG] Usuario: {request.user}")
    
    # Obtener o crear carrito activo del usuario
    carrito, created = Carrito.objects.get_or_create(
        usuario=request.user, 
        activo=True
    )
    
    items_carrito = carrito.items.select_related('producto').all()
    total_carrito = carrito.subtotal
    
    context = {
        'carrito': carrito,
        'items_carrito': items_carrito,
        'total_carrito': total_carrito,
    }
    return render(request, 'carrito.html', context)

@login_required
def agregar_al_carrito(request, producto_id):
    """Agregar producto al carrito"""
    print(f"[DEBUG] Agregando producto {producto_id} al carrito")
    
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id)
        cantidad = int(request.POST.get('cantidad', 1))
        
        print(f"[DEBUG] Producto: {producto.nombre}, Cantidad: {cantidad}")
        
        # Verificar stock
        if cantidad > producto.cantidad:
            messages.error(request, f'Stock insuficiente. Solo hay {producto.cantidad} unidades disponibles.')
            return redirect('productos_cliente')
        
        # Obtener carrito activo del usuario
        carrito, created = Carrito.objects.get_or_create(
            usuario=request.user, 
            activo=True
        )
        
        # Verificar si el producto ya está en el carrito
        item_existente = ProductoCarrito.objects.filter(
            carrito=carrito,
            producto=producto
        ).first()
        
        if item_existente:
            # Actualizar cantidad si ya existe
            nueva_cantidad = item_existente.cantidad + cantidad
            if nueva_cantidad > producto.cantidad:
                messages.error(request, f'No puedes agregar más de {producto.cantidad} unidades.')
                return redirect('productos_cliente')
            
            item_existente.cantidad = nueva_cantidad
            item_existente.save()
            messages.success(request, f'Actualizado: {producto.nombre} - {item_existente.cantidad} unidades')
        else:
            # Crear nuevo item en el carrito
            ProductoCarrito.objects.create(
                carrito=carrito,
                producto=producto,
                cantidad=cantidad
            )
            messages.success(request, f'¡{producto.nombre} agregado al carrito!')
        
        return redirect('carrito')
    
    return redirect('productos_cliente')

@login_required
def eliminar_del_carrito(request, item_id):
    """Eliminar item del carrito"""
    item = get_object_or_404(ProductoCarrito, id=item_id, carrito__usuario=request.user)
    producto_nombre = item.producto.nombre
    item.delete()
    
    messages.success(request, f'{producto_nombre} eliminado del carrito')
    return redirect('carrito')

@login_required
def actualizar_cantidad_carrito(request, item_id):
    """Actualizar cantidad de un item en el carrito"""
    if request.method == 'POST':
        item = get_object_or_404(ProductoCarrito, id=item_id, carrito__usuario=request.user)
        accion = request.POST.get('accion')
        
        if accion == 'incrementar':
            if item.cantidad < item.producto.cantidad:
                item.cantidad += 1
                item.save()
                messages.success(request, 'Cantidad actualizada')
            else:
                messages.error(request, 'No hay más stock disponible')
        elif accion == 'decrementar':
            if item.cantidad > 1:
                item.cantidad -= 1
                item.save()
                messages.success(request, 'Cantidad actualizada')
            else:
                # Si la cantidad sería 0, eliminar el item
                item.delete()
                messages.success(request, 'Producto eliminado del carrito')
    
    return redirect('carrito')

@login_required
def vaciar_carrito(request):
    """Vaciar todo el carrito del usuario"""
    if request.method == 'POST':
        carrito = get_object_or_404(Carrito, usuario=request.user, activo=True)
        carrito.items.all().delete()
        messages.success(request, 'Carrito vaciado correctamente')
    
    return redirect('carrito')
# ==================================================

@login_required
def miperfil(request):
    """Perfil del usuario"""
    print("[DEBUG] EJECUTANDO: miperfil view")
    print(f"[DEBUG] Usuario: {request.user}")
    return render(request, 'miperfil.html')

@login_required
def suscripcion(request):
    """Gestion de suscripciones"""
    print("[DEBUG] EJECUTANDO: suscripcion view")
    print(f"[DEBUG] Usuario: {request.user}")
    return render(request, 'suscripcion.html')

# ==================================================
# MANTENEDOR GENERAL DE PRODUCTOS (SOLO ADMIN)
# ==================================================

@login_required
def indexM(request):
    """Página del mantenedor - SOLO para admins"""
    print("[DEBUG] EJECUTANDO: indexM view")
    print(f"[DEBUG] Usuario: {request.user}")
    
    # Verificación directa SIN decorador
    if not hasattr(request.user, 'perfil') or request.user.perfil.rol != 3:
        print("[DEBUG] Usuario NO es admin, redirigiendo a home")
        messages.error(request, "No tienes permisos de administrador")
        return redirect('home')
    
    print("[DEBUG] Usuario es admin, mostrando indexM")
    return render(request, 'mantenedor/indexM.html')

@login_required
def mantenedor_lista_productos(request):
    """
    Vista para mostrar la lista de productos (productos.html)
    """
    print("[DEBUG] EJECUTANDO: mantenedor_lista_productos view")
    print(f"[DEBUG] Usuario: {request.user}")
    
    # Obtener todos los productos inicialmente
    productos = Producto.objects.all().select_related('categoria').order_by('-fecha_creacion')
    
    # Obtener categorías para el filtro
    categorias = Categoria.objects.all().annotate(
        productos_count=Count('producto')
    ).order_by('nombre')
    
    # ============================================
    # AGREGAR EL FILTRO (igual que en productos)
    # ============================================
    categoria_id = request.GET.get('categoria')
    categoria_actual = None
    
    if categoria_id and categoria_id != 'todos':
        print(f"[DEBUG] Filtrando por categoria ID: {categoria_id}")
        productos = productos.filter(categoria_id=categoria_id)
        try:
            categoria_actual = Categoria.objects.get(id=categoria_id)
        except Categoria.DoesNotExist:
            print("[DEBUG] Categoria no encontrada")
            pass
    # ============================================
    
    # Calcular estadísticas (DESPUÉS del filtro)
    productos_con_stock = productos.filter(cantidad__gt=0).count()
    productos_bajo_stock = productos.filter(cantidad__lt=5, cantidad__gt=0).count()
    categorias_count = Categoria.objects.count()
    
    print(f"[DEBUG] Estadisticas - Con stock: {productos_con_stock}, Bajo stock: {productos_bajo_stock}")
    print(f"[DEBUG] Productos totales mostrados: {productos.count()}")
    
    context = {
        'productos': productos,
        'categorias': categorias,
        'productos_con_stock': productos_con_stock,
        'productos_bajo_stock': productos_bajo_stock,
        'categorias_count': categorias_count,
        'categoria_actual': categoria_actual,  # IMPORTANTE: agregar esto
        'titulo': 'Lista de Productos'
    }
    return render(request, 'mantenedor/productos.html', context)

@login_required
def mantenedor_agregar_producto(request):
    """
    Agregar nuevo producto - Mantenedor general
    """
    print("[DEBUG] EJECUTANDO: mantenedor_agregar_producto view")
    print(f"[DEBUG] Usuario: {request.user}")
    
    if request.method == 'POST':
        print("[DEBUG] Agregar producto POST request")
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                producto = form.save()
                print(f"[DEBUG] Producto agregado: {producto.nombre}")
                messages.success(request, f"Producto '{producto.nombre}' agregado correctamente!")
                return redirect('mantenedor_lista_productos')
            except Exception as e:
                print(f"[DEBUG] Error al guardar producto: {str(e)}")
                messages.error(request, f"Error al guardar el producto: {str(e)}")
        else:
            print("[DEBUG] Formulario invalido")
            messages.error(request, "Por favor corrige los errores en el formulario")
    else:
        print("[DEBUG] Mostrando formulario agregar producto")
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
    print(f"[DEBUG] EJECUTANDO: mantenedor_editar_producto view - ID: {producto_id}")
    print(f"[DEBUG] Usuario: {request.user}")
    
    producto = get_object_or_404(Producto, id=producto_id)
    print(f"[DEBUG] Editando producto: {producto.nombre}")
    
    if request.method == 'POST':
        print("[DEBUG] Editar producto POST request")
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            # Manejar eliminación de imagen
            if 'eliminar_imagen' in request.POST:
                if producto.imagen:
                    print("[DEBUG] Eliminando imagen del producto")
                    producto.imagen.delete(save=False)
            
            producto_actualizado = form.save()
            print(f"[DEBUG] Producto actualizado: {producto_actualizado.nombre}")
            messages.success(request, f"Producto '{producto_actualizado.nombre}' actualizado correctamente!")
            return redirect('mantenedor_lista_productos')
        else:
            print("[DEBUG] Formulario invalido")
            messages.error(request, "Por favor corrige los errores en el formulario")
    else:
        print("[DEBUG] Mostrando formulario editar producto")
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
    print(f"[DEBUG] EJECUTANDO: mantenedor_eliminar_producto view - ID: {producto_id}")
    print(f"[DEBUG] Usuario: {request.user}")
    
    producto = get_object_or_404(Producto, id=producto_id)
    print(f"[DEBUG] Eliminando producto: {producto.nombre}")
    
    if request.method == 'POST':
        nombre_producto = producto.nombre
        producto.delete()
        print(f"[DEBUG] Producto eliminado: {nombre_producto}")
        messages.success(request, f"Producto '{nombre_producto}' eliminado correctamente!")
        return redirect('mantenedor_lista_productos')
    
    print("[DEBUG] Mostrando confirmacion de eliminacion")
    return render(request, 'mantenedor/eliminar_producto.html', {
        'producto': producto
    })

# ==================================================
# PROVEEDORES 
# ==================================================

@login_required
def proveedor_productos(request):
    """Lista de productos del proveedor logueado"""
    print("[DEBUG] EJECUTANDO: proveedor_productos view")
    print(f"[DEBUG] Usuario: {request.user}")
    
    try:
        proveedor = request.user.proveedor
        print(f"[DEBUG] Proveedor encontrado: {proveedor}")
        productos = Producto.objects.filter(proveedor=proveedor).order_by('-fecha_creacion')
        print(f"[DEBUG] Productos del proveedor: {productos.count()}")
        return render(request, 'proveedor/productos.html', {
            'productos': productos,
            'proveedor': proveedor
        })
    except Proveedor.DoesNotExist:
        print("[DEBUG] Usuario no es proveedor")
        messages.error(request, "Solo los proveedores pueden gestionar productos")
        return redirect('home')

@login_required
def proveedor_agregar_producto(request):
    """Agregar nuevo producto (proveedores)"""
    print("[DEBUG] EJECUTANDO: proveedor_agregar_producto view")
    
    try:
        proveedor = request.user.proveedor
        print(f"[DEBUG] Proveedor: {proveedor}")
    except Proveedor.DoesNotExist:
        print("[DEBUG] Usuario no es proveedor")
        messages.error(request, "Solo los proveedores pueden agregar productos")
        return redirect('home')
    
    if request.method == 'POST':
        print("[DEBUG] Proveedor agregar producto POST request")
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.proveedor = proveedor
            producto.save()
            print(f"[DEBUG] Producto agregado por proveedor: {producto.nombre}")
            messages.success(request, f"Producto '{producto.nombre}' agregado correctamente!")
            return redirect('proveedor_productos')
    else:
        print("[DEBUG] Mostrando formulario proveedor agregar producto")
        form = ProductoForm()
    
    return render(request, 'proveedor/form_producto.html', {
        'form': form,
        'titulo': 'Agregar Producto'
    })

@login_required
def proveedor_editar_producto(request, producto_id):
    """Editar producto existente (proveedores)"""
    print(f"[DEBUG] EJECUTANDO: proveedor_editar_producto view - ID: {producto_id}")
    
    producto = get_object_or_404(Producto, id=producto_id)
    print(f"[DEBUG] Producto a editar: {producto.nombre}")
    
    try:
        if producto.proveedor != request.user.proveedor:
            print("[DEBUG] Usuario no tiene permisos para editar este producto")
            messages.error(request, "No tienes permisos para editar este producto")
            return redirect('proveedor_productos')
    except Proveedor.DoesNotExist:
        print("[DEBUG] Usuario no es proveedor")
        messages.error(request, "Solo los proveedores pueden editar productos")
        return redirect('proveedor_productos')
    
    if request.method == 'POST':
        print("[DEBUG] Proveedor editar producto POST request")
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            print(f"[DEBUG] Producto actualizado por proveedor: {producto.nombre}")
            messages.success(request, f"Producto actualizado correctamente!")
            return redirect('proveedor_productos')
    else:
        print("[DEBUG] Mostrando formulario proveedor editar producto")
        form = ProductoForm(instance=producto)
    
    return render(request, 'proveedor/form_producto.html', {
        'form': form,
        'titulo': 'Editar Producto'
    })

@login_required
def proveedor_eliminar_producto(request, producto_id):
    """Eliminar producto (proveedores)"""
    print(f"[DEBUG] EJECUTANDO: proveedor_eliminar_producto view - ID: {producto_id}")
    
    producto = get_object_or_404(Producto, id=producto_id)
    print(f"[DEBUG] Producto a eliminar: {producto.nombre}")
    
    try:
        if producto.proveedor != request.user.proveedor:
            print("[DEBUG] Usuario no tiene permisos para eliminar este producto")
            messages.error(request, "No tienes permisos para eliminar este producto")
            return redirect('proveedor_productos')
    except Proveedor.DoesNotExist:
        print("[DEBUG] Usuario no es proveedor")
        messages.error(request, "Solo los proveedores pueden eliminar productos")
        return redirect('proveedor_productos')
    
    if request.method == 'POST':
        nombre_producto = producto.nombre
        producto.delete()
        print(f"[DEBUG] Producto eliminado por proveedor: {nombre_producto}")
        messages.success(request, f"Producto '{nombre_producto}' eliminado correctamente!")
        return redirect('proveedor_productos')
    
    print("[DEBUG] Mostrando confirmacion proveedor eliminar producto")
    return render(request, 'proveedor/confirmar_eliminar.html', {'producto': producto})

# ==================================================
# PANEL DE ADMINISTRACIÓN (SUPERUSUARIOS)
# ==================================================

@login_required
def admin_panel_productos(request):
    """Panel de administración - TODOS los productos"""
    print("[DEBUG] EJECUTANDO: admin_panel_productos view")
    print(f"[DEBUG] Usuario: {request.user}")
    
    if not request.user.is_superuser:
        print("[DEBUG] Usuario no es superusuario")
        messages.error(request, "No tienes permisos de administrador")
        return redirect('home')
    
    productos = Producto.objects.all().select_related('proveedor', 'categoria')
    print(f"[DEBUG] Total productos en admin panel: {productos.count()}")
    return render(request, 'admin/panel_productos.html', {
        'productos': productos
    })

# ==================================================
# VISTA DE LISTA DE PRODUCTOS PARA REDIRECCIÓN
# ==================================================

@login_required
def lista_productos(request):
    """
    Vista para mostrar la lista de productos (productos.html)
    Esta es la vista a la que se redirige despues de agregar un producto
    """
    print("[DEBUG] EJECUTANDO: lista_productos view")
    
    productos = Producto.objects.all().select_related('categoria').order_by('-fecha_creacion')
    
    # Calcular estadísticas
    productos_con_stock = productos.filter(cantidad__gt=0).count()
    productos_bajo_stock = productos.filter(cantidad__lt=5, cantidad__gt=0).count()
    categorias_count = Categoria.objects.count()
    
    print(f"[DEBUG] Estadisticas lista productos - Con stock: {productos_con_stock}")
    
    context = {
        'productos': productos,
        'productos_con_stock': productos_con_stock,
        'productos_bajo_stock': productos_bajo_stock,
        'categorias_count': categorias_count,
        'titulo': 'Lista de Productos'
    }
    return render(request, 'mantenedor/productos.html', context)

# ==================================================
# REDIRECCIONES PARA COMPATIBILIDAD (ACTUALIZADAS)
# ==================================================

def gestionproducto(request):
    """Redirección para compatibilidad - Ahora al mantenedor general"""
    print("[DEBUG] EJECUTANDO: gestionproducto view - Redirigiendo a mantenedor")
    return redirect('mantenedor_lista_productos')

def detalle_producto(request, producto_id):
    """Redirección para compatibilidad"""
    print(f"[DEBUG] EJECUTANDO: detalle_producto view - Redirigiendo a verproducto ID: {producto_id}")
    return redirect('verproducto', producto_id=producto_id)

def error_404(request, exception=None):
    """Página de error 404"""
    print("[DEBUG] EJECUTANDO: error_404 view")
    return render(request, '404.html', status=404)

# ==================================================
# VISTAS ADICIONALES PARA COMPLETAR EL SISTEMA
# ==================================================

@login_required
def editar_producto(request, producto_id):
    """
    Vista genérica para editar producto
    """
    print(f"[DEBUG] EJECUTANDO: editar_producto view - ID: {producto_id}")
    
    producto = get_object_or_404(Producto, id=producto_id)
    print(f"[DEBUG] Editando producto generico: {producto.nombre}")
    
    if request.method == 'POST':
        print("[DEBUG] Editar producto generico POST request")
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            producto_actualizado = form.save()
            print(f"[DEBUG] Producto actualizado generico: {producto_actualizado.nombre}")
            messages.success(request, f'Producto "{producto_actualizado.nombre}" actualizado exitosamente!')
            return redirect('lista_productos')
    else:
        print("[DEBUG] Mostrando formulario editar producto generico")
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
    print(f"[DEBUG] EJECUTANDO: eliminar_producto view - ID: {producto_id}")
    
    producto = get_object_or_404(Producto, id=producto_id)
    print(f"[DEBUG] Eliminando producto generico: {producto.nombre}")
    
    if request.method == 'POST':
        nombre_producto = producto.nombre
        producto.delete()
        print(f"[DEBUG] Producto eliminado generico: {nombre_producto}")
        messages.success(request, f'Producto "{nombre_producto}" eliminado exitosamente!')
        return redirect('lista_productos')
    
    print("[DEBUG] Mostrando confirmacion eliminacion generica")
    return render(request, 'confirmar_eliminar.html', {'producto': producto})

@login_required
def detalle_producto_admin(request, producto_id):
    """
    Vista de detalle de producto para administración
    """
    print(f"[DEBUG] EJECUTANDO: detalle_producto_admin view - ID: {producto_id}")
    
    producto = get_object_or_404(Producto, id=producto_id)
    print(f"[DEBUG] Detalle admin producto: {producto.nombre}")
    
    context = {
        'producto': producto,
        'titulo': f'Detalle: {producto.nombre}'
    }
    return render(request, 'detalle_producto.html', context)
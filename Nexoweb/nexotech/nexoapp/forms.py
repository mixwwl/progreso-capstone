from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Perfil, Cliente, Proveedor, Empresa, Producto, Categoria

# ==================================================
# FORMULARIO DE REGISTRO (CREACIÓN DE USUARIOS)
# ==================================================
class RegistroForm(UserCreationForm):
    """
    Formulario personalizado para el REGISTRO de nuevos usuarios.
    Maneja la creación de clientes y proveedores con sus perfiles asociados.
    """
    
    # Campo de email personalizado
    email = forms.EmailField(
        required=True,
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"placeholder": "tu@email.com"})
    )

    # Opciones de rol con IDs numéricos para mejor organización en Admin
    ROL_PUBLICO = [
        (1, "Cliente"),     # ID 1 para clientes
        (2, "Proveedor"),   # ID 2 para proveedores
    ]
    
    # Campo para seleccionar tipo de cuenta
    rol = forms.ChoiceField(
        choices=ROL_PUBLICO,
        required=True,
        label="Tipo de cuenta"
    )

    # Campo opcional para nombre de empresa (solo proveedores)
    empresa = forms.CharField(
        required=False,
        label="Empresa (si eres proveedor)",
        widget=forms.TextInput(attrs={"placeholder": "Nombre de la empresa"})
    )

    class Meta:
        model = User  # Usa el modelo User por defecto de Django
        fields = ["username", "email", "password1", "password2", "rol", "empresa"]
        labels = {
            "username": "Usuario",
            "password1": "Contraseña", 
            "password2": "Confirmar contraseña",
        }
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Tu usuario"}),
        }

    def __init__(self, *args, **kwargs):
        """
        Inicialización del formulario.
        Oculta los textos de ayuda automáticos de Django para una UI más limpia.
        """
        super().__init__(*args, **kwargs)

        # Ocultar los help_text largos y técnicos de Django
        for field in self.fields.values():
            field.help_text = ""

    def save(self, commit=True):
        """
        Guarda el usuario y crea los modelos relacionados automáticamente.
        - Usa el Perfil creado automáticamente por la señal post_save
        - Actualiza el rol en ese perfil
        - Crea Cliente o Proveedor según el rol
        - Para proveedores, crea o asocia la empresa
        """
        # 1️⃣ Crear el usuario base con UserCreationForm
        user = super().save(commit=commit)

        # 2️⃣ Obtener el rol como entero (1 o 2)
        rol = int(self.cleaned_data["rol"])

        # 3️⃣ Actualizar el perfil creado automáticamente por la señal
        perfil = user.perfil  # OneToOneField → acceso directo
        perfil.rol = rol
        perfil.save()

        # 4️⃣ Crear o asociar entidad según el rol
        if rol == 1:  # Cliente
            Cliente.objects.get_or_create(user=user)
        else:  # Proveedor
            nombre_empresa = (self.cleaned_data.get("empresa") or "").strip()
            empresa_obj = None

            # Si hay nombre de empresa, buscarla o crearla
            if nombre_empresa:
                empresa_obj, _ = Empresa.objects.get_or_create(nombre=nombre_empresa)

            Proveedor.objects.get_or_create(user=user, defaults={"empresa": empresa_obj})

        # 5️⃣ Retornar el usuario final
        return user


# ==================================================
# FORMULARIO DE LOGIN (INICIO DE SESIÓN)
# ==================================================
class EmailAuthenticationForm(AuthenticationForm):
    """
    Formulario personalizado para el LOGIN de usuarios.
    Utiliza email como campo principal en lugar de username.
    """
    
    username = forms.EmailField(
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={"placeholder": "tu@email.com"})
    )
    
    def clean_username(self):
        """
        LOGIN: Valida y procesa el campo de email.
        Si existe un usuario con ese email, devuelve su username para la autenticación.
        Si no existe, devuelve el email para que falle la autenticación normalmente.
        """
        email = self.cleaned_data['username']
        
        try:
            user = User.objects.get(email=email)
            return user.username
        except User.DoesNotExist:
            return email


# ==================================================
# FORMULARIO DE PRODUCTOS (MANTENEDOR)
# ==================================================
class ProductoForm(forms.ModelForm):
    """
    Formulario para crear y editar productos en el mantenedor.
    Incluye validaciones personalizadas y campos con placeholders.
    """
    
    nueva_categoria = forms.CharField(
        required=False,
        max_length=100,
        label="O crear nueva categoría",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Herramientas Digitales'
        })
    )
    
    class Meta:
        model = Producto
        fields = ['codigo_producto', 'nombre', 'descripcion', 'cantidad', 'precio', 'categoria', 'imagen', 'estado']
        labels = {
            'codigo_producto': 'Código del Producto',
            'nombre': 'Nombre del Producto', 
            'descripcion': 'Descripción',
            'cantidad': 'Stock Disponible',
            'precio': 'Precio ($)',
            'categoria': 'Seleccionar categoría existente',
            'imagen': 'Imagen del Producto',
            'estado': 'Estado del Producto',
        }
        widgets = {
            'codigo_producto': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: PROD-001'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: Martillo Profesional'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Describe las características del producto...'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '0',
                'min': '0'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.webp'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = Categoria.objects.all().order_by('nombre')
        self.fields['categoria'].empty_label = "---------"
        self.fields['categoria'].required = False

    def clean(self):
        cleaned_data = super().clean()
        categoria = cleaned_data.get('categoria')
        nueva_categoria = cleaned_data.get('nueva_categoria', '').strip()
        
        if not categoria and not nueva_categoria:
            raise forms.ValidationError({
                'categoria': 'Debes seleccionar una categoría existente o crear una nueva.',
                'nueva_categoria': 'Debes seleccionar una categoría existente o crear una nueva.'
            })
        
        if categoria and nueva_categoria:
            cleaned_data['nueva_categoria'] = ''
            self.add_warning('nueva_categoria', 'Se usará la categoría existente seleccionada y se ignorará la nueva categoría.')
        
        if nueva_categoria and not categoria:
            if Categoria.objects.filter(nombre__iexact=nueva_categoria).exists():
                raise forms.ValidationError({
                    'nueva_categoria': f'Ya existe una categoría con el nombre "{nueva_categoria}".'
                })
        
        return cleaned_data

    def add_warning(self, field, message):
        if field in self.errors:
            self.errors[field].append(message)
        else:
            self.errors[field] = [message]

    def clean_codigo_producto(self):
        codigo_producto = self.cleaned_data.get('codigo_producto')
        
        if self.instance and self.instance.pk:
            if Producto.objects.filter(codigo_producto=codigo_producto).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('Ya existe un producto con este código.')
        elif Producto.objects.filter(codigo_producto=codigo_producto).exists():
            raise forms.ValidationError('Ya existe un producto con este código.')
            
        return codigo_producto

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad < 0:
            raise forms.ValidationError('La cantidad no puede ser negativa.')
        return cantidad

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio <= 0:
            raise forms.ValidationError('El precio debe ser mayor a 0.')
        return precio

    def save(self, commit=True):
        nueva_categoria_nombre = self.cleaned_data.get('nueva_categoria', '').strip()
        
        if nueva_categoria_nombre and not self.cleaned_data.get('categoria'):
            nueva_categoria = Categoria.objects.create(
                nombre=nueva_categoria_nombre,
                descripcion=f'Categoría: {nueva_categoria_nombre}'
            )
            self.instance.categoria = nueva_categoria
        
        return super().save(commit=commit)


# ==================================================
# FORMULARIO DE CATEGORÍAS (OPCIONAL)
# ==================================================
class CategoriaForm(forms.ModelForm):
    """
    Formulario para crear y editar categorías de productos.
    """
    
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']
        labels = {
            'nombre': 'Nombre de la Categoría',
            'descripcion': 'Descripción',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Herramientas Eléctricas'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe esta categoría...'
            }),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if Categoria.objects.filter(nombre__iexact=nombre).exists():
            if not self.instance or self.instance.nombre != nombre:
                raise forms.ValidationError('Ya existe una categoría con este nombre.')
        return nombre

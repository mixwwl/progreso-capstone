from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Perfil, Cliente, Proveedor, Empresa, Producto, Categoria

class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Correo electronico",
        widget=forms.EmailInput(attrs={"placeholder": "tu@email.com"})
    )

    ROL_PUBLICO = [
        (1, "Cliente"),
        (2, "Proveedor"),
    ]
    
    rol = forms.ChoiceField(
        choices=ROL_PUBLICO,
        required=True,
        label="Tipo de cuenta"
    )

    empresa = forms.CharField(
        required=False,
        label="Empresa (si eres proveedor)",
        widget=forms.TextInput(attrs={"placeholder": "Nombre de la empresa"})
    )

    class Meta:
        model = User
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
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = ""

    def save(self, commit=True):
        user = super().save(commit=commit)
        rol = int(self.cleaned_data["rol"])
        perfil = user.perfil
        perfil.rol = rol
        perfil.save()

        if rol == 1:
            Cliente.objects.get_or_create(user=user)
        else:
            nombre_empresa = (self.cleaned_data.get("empresa") or "").strip()
            empresa_obj = None
            if nombre_empresa:
                empresa_obj, _ = Empresa.objects.get_or_create(nombre=nombre_empresa)
            Proveedor.objects.get_or_create(user=user, defaults={"empresa": empresa_obj})

        return user

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Correo Electronico",
        widget=forms.EmailInput(attrs={"placeholder": "tu@email.com"})
    )
    
    def clean_username(self):
        email = self.cleaned_data['username']
        try:
            user = User.objects.get(email=email)
            return user.username
        except User.DoesNotExist:
            return email

class ProductoForm(forms.ModelForm):
    nueva_categoria = forms.CharField(
        required=False,
        max_length=100,
        label="O crear nueva categoria",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Herramientas Digitales'
        })
    )
    
    class Meta:
        model = Producto
        fields = ['codigo_producto', 'nombre', 'descripcion', 'cantidad', 'precio', 'categoria', 'imagen']
        labels = {
            'codigo_producto': 'Codigo del Producto',
            'nombre': 'Nombre del Producto', 
            'descripcion': 'Descripcion',
            'cantidad': 'Stock Disponible',
            'precio': 'Precio ($)',
            'categoria': 'Seleccionar categoria existente',
            'imagen': 'Imagen del Producto',
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
                'placeholder': 'Describe las caracteristicas del producto...'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '0',
                'min': '0'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '0',
                'min': '1'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.webp'
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
                'categoria': 'Debes seleccionar una categoria existente o crear una nueva.',
                'nueva_categoria': 'Debes seleccionar una categoria existente o crear una nueva.'
            })
        
        if categoria and nueva_categoria:
            cleaned_data['nueva_categoria'] = ''
            self.add_warning('nueva_categoria', 'Se usara la categoria existente seleccionada y se ignorara la nueva categoria.')
        
        if nueva_categoria and not categoria:
            if Categoria.objects.filter(nombre__iexact=nueva_categoria).exists():
                raise forms.ValidationError({
                    'nueva_categoria': f'Ya existe una categoria con el nombre "{nueva_categoria}".'
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
                raise forms.ValidationError('Ya existe un producto con este codigo.')
        elif Producto.objects.filter(codigo_producto=codigo_producto).exists():
            raise forms.ValidationError('Ya existe un producto con este codigo.')
            
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
                descripcion=f'Categoria: {nueva_categoria_nombre}'
            )
            self.instance.categoria = nueva_categoria
        
        return super().save(commit=commit)

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']
        labels = {
            'nombre': 'Nombre de la Categoria',
            'descripcion': 'Descripcion',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Herramientas Electricas'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe esta categoria...'
            }),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if Categoria.objects.filter(nombre__iexact=nombre).exists():
            if not self.instance or self.instance.nombre != nombre:
                raise forms.ValidationError('Ya existe una categoria con este nombre.')
        return nombre
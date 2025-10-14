from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Perfil, Cliente, Proveedor, Empresa


class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"placeholder": "tu@email.com"})
    )

    ROL_PUBLICO = [("cliente", "Cliente"), ("proveedor", "Proveedor")]
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

        # Ocultar los help_text largos de Django
        for field in self.fields.values():
            field.help_text = ""

    def save(self, commit=True):
        user = super().save(commit=commit)
        rol = self.cleaned_data["rol"]

        # Crear perfil asociado
        Perfil.objects.create(user=user, rol=rol)

        if rol == "cliente":
            Cliente.objects.create(user=user)
        else:
            nombre_empresa = (self.cleaned_data.get("empresa") or "").strip()
            empresa_obj = None
            if nombre_empresa:
                empresa_obj, _ = Empresa.objects.get_or_create(nombre=nombre_empresa)

            Proveedor.objects.create(user=user, empresa=empresa_obj)

        return user

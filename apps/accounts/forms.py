from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import User


class MerchantRegistrationForm(UserCreationForm):

    merchant_name = forms.CharField(
        label='Merchant Name',
        help_text='Your name or business name.',
    )
    email = forms.EmailField(
        required=True,
        help_text='Used for password recovery.',
    )

    class Meta:
        model = User
        fields = ['merchant_name', 'username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean_merchant_name(self):
        name = self.cleaned_data.get('merchant_name', '').strip()
        if not name:
            raise ValidationError("Merchant name cannot be blank.")
        return name

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['merchant_name']
        user.email = self.cleaned_data['email']
        user.role = 'MERCHANT'
        if commit:
            user.save()
        return user


class ConTrackLoginForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

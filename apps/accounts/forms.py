import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import User

PH_PHONE_ATTRS = {
    'type':        'tel',
    'placeholder': '09XXXXXXXXX',
    'maxlength':   '11',
    'pattern':     '09[0-9]{9}',
    'inputmode':   'numeric',
    'oninput':     "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 11)",
    'class':       'form-control',
}


def validate_ph_phone(value):
    if value and not re.match(r'^09\d{9}$', value):
        raise ValidationError('Enter a valid Philippine mobile number (e.g., 09171234567)')


class MerchantRegistrationForm(UserCreationForm):

    merchant_name = forms.CharField(label='Merchant Name')
    email         = forms.EmailField(required=True)
    phone_number  = forms.CharField(
        label='Phone Number',
        max_length=11,
        required=False,
        validators=[validate_ph_phone],
        widget=forms.TextInput(attrs=PH_PHONE_ATTRS),
    )

    class Meta:
        model  = User
        fields = ['merchant_name', 'username', 'email', 'phone_number', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'merchant_name': 'Merchant Name',
            'username':      'Username',
            'email':         'Email address',
            'password1':     'Password',
            'password2':     'Confirm password',
        }
        for name, field in self.fields.items():
            field.help_text = ''
            if name != 'phone_number':
                field.widget.attrs.setdefault('class', 'form-control')
            if name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[name]

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        if User.objects.filter(email=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def clean_merchant_name(self):
        name = self.cleaned_data.get('merchant_name', '').strip()
        if not name:
            raise ValidationError('Merchant name cannot be blank.')
        return name

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name   = self.cleaned_data['merchant_name']
        user.email        = self.cleaned_data['email']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        user.role         = 'MERCHANT'
        if commit:
            user.save()
        return user


class ConTrackLoginForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {'username': 'Username', 'password': 'Password'}
        for name, field in self.fields.items():
            field.help_text = ''
            field.widget.attrs.setdefault('class', 'form-control')
            if name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[name]

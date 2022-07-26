from django.contrib.auth.forms import UserCreationForm
from django import forms

from django.contrib.auth.models import User


class UserRegisterForm(UserCreationForm):
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'autocomplete': 'off',
                   'placeholder': '150 characters or fewer; letters, digits and @/./+/-/_ only'}
        ),
    )
    first_name = forms.CharField(
        label='First name',
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'autocomplete': 'off', 'placeholder': '(optional)'}
        ),
    )
    last_name = forms.CharField(
        label='Last name',
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'autocomplete': 'off', 'placeholder': '(optional)'}
        ),
    )
    email = forms.EmailField(
        label='Email address',
        required=False,
        widget=forms.EmailInput(
            attrs={'class': 'form-control', 'autocomplete': 'off', 'placeholder': '(optional)'}
        ),
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(
            attrs={'class': 'form-control',
                   'placeholder': 'your password can’t be entirely numeric'}
        ),
    )
    password2 = forms.CharField(
        label='Password confirmation',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'required'}),
    )
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

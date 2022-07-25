from django.contrib.auth.forms import UserCreationForm
from django import forms

from django.contrib.auth.models import User


class UserRegisterForm(UserCreationForm):
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
        help_text='150 characters or fewer. Letters, digits and @/./+/-/_ only.',
    )
    first_name = forms.CharField(
        label='First name',
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
    )
    last_name = forms.CharField(
        label='Last name',
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Your password can’t be entirely numeric.',
    )
    password2 = forms.CharField(
        label='Password confirmation',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Enter the same password as before, for verification.',
    )
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password1', 'password2']

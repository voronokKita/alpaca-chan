import sys

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms

from django.contrib.auth.models import User


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )


class UserRegisterForm(UserCreationForm):
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'autocomplete': 'off',
                   'placeholder': '150 characters or fewer; '
                                  'letters, digits and @/./+/-/_ only'}
        ),
    )
    first_name = forms.CharField(
        label='First name',
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'autocomplete': 'off',
                   'placeholder': '(optional)'}
        ),
    )
    last_name = forms.CharField(
        label='Last name',
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'autocomplete': 'off',
                   'placeholder': '(optional)'}
        ),
    )
    email = forms.EmailField(
        label='Email address',
        required=False,
        widget=forms.EmailInput(
            attrs={'class': 'form-control', 'autocomplete': 'off',
                   'placeholder': '(optional)'}
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
        widget=forms.PasswordInput(attrs={'class': 'form-control',
                                          'placeholder': 'required'}),
    )
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name',
                  'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            self._get_auctions_profile(user)
        return user

    @staticmethod
    def _get_auctions_profile(user):
        if 'test' in sys.argv and \
                not [True for arg in sys.argv if 'auctions' in arg]:
            # testing some other app
            return

        from auctions.models import Profile
        if not Profile.manager.filter(username=user.username).exists():
            profile = Profile(username=user.username, user_model_pk=user.pk)
            profile.save()

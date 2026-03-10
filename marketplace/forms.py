from django import forms
from django.contrib.auth.models import User


class RegisterForm(forms.ModelForm):

    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
        ]

    def clean(self):

        cleaned_data = super().clean()

        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")

        if p1 != p2:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data
from django import forms
from .models import Organization
from django.contrib.auth.models import User

import random
import string

class LoginForm(forms.Form):
    adminEmail=forms.CharField(max_length=30)
    password=forms.CharField(widget=forms.PasswordInput)
    
class RegistrationForm(forms.ModelForm):
    class Meta:
        model= Organization
        fields='__all__'
        exclude=('status','user')
        
    def clean_adminEmail(self):
        email = self.cleaned_data.get('adminEmail')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use by another user.")
        if Organization.objects.filter(adminEmail=email).exists():
            raise forms.ValidationError("This email is already used by another organization.")
        return email
    
    def save(self, commit = True):
        instance = super().save(commit=False)
        email=self.cleaned_data.get('adminEmail')

        if self.cleaned_data.get('status')!='rejected':
            password=''.join(random.choices(string.ascii_letters, k=4))
            user = User.objects.create_user(username=email, password=password)
            print(password)
            instance.user=user
            
        if commit:
            instance.save()

        return instance
    
class AdminSetupForm(forms.Form):
    email=forms.EmailField()
    username = forms.CharField(max_length=30)
    password = forms.CharField(widget=forms.PasswordInput)
    retypePassword = forms.CharField(widget=forms.PasswordInput)
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email
    
    def clean_retypePassword(self):
        password=self.cleaned_data['password']
        retypePasswprd=self.cleaned_data['retypePassword']
        
        if password and retypePasswprd and password != retypePasswprd:
            raise forms.ValidationError("Passwords do not match.")
        
        return retypePasswprd
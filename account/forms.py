from django import forms
from .models import Organization, Clients
from django.contrib.auth.models import User

import random
import string

class LoginForm(forms.Form):
    adminEmail=forms.CharField(max_length=30)
    password=forms.CharField(widget=forms.PasswordInput)
    
class OrganizationRegistrationForm(forms.ModelForm):
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
            if '@' in self.cleaned_data.get('adminEmail'):
                user_fullname=self.cleaned_data.get('adminEmail').split('@',1)[0]
            else:
                user_fullname=self.cleaned_data.get('adminEmail')
            if '.' in user_fullname:
                user_firstname=user_fullname.split('.',1)[0]
                # user_lastname=user_fullname.split('.',1)[1]
                # user_fullname=user_firstname+' '+user_lastname
            else:
                user_firstname=user_fullname
            user = User.objects.create_user(username=user_firstname, password=password, email=email)
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
    
    

    
class ClientRegistrationForm(forms.ModelForm):
    password=forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model=Clients
        fields='__all__'
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Get user from kwargs
        self.organization = kwargs.pop('org', None)  # Get user from kwargs
        super().__init__(*args, **kwargs)

        if self.organization:
            self.fields.pop('organization', None)

        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use by another user.")
        if Clients.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already used by another client and/or organization.")
        return email

    def save(self, commit = ...):
        instance = super().save(commit=False)
        
        firstName=self.cleaned_data.get('firstName')
        email=self.cleaned_data.get('email')
        password=self.cleaned_data.get('password')

        User.objects.create_user(username=firstName, email=email, password=password)
        print(password)
        if self.user.is_superuser:
            instance.organization=self.cleaned_data.get('organization')
        else:
            instance.organization=self.organization
        
        if commit:
            instance.save()

        return instance

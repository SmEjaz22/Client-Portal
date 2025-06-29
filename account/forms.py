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
        user_qs = User.objects.filter(email=email)
        if self.instance:
            user_qs = user_qs.exclude(email=self.instance.adminEmail)
        
        if user_qs.exists():
            raise forms.ValidationError("This email is already in use by another user.")
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
            user, user_create = User.objects.get_or_create(username=user_firstname, email=email)
            user.set_password(password)
            print(password)
            instance.user=user
            
        if commit:
            instance.save()
            user.save()

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
    


from django.utils.text import slugify
import uuid

def generate_unique_username(base_name):
    base = slugify(base_name) or "user"
    while True:
        username = f"{base}_{uuid.uuid4().hex[:6]}"
        if not User.objects.filter(username=username).exists():
            return username    

    
class ClientRegistrationForm(forms.ModelForm):
    password=forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model=Clients
        fields='__all__'
        exclude=['user']
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Get user from kwargs
        self.organization = kwargs.pop('org', None)  # Get user from kwargs
        super().__init__(*args, **kwargs)

        if self.user and not self.user.is_superuser:
            self.fields.pop('organization', None)

        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # if User.objects.filter(email=email).exists():
        #     raise forms.ValidationError("This email is already in use by another user.")
        # if Clients.objects.filter(email=email).exists():
        #     raise forms.ValidationError("This email is already used by another client and/or organization.")
        
        
        # Check for duplicate Clients (excluding current instance if editing)
        # client_qs = Clients.objects.filter(email=email)
        # if self.instance:
        #     client_qs = client_qs.exclude(pk=self.instance.pk)
        # if client_qs.exists():
        #     raise forms.ValidationError("This email is already used by another client and/or organization.")
        
        
        user_qs = User.objects.filter(email=email)
        if self.instance:
            user_qs = user_qs.exclude(email=self.instance.email)
        
        if user_qs.exists():
            raise forms.ValidationError("This email is already in use by another user.")
        
        
        return email

    def save(self, commit = ...):
        instance = super().save(commit=False)
        
        firstName=self.cleaned_data.get('firstName')
        email=self.cleaned_data.get('email')
        password=self.cleaned_data.get('password')

        username = generate_unique_username(firstName)

        user, user_create = User.objects.get_or_create(username=username, email=email)
        if password:
            print(password)
            user.set_password(password)
            
        if self.user.is_superuser:
            instance.organization=self.cleaned_data.get('organization')
        else:
            instance.organization=self.organization
        
        instance.user=user

        if commit:
            instance.save()
            user.save()

        return instance



class ChatForm(forms.Form):
    To=forms.ModelMultipleChoiceField(queryset=Organization.objects.none(),
                                      widget=forms.SelectMultiple(attrs={'size':5}),
                                      label='Send To',
                                      required=True)
    
    Heading = forms.CharField(max_length=30, required=True) # for single line input
    Description =forms.CharField(widget=forms.Textarea(attrs={
        'cols':40,
        'rows':5
    }),required=True)
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # if self.user and Clients.objects.filter(email=self.user.email).first() is not None:
        #     self.fields['To'].queryset = Clients.objects.filter(email=self.user)
        
        # As admin
        org = Organization.objects.filter(adminEmail=self.user.email).first()

        # Or as a client
        if not org:
            client = Clients.objects.filter(user=self.user).first()
            if client:
                org = client.organization

        if org:
            client_users = User.objects.filter(clients__organization=org)
            try:
                admin_user = User.objects.get(email=org.adminEmail)
            except User.DoesNotExist:
                admin_user = None

            # Combine admin and clients
            combined_users = client_users
            if admin_user:
                combined_users = combined_users | User.objects.filter(pk=admin_user.pk)

            self.fields['To'].queryset = combined_users.distinct().exclude(pk=self.user.pk)
            self.fields['To'].label_from_instance = lambda user: f'{user.username} - ({user.email})'
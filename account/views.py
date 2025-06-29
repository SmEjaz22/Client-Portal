from django.shortcuts import render, redirect

# Create your views here.
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView, LogoutView, PasswordChangeView

from .models import Organization, Clients, ChatHistory 
from .forms import OrganizationRegistrationForm, LoginForm, AdminSetupForm, ClientRegistrationForm, ChatForm


class CustomPasswordResetView(PasswordResetView):
    success_url=reverse_lazy('account:password_reset_done') # You set success_url on the view that does the redirect, not the one being redirected to.


def loginView(request):
    if User.objects.count() < 2:
        return redirect('account:adminSetup')
    else:
        pass

    if request.method!='POST':
        form=LoginForm()
    else:
        form=LoginForm(request.POST)
        if form.is_valid():
            cd=form.cleaned_data
            user=authenticate(request, username=cd.get('adminEmail'), # The default ModelBackend(authentication backend) authenticates users against the database using the user model of django.contrib.auth.
                                   password=cd.get('password'))
            
            org_exists=Organization.objects.filter(adminEmail=cd.get('adminEmail')).exists()
            client_exists=Clients.objects.filter(Q(email=cd.get('adminEmail')) | Q(firstName=cd.get('adminEmail'))).exists()
            user_exists=User.objects.filter(Q(username=cd.get('adminEmail')) | Q(email=cd.get('adminEmail'))).exists()
            if user is not None:
                if not org_exists and not user_exists:
                    return HttpResponse('Organization and/or User Does not exist!')
                
                elif org_exists:
                    org=Organization.objects.get(adminEmail=cd.get('adminEmail'))
                    # to use in statusView().
                    request.session['pending_status_email'] = org.adminEmail
                    
                    if org.status=='approved':
                        if user.is_active:
                            login(request,user)
                            request.session.pop('pending_status_email', None)
                            # This technique is super handy whenever you want to allow access to something before login, without creating real accounts, or without storing temporary users.  Why it’s secure: A user cannot change their session data from the frontend — it’s stored securely on the server.
                            return redirect('account:dashboard', org_id=org.id)
                        else:
                            return HttpResponse("Disabled account!")
                    else:
                        if user.username == org.adminEmail or user.email == org.adminEmail:
                            
                            return redirect('account:status', org_id=org.id)
                        else:
                            return HttpResponse('<h1>You are only allowed to access your own status. If you think this is a mistake. Contact support!</h1>')
                
                elif client_exists:
                    login(request, user)
                    return redirect('account:clientDashboard', user.email)
                    
                else: # Admin logging here.
                    login(request, user)
                    return redirect('account:admin', user.username)

            else:
                return HttpResponse("Invalid Login!")
    return render(request, 'account/login.html', {'form':form})


def orgregistrationView(request):
    if request.method!='POST':
        form=OrganizationRegistrationForm()
    else:
        form=OrganizationRegistrationForm(request.POST)
        if form.is_valid():
            request.session['pending_status_email'] = form.cleaned_data['adminEmail']
            org=form.save()
            return redirect('account:status', org_id=org.id)
    return render(request, 'account/register.html',{'form':form})


def statusView(request, org_id):
    org=get_object_or_404(Organization, id=org_id)
    
    # stored in session
    allowed_email = request.session.get('pending_status_email')
    
    if allowed_email != org.adminEmail:
        return HttpResponse("<h1>You are only allowed to access your own status. If you think this is a mistake, contact support.</h1>")

    return render(request, 'account/status.html', {'status':org.status})


@login_required
def userDashboard(request, org_id):
    user=request.user
    messages = ChatHistory.objects.filter(recipients=user).order_by('-timestamp')
    
    user=request.user.email
    try:
        org=Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return HttpResponse('<h1>You are only allowed to access your own dashboard. If you think this is a mistake. Contact support!</h1>')
    
    clients=Clients.objects.filter(organization=org)
    if '@' in org.adminEmail:
        user_fullname=org.adminEmail.split('@',1)[0]
    else:
        user_fullname=org.adminEmail
    if '.' in user_fullname:
        user_firstname=user_fullname.split('.',1)[0]
        user_lastname=user_fullname.split('.',1)[1]
        user_name=user_firstname+' '+user_lastname
    else:
        user_name=user_fullname
        
    if user==org.adminEmail:
        return render(request, 'account/userDashboard.html', {'org':org, 'user_name':user_name,'clients':clients, 'messages':messages})    
    else:
        return HttpResponse('<h1>You are only allowed to access your own dashboard. If you think this is a mistake. Contact support!</h1>')
    
    
@login_required
def orgDetail(request, org_id):
    if request.user.is_superuser:
        try:
            org=Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return HttpResponse('Organization does not exist.')
        if request.method!='POST':
            form=OrganizationRegistrationForm(instance=org)
        else:
            form=OrganizationRegistrationForm(request.POST, instance=org)
            if form.is_valid():
                form.save()
                return redirect('account:admin', request.user.username)
    else:
        return HttpResponse("You Are Not allowed!")
    return render(request, 'account/orgdetail.html', {'form':form, 'org':org,'user':request.user.email})


@login_required
def approveStatus(request, org_id):
    if request.user.is_superuser:
        try:
            org=Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return HttpResponse('Organization does not exist.')
        if org.status!='approved':
            org.status='approved'
            org.save()
            return redirect('account:admin', request.user.username)
        # Handle non-POST or already approved
        return HttpResponse(f'organization already {org.status}.')
    else:
        return HttpResponse('Only admins are allowed.')
    

@login_required
def rejectStatus(request, org_id):
    if request.user.is_superuser:
        try:
            org=Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return HttpResponse('Organization does not exist.')
        if org.status!='rejected':
            org.status='rejected'
            org.save()
            return redirect('account:admin', request.user.username)
        # Handle non-POST or already approved
        return HttpResponse(f'Your organization request is {org.status}.')
    else:
        return HttpResponse('Only admins are allowed.')

    
@login_required
def admin(request, admin_name):
    if request.user.is_superuser:
        org=Organization.objects.all().exclude(name=admin_name)
        total_orgs=org.count()
        approved_org=Organization.objects.filter(status='approved')
        total_approved_org=Organization.objects.filter(status='approved').count()
        rejected_org=Organization.objects.filter(status='rejected')
        
        total_clients=Clients.objects.all()
    else:
        return HttpResponse('You are not an admin.')
    
    return render(request, 'account/admin.html', {'admin_name':admin_name, 'org':org, 'approved_org':approved_org, 'total_orgs':total_orgs, 'total_approved_org':total_approved_org, 'total_clients':total_clients})


def adminSetup(request):
    if request.method!='POST':
        form = AdminSetupForm()    
    else:
        form=AdminSetupForm(request.POST)
        if form.is_valid():
            admin=User.objects.create_superuser(username=form.cleaned_data['username'],
                                                password=form.cleaned_data['password'],
                                                email=form.cleaned_data['email'])
            # org=Organization.objects.create(name=admin.username,
            #                                 location='Maymar',
            #                                 url='https://paperx.com',
            #                                 adminEmail=admin.email,
            #                                 user=admin,
            #                                 status='approved')
            # 'create_superuser' and 'create' already save the objects to the database, so calling .save() again is redundant (though harmless).
            return redirect('account:admin', admin.username)
    return render(request, 'account/adminSetup.html', {'form':form})
    
    

@login_required
def addClients(request):
    user_admin = request.user.is_superuser
    user=request.user.email
    org_exist=Organization.objects.filter(adminEmail=user).exists()
    org=Organization.objects.filter(adminEmail=user).first()

    if user_admin or org_exist:
        if request.method!='POST':
            if org_exist:
                form=ClientRegistrationForm(org=org, user=request.user)
            else:
                form=ClientRegistrationForm(user=request.user)
        else:
            if org_exist:
                form=ClientRegistrationForm(request.POST, user=request.user, org=org)
            else: # admin here
                form=ClientRegistrationForm(request.POST, user=request.user)
            if form.is_valid():
                form.save()
                if org_exist:
                    return redirect('account:dashboard', org.id )
                else:
                    return redirect('account:admin', request.user.username)
    else:
        return HttpResponse('You are a client. You do not have permission to view this.')
    return render(request, 'account/addclients.html', {'form':form})


@login_required
def editClients(request, cli_email):
    user_admin = request.user.is_superuser
    org=None
    
    try:
        cli=Clients.objects.get(email=cli_email)
    except Clients.DoesNotExist:
        return HttpResponse('This client has been deleted and no longer exists.')

    if not user_admin:
        try:
            org = Organization.objects.get(user=request.user)
            if cli.organization.adminEmail != org.adminEmail:
                return HttpResponse("You do not have permission to edit this clients")
        except Organization.DoesNotExist:
            return HttpResponse("You do not have permission to edit clients.")
        
    
    if request.method != 'POST':
        form=ClientRegistrationForm(instance=cli, user=request.user)
    else:
        form=ClientRegistrationForm(request.POST, instance=cli, user=request.user, org=org)
        if form.is_valid():
            form.save()
            if user_admin:
                return redirect('account:admin', request.user.username)
            else:
                return redirect('account:dashboard', org.id)
    return render(request, 'account/editclients.html', {'form':form, 'org': org, 'cli':cli })


from django.contrib import messages
@login_required
def sendChat(request):
    previous_url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        form = ChatForm(request.POST, user=request.user)
        if form.is_valid():

            heading = form.cleaned_data['Heading']
            description = form.cleaned_data['Description']
            recipients = form.cleaned_data['To']  # Could be multiple users

            chat = ChatHistory.objects.create(
                sender=request.user,
                heading=heading,
                description=description
            )
            chat.recipients.set(recipients)  # ManyToMany assignment
            chat.save()
            messages.success(request,'Message sent successfully.')

    else:
        form = ChatForm(user=request.user)

    return render(request, 'account/sendChat.html', {'form': form, 'back_url': previous_url})


from collections import defaultdict
@login_required
def clientDashboard(request, cli_email):
    user=request.user
    client=Clients.objects.filter(email=cli_email).first()
    messages = ChatHistory.objects.filter(recipients=user).order_by('timestamp')

    grouped = defaultdict(list) # automatically add an empty list under a key if it doesn't exist yet.
    for msg in messages:
        grouped[msg.sender].append(msg)
        # grouped['Mumtaz'].append('Hi') 
        # grouped = {'Mumtaz':['Hi','Hello', 'etc']}
    if client:
        org=client.organization
    if client.email != user.email:
        return HttpResponse('Not authorised to view another client profile')
    else:
        return render(request, 'account/clientDashboard.html', {'client':client, 'org':org, 'user':user, 'grouped_messages': grouped.items()})
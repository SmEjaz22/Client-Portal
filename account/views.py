from django.shortcuts import render, redirect

# Create your views here.
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from .models import Organization 
from .forms import RegistrationForm, LoginForm, AdminSetupForm

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
            user_exists=User.objects.filter(Q(username=cd.get('adminEmail')) | Q(email=cd.get('adminEmail'))).exists()
            
            if not org_exists and not user_exists:
                return HttpResponse('Organization and/or User Does not exist!')
            elif user.is_superuser:
                login(request, user)
                return redirect('account:admin', user.username) #  Idher masla hai
            else:
                org=Organization.objects.get(adminEmail=cd.get('adminEmail'))

                # to use in statusView().
                request.session['pending_status_email'] = org.adminEmail
                if user is not None:
                    if org.status=='approved':
                        if user.is_active:
                            login(request,user)
                            request.session.pop('pending_status_email', None)
                            # This technique is super handy whenever you want to allow access to something before login, without creating real accounts, or without storing temporary users.  Why it’s secure: A user cannot change their session data from the frontend — it’s stored securely on the server.
                            if request.user.is_superuser:
                                return redirect('account:admin', user.username)
                            else:
                                return redirect('account:dashboard', org_id=org.id)
                        else:
                            return HttpResponse("Disabled account!")
                    else:
                        if user.username == org.adminEmail:
                            return redirect('account:status', org_id=org.id)
                        else:
                            return HttpResponse('<h1>You are only allowed to access your own status. If you think this is a mistake. Contact support!</h1>')

                else:
                    return HttpResponse("Invalid Login!")
    return render(request, 'account/login.html', {'form':form})


def registrationView(request):
    if request.method!='POST':
        form=RegistrationForm()
    else:
        form=RegistrationForm(request.POST)
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
    user=request.user.username
    org=Organization.objects.get(id=org_id)
    if user==org.adminEmail:
        return render(request, 'account/userDashboard.html', {'org':org})    
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
            form=RegistrationForm(instance=org)
        else:
            form=RegistrationForm(request.POST, instance=org)
            if form.is_valid():
                form.save()
                return redirect('account:admin', request.user.username)
    else:
        return HttpResponse("You Are Not allowed!")
    return render(request, 'account/orgdetail.html', {'form':form, 'org':org,'user':request.user.email})


@login_required
def approvedStatus(request, org_id):
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
def admin(request, admin_name):
    org=Organization.objects.all().exclude(name=admin_name)
    total_orgs=org.count()
    approved_org=Organization.objects.filter(status='approved')
    total_approved_org=Organization.objects.filter(status='approved').count()
    rejected_org=Organization.objects.filter(status='rejected')
    
    return render(request, 'account/admin.html', {'admin_name':admin_name, 'org':org, 'approved_org':approved_org, 'total_orgs':total_orgs, 'total_approved_org':total_approved_org})


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
    
    

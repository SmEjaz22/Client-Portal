from django.urls import path, include, reverse_lazy
from . import views

app_name='account'

urlpatterns = [
    
    path('login/', views.loginView, name='login'),
    path('register/', views.orgregistrationView, name='register'),
    path('status/<int:org_id>', views.statusView, name='status'),
    path('dashboard/<int:org_id>', views.userDashboard, name='dashboard'),
    # path('dashboard/org/<int:org_id>/', views.userDashboard, name='dashboard_by_org'),
    # path('dashboard/client/<int:cli_id>/', views.userDashboard, name='dashboard_by_client'),
    path('organization-detail/<int:org_id>', views.orgDetail, name='orgdetail'),
    path('approve-status/<int:org_id>', views.approveStatus, name='approveStatus'),
    path('reject-status/<int:org_id>', views.rejectStatus, name='rejectStatus'),
    path('admin/<str:admin_name>', views.admin, name='admin'),
    path('admin-setup/', views.adminSetup, name='adminSetup'),
    path('add-clients/', views.addClients, name='addClients'),
    path('edit-clients/<str:cli_email>', views.editClients, name='editClients'),
    path('send-chat/', views.sendChat, name='sendChat'),
    path('dashboard/<str:cli_email>', views.clientDashboard, name='clientDashboard'),

    # Built-in urls for registration views.
    path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('', include('django.contrib.auth.urls')),
]

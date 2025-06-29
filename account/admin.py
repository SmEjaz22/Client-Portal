from django.contrib import admin

# Register your models here.
from .models import Organization, Clients, ChatHistory

admin.site.register(Organization)
admin.site.register(Clients)
admin.site.register(ChatHistory)
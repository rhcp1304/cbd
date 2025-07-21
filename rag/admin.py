from django.contrib import admin
from .models import GoogleSheetData # Import your new model

@admin.register(GoogleSheetData)
class GoogleSheetDataAdmin(admin.ModelAdmin):
    list_display = [field.name for field in GoogleSheetData._meta.fields]
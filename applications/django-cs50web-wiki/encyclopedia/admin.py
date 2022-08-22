from django.contrib import admin

from .models import Entry


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ['pk', 'slug', 'pub_date', 'upd_date']
    list_display_links = ['pk', 'slug']
    list_filter = ['entry_name']

    fields = ['pk', 'slug', 'entry_name', 'entry_text', 'pub_date', 'upd_date']

    def get_readonly_fields(self, request, obj=None):
        if obj: return ['pk', 'slug', 'upd_date']
        else: return ['pk', 'upd_date']

    def get_prepopulated_fields(self, request, obj=None):
        if obj: return super().get_prepopulated_fields(request, obj)
        else: return {'slug': ['entry_name']}

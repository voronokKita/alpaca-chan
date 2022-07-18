from django.contrib import admin

from .models import Entry


class EntryInline(admin.TabularInline):
    model = Entry
    extra = 3


class EntryAdmin(admin.ModelAdmin):
    list_display = ('entry_name', 'pub_date', 'upd_date')
    list_filter = ['entry_name']
    prepopulated_fields = {"slug": ("entry_name",)}


admin.site.register(Entry, EntryAdmin)

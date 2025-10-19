from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Building, Floor, Room, Tenant, Lease, RentPayment, 
    MeterReading, Invoice, InvoiceItem, Setting
)


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ['name', 'floor_count', 'room_count', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at']

    def floor_count(self, obj):
        return obj.floors.count()
    floor_count.short_description = 'Floors'

    def room_count(self, obj):
        return obj.rooms.count()
    room_count.short_description = 'Rooms'


@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ['building', 'floor_number', 'room_count', 'created_at']
    search_fields = ['building__name', 'floor_number']
    list_filter = ['building', 'created_at']
    readonly_fields = ['created_at', 'updated_at']

    def room_count(self, obj):
        return obj.rooms.count()
    room_count.short_description = 'Rooms'


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'building', 'floor', 'status', 'current_tenant', 'created_at']
    search_fields = ['room_number', 'building__name', 'notes']
    list_filter = ['building', 'floor', 'status', 'created_at']
    readonly_fields = ['created_at', 'updated_at', 'history']
    list_select_related = ['building', 'floor']

    def current_tenant(self, obj):
        active_lease = obj.leases.filter(status='active').first()
        if active_lease:
            url = reverse('admin:core_tenant_change', args=[active_lease.tenant.id])
            return format_html('<a href="{}">{}</a>', url, active_lease.tenant.full_name)
        return '-'
    current_tenant.short_description = 'Current Tenant'


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'email', 'active_lease', 'created_at']
    search_fields = ['full_name', 'phone', 'email']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at', 'history']

    def active_lease(self, obj):
        active_lease = obj.leases.filter(status='active').first()
        if active_lease:
            url = reverse('admin:core_lease_change', args=[active_lease.id])
            return format_html('<a href="{}">{}</a>', url, active_lease.room)
        return '-'
    active_lease.short_description = 'Active Lease'


@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'room', 'start_date', 'end_date', 'monthly_rent', 'status', 'created_at']
    search_fields = ['tenant__full_name', 'room__room_number', 'room__building__name']
    list_filter = ['status', 'start_date', 'created_at']
    readonly_fields = ['created_at', 'updated_at', 'history']
    list_select_related = ['tenant', 'room', 'room__building']

    fieldsets = (
        ('Basic Information', {
            'fields': ('tenant', 'room', 'start_date', 'end_date', 'status')
        }),
        ('Financial Details', {
            'fields': ('monthly_rent', 'deposit', 'billing_day')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('History', {
            'fields': ('history',),
            'classes': ('collapse',)
        }),
    )


@admin.register(RentPayment)
class RentPaymentAdmin(admin.ModelAdmin):
    list_display = ['lease', 'paid_on', 'amount', 'method', 'created_at']
    search_fields = ['lease__tenant__full_name', 'lease__room__room_number', 'method', 'notes']
    list_filter = ['paid_on', 'method', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    list_select_related = ['lease', 'lease__tenant', 'lease__room']

    fieldsets = (
        ('Payment Details', {
            'fields': ('lease', 'paid_on', 'amount', 'method', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MeterReading)
class MeterReadingAdmin(admin.ModelAdmin):
    list_display = ['room', 'reading_date', 'reading_value', 'created_at']
    search_fields = ['room__room_number', 'room__building__name']
    list_filter = ['reading_date', 'room__building', 'created_at']
    readonly_fields = ['created_at', 'updated_at', 'history']
    list_select_related = ['room', 'room__building']

    fieldsets = (
        ('Reading Details', {
            'fields': ('room', 'reading_date', 'reading_value')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('History', {
            'fields': ('history',),
            'classes': ('collapse',)
        }),
    )


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['room', 'month', 'type', 'total', 'pdf_url', 'created_at']
    search_fields = ['room__room_number', 'room__building__name']
    list_filter = ['type', 'month', 'created_at']
    readonly_fields = ['created_at', 'updated_at', 'history']
    list_select_related = ['room', 'room__building']
    inlines = [InvoiceItemInline]

    fieldsets = (
        ('Invoice Details', {
            'fields': ('room', 'month', 'type', 'subtotal', 'tax', 'total', 'pdf_url')
        }),
        ('Metadata', {
            'fields': ('meta',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('History', {
            'fields': ('history',),
            'classes': ('collapse',)
        }),
    )


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'label', 'qty', 'rate', 'amount', 'created_at']
    search_fields = ['invoice__room__room_number', 'label']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at']
    list_select_related = ['invoice', 'invoice__room']

    fieldsets = (
        ('Item Details', {
            'fields': ('invoice', 'label', 'qty', 'rate', 'amount')
        }),
        ('Metadata', {
            'fields': ('meta',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'created_at']
    search_fields = ['key', 'value']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Setting Details', {
            'fields': ('key', 'value')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['key']
        return self.readonly_fields


# Customize admin site
admin.site.site_header = "Rental Management System"
admin.site.site_title = "Rental Admin"
admin.site.index_title = "Welcome to Rental Management Administration"

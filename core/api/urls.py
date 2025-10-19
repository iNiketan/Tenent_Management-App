from django.urls import path
from . import api

urlpatterns = [
    # Buildings
    path('buildings/', api.building_list, name='building-list'),
    path('buildings/<int:pk>/', api.building_detail, name='building-detail'),
    
    # Floors
    path('floors/', api.floor_list, name='floor-list'),
    
    # Rooms
    path('rooms/', api.room_list, name='room-list'),
    path('rooms/<int:pk>/', api.room_detail, name='room-detail'),
    
    # Tenants
    path('tenants/', api.tenant_list, name='tenant-list'),
    path('tenants/<int:pk>/', api.tenant_detail, name='tenant-detail'),
    
    # Leases
    path('leases/', api.lease_list, name='lease-list'),
    path('leases/<int:pk>/', api.lease_detail, name='lease-detail'),
    
    # Rent Payments
    path('rent-payments/', api.rent_payment_list, name='rent-payment-list'),
    
    # Meter Readings
    path('meter/readings/', api.meter_reading_list, name='meter-reading-list'),
    path('meter/readings/bulk/', api.meter_reading_bulk, name='meter-reading-bulk'),
    
    # Billing
    path('billing/electricity/calc/', api.electricity_bill_calc, name='electricity-bill-calc'),
    
    # Invoices
    path('invoices/', api.invoice_list, name='invoice-list'),
    path('invoices/<int:pk>/', api.invoice_detail, name='invoice-detail'),
    path('invoices/electricity/', api.electricity_invoice_create, name='electricity-invoice-create'),
    path('invoices/rent/', api.rent_invoice_create, name='rent-invoice-create'),
    
    # Settings
    path('settings/', api.setting_list, name='setting-list'),
]

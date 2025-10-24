from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Main views
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('map/', views.map_view, name='map'),
    path('building/create/', views.create_building, name='create_building'),
    path('tenants/', views.tenants_view, name='tenants'),
    path('tenants/<int:tenant_id>/edit/', views.tenant_edit, name='tenant_edit'),
    path('leases/', views.leases_view, name='leases'),
    path('payments/', views.payments_view, name='payments'),
    path('meter/bulk/', views.meter_bulk_view, name='meter_bulk'),
    path('billing/', views.billing_view, name='billing'),
    path('settings/', views.settings_view, name='settings'),
    
    # Building details
    path('building/<int:building_id>/', views.building_details, name='building_details'),
    path('building/<int:building_id>/floor/<int:floor_index>/', views.building_floor_partial, name='building_floor_partial'),
    
    # Room details (full page)
    path('room/<int:room_id>/', views.room_details_page, name='room_details_page'),
    
    # HTMX partials
    path('rooms/<int:room_id>/drawer/', views.room_drawer, name='room_drawer'),
    path('room/<int:room_id>/panel/', views.room_panel, name='room_panel'),
    path('room/<int:room_id>/status/<str:new_status>/', views.update_room_status, name='update_room_status'),
    path('rooms/<int:room_id>/add-reading/', views.add_meter_reading, name='add_meter_reading'),
    path('leases/<int:lease_id>/record-payment/', views.record_rent_payment, name='record_rent_payment'),
    path('lease/<int:lease_id>/bill/create/', views.create_bill, name='create_bill'),
    path('invoice/<int:invoice_id>/status/<str:status>/', views.set_bill_status, name='set_bill_status'),
    path('rooms/<int:room_id>/compute-bill/', views.compute_electricity_bill, name='compute_electricity_bill'),
    path('rooms/<int:room_id>/generate-invoice/', views.generate_electricity_invoice, name='generate_electricity_invoice'),
    
    # Inline editing
    path('lease/<int:lease_id>/update-tenant/', views.update_lease_tenant, name='update_lease_tenant'),
    path('lease/<int:lease_id>/update-rent/', views.update_lease_rent, name='update_lease_rent'),
    path('room/<int:room_id>/update-payment/', views.update_payment_status, name='update_payment_status'),
    path('room/<int:room_id>/add-meter-reading/', views.add_meter_reading_inline, name='add_meter_reading_inline'),
    path('room/<int:room_id>/create-lease/', views.create_lease_for_room, name='create_lease_for_room'),
    
    # Reports
    path('reports/rent-collection/', views.reports_rent_collection, name='reports_rent_collection'),
    path('reports/electricity/', views.reports_electricity, name='reports_electricity'),
    
    # PDFs
    path('invoices/<int:invoice_id>/pdf/', views.invoice_pdf, name='invoice_pdf'),
]

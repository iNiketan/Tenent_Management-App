from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Count
from django.db import transaction
from django.utils import timezone
from datetime import date, datetime, timedelta
from decimal import Decimal
import json

from .models import (
    Building, Floor, Room, Tenant, Lease, RentPayment, 
    MeterReading, Invoice, InvoiceItem, Setting
)
from .billing.electricity import calc_month_bill, get_room_billing_summary
from .forms import (
    BuildingForm, FloorForm, RoomForm, TenantForm, LeaseForm, 
    RentPaymentForm, MeterReadingForm, SettingForm
)


# Helper Functions
def get_room_finance_snapshot(room):
    """
    Generate a finance snapshot for a room including:
    - Active lease info (tenant, rent, dates)
    - Bills summary (paid/unpaid months)
    - Last bill details
    - Badge status (OK / Due soon / Overdue / Vacant / Maintenance)
    
    OPTIMIZED: Uses prefetched data when available to avoid N+1 queries.
    """
    snapshot = {
        'room': room,
        'active_lease': None,
        'tenant_name': None,
        'rent': None,
        'lease_start': None,
        'lease_end': None,
        'months_paid': 0,
        'months_unpaid': 0,
        'last_invoice': None,
        'last_invoice_period': None,
        'last_invoice_status': None,
        'last_invoice_due_date': None,
        'last_invoice_elec_units': None,
        'last_invoice_elec_amount': None,
        'badge': 'Vacant',
        'badge_class': 'bg-gray-100 text-gray-700',
    }
    
    # Get active lease - use prefetched data if available
    if hasattr(room, 'active_leases_list'):
        active_lease = room.active_leases_list[0] if room.active_leases_list else None
    else:
        active_lease = room.leases.filter(status='active').select_related('tenant').first()
    
    if not active_lease:
        if room.status == 'maintenance':
            snapshot['badge'] = 'Maintenance'
            snapshot['badge_class'] = 'bg-yellow-100 text-yellow-700'
        return snapshot
    
    snapshot['active_lease'] = active_lease
    snapshot['tenant_name'] = active_lease.tenant.full_name
    snapshot['rent'] = active_lease.monthly_rent
    snapshot['lease_start'] = active_lease.start_date
    snapshot['lease_end'] = active_lease.end_date
    
    # Get recent invoices - use prefetched data if available
    if hasattr(room, 'current_invoices_list'):
        # For building list view, we only prefetch current month
        recent_invoices = room.current_invoices_list
    else:
        # Fallback for other views
        recent_invoices = Invoice.objects.filter(room=room).order_by('-month')[:6]
    
    # Simplified: just check the latest invoice for badge
    # (Full payment counting can be done on detail pages, not needed for grid view)
    last_invoice = recent_invoices[0] if recent_invoices else None
    
    if last_invoice:
        snapshot['last_invoice'] = last_invoice
        snapshot['last_invoice_period'] = last_invoice.month.strftime('%Y-%m')
        
        # Check if paid - simplified check
        payment_exists = RentPayment.objects.filter(
            lease=active_lease,
            paid_on__year=last_invoice.month.year,
            paid_on__month=last_invoice.month.month
        ).exists()
        
        snapshot['last_invoice_status'] = 'paid' if payment_exists else 'unpaid'
        
        # Calculate due date (assume 5 days after month start)
        from dateutil.relativedelta import relativedelta
        due_date = last_invoice.month + relativedelta(days=5)
        snapshot['last_invoice_due_date'] = due_date
        
        # Extract electricity info from meta
        if last_invoice.meta:
            snapshot['last_invoice_elec_units'] = last_invoice.meta.get('units')
            snapshot['last_invoice_elec_amount'] = last_invoice.meta.get('total')
        
        # Determine badge based on payment status and due date
        today = timezone.now().date()
        if payment_exists:
            snapshot['badge'] = 'OK'
            snapshot['badge_class'] = 'bg-green-100 text-green-700'
        elif today > due_date:
            snapshot['badge'] = 'Overdue'
            snapshot['badge_class'] = 'bg-red-100 text-red-700'
        elif today > due_date - timedelta(days=3):
            snapshot['badge'] = 'Due Soon'
            snapshot['badge_class'] = 'bg-orange-100 text-orange-700'
        else:
            snapshot['badge'] = 'OK'
            snapshot['badge_class'] = 'bg-green-100 text-green-700'
    else:
        # No invoices yet, but has active lease
        snapshot['badge'] = 'OK'
        snapshot['badge_class'] = 'bg-green-100 text-green-700'
    
    return snapshot


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    # KPIs
    total_rooms = Room.objects.count()
    occupied_rooms = Room.objects.filter(status='occupied').count()
    vacant_rooms = Room.objects.filter(status='vacant').count()
    maintenance_rooms = Room.objects.filter(status='maintenance').count()
    
    # Outstanding rent (simplified calculation)
    active_leases = Lease.objects.filter(status='active')
    total_monthly_rent = sum(lease.monthly_rent for lease in active_leases)
    
    # Recent payments (last 30 days)
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    recent_payments = RentPayment.objects.filter(paid_on__gte=thirty_days_ago)
    total_collections = sum(payment.amount for payment in recent_payments)
    
    # Monthly collections for chart (last 6 months)
    monthly_collections = []
    for i in range(6):
        month_start = timezone.now().date().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        month_payments = RentPayment.objects.filter(
            paid_on__gte=month_start,
            paid_on__lt=month_end
        )
        month_total = sum(payment.amount for payment in month_payments)
        monthly_collections.append({
            'month': month_start.strftime('%b %Y'),
            'amount': float(month_total)
        })
    
    monthly_collections.reverse()
    
    context = {
        'total_rooms': total_rooms,
        'occupied_rooms': occupied_rooms,
        'vacant_rooms': vacant_rooms,
        'maintenance_rooms': maintenance_rooms,
        'total_monthly_rent': total_monthly_rent,
        'total_collections': total_collections,
        'monthly_collections': monthly_collections,
    }
    
    return render(request, 'core/dashboard.html', context)


@login_required
def create_building(request):
    """
    View to create a building with floors and rooms in one go.
    """
    from core.forms import BuildingWithFloorsForm
    
    if request.method == 'POST':
        form = BuildingWithFloorsForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create building
                    building = Building.objects.create(
                        name=form.cleaned_data['building_name']
                    )
                    
                    num_floors = form.cleaned_data['num_floors']
                    rooms_per_floor = form.cleaned_data['rooms_per_floor']
                    room_prefix = form.cleaned_data.get('room_number_prefix', '')
                    
                    # Create floors and rooms
                    for floor_num in range(num_floors):
                        floor = Floor.objects.create(
                            building=building,
                            floor_number=floor_num
                        )
                        
                        # Create rooms for this floor
                        for room_num in range(1, rooms_per_floor + 1):
                            # Generate room number: floor_num + room_num (e.g., 101, 102, 201, 202)
                            if room_prefix:
                                room_number = f"{room_prefix}{floor_num}{room_num:02d}"
                            else:
                                room_number = f"{floor_num}{room_num:02d}"
                            
                            Room.objects.create(
                                building=building,
                                floor=floor,
                                room_number=room_number,
                                status='vacant'
                            )
                    
                    messages.success(
                        request,
                        f'Successfully created building "{building.name}" with {num_floors} floors '
                        f'and {num_floors * rooms_per_floor} rooms!'
                    )
                    return redirect('map')
                    
            except Exception as e:
                messages.error(request, f'Error creating building: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = BuildingWithFloorsForm()
    
    context = {
        'form': form,
    }
    return render(request, 'core/create_building.html', context)


@login_required
def map_view(request):
    buildings = Building.objects.all()
    floors = Floor.objects.all()
    rooms = Room.objects.all()
    
    # Get selected building and floor from query params
    selected_building = request.GET.get('building')
    selected_floor = request.GET.get('floor')
    
    if selected_building:
        rooms = rooms.filter(building_id=selected_building)
    if selected_floor:
        rooms = rooms.filter(floor_id=selected_floor)
    
    context = {
        'buildings': buildings,
        'floors': floors,
        'rooms': rooms,
        'selected_building': selected_building,
        'selected_floor': selected_floor,
    }
    
    return render(request, 'core/map.html', context)


@login_required
def room_drawer(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    active_lease = room.leases.filter(status='active').first()
    
    # Get recent meter readings
    recent_readings = room.meter_readings.order_by('-reading_date')[:2]
    
    # Get recent payments
    recent_payments = []
    if active_lease:
        recent_payments = active_lease.payments.order_by('-paid_on')[:5]
    
    context = {
        'room': room,
        'active_lease': active_lease,
        'recent_readings': recent_readings,
        'recent_payments': recent_payments,
    }
    
    return render(request, 'core/partials/room_drawer.html', context)


@login_required
def tenants_view(request):
    # OPTIMIZED: Prefetch active leases to avoid N+1 when displaying tenant list
    from django.db.models import Prefetch
    
    tenants = Tenant.objects.prefetch_related(
        Prefetch(
            'leases',
            queryset=Lease.objects.filter(status='active').select_related('room', 'room__building', 'room__floor'),
            to_attr='active_leases_list'
        )
    ).all()
    
    if request.method == 'POST':
        form = TenantForm(request.POST)
        if form.is_valid():
            # Save the tenant
            tenant = form.save()
            
            # If a room was selected, create a lease
            room = form.cleaned_data.get('room')
            if room:
                start_date = form.cleaned_data.get('start_date')
                monthly_rent = form.cleaned_data.get('monthly_rent')
                deposit = form.cleaned_data.get('deposit') or 0
                
                # Create the lease
                lease = Lease.objects.create(
                    tenant=tenant,
                    room=room,
                    start_date=start_date,
                    monthly_rent=monthly_rent,
                    deposit=deposit,
                    status='active'
                )
                messages.success(request, f'Tenant created and assigned to {room}. Room status updated to occupied.')
            else:
                messages.success(request, 'Tenant created successfully.')
            
            return redirect('tenants')
    else:
        form = TenantForm()
    
    context = {
        'tenants': tenants,
        'form': form,
    }
    
    return render(request, 'core/tenants.html', context)


@login_required
def tenant_edit(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    if request.method == 'POST':
        form = TenantForm(request.POST, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tenant updated successfully.')
            return redirect('tenants')
    else:
        form = TenantForm(instance=tenant)
    
    context = {
        'tenant': tenant,
        'form': form,
    }
    
    return render(request, 'core/tenant_edit.html', context)


@login_required
def leases_view(request):
    leases = Lease.objects.all()
    
    if request.method == 'POST':
        form = LeaseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lease created successfully.')
            return redirect('leases')
    else:
        form = LeaseForm()
    
    context = {
        'leases': leases,
        'form': form,
    }
    
    return render(request, 'core/leases.html', context)


@login_required
def payments_view(request):
    payments = RentPayment.objects.all()
    
    if request.method == 'POST':
        form = RentPaymentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment recorded successfully.')
            return redirect('payments')
    else:
        form = RentPaymentForm()
    
    context = {
        'payments': payments,
        'form': form,
    }
    
    return render(request, 'core/payments.html', context)


@login_required
def meter_bulk_view(request):
    rooms = Room.objects.all()
    current_month = timezone.now().date().replace(day=1)
    
    # Get readings for current month
    readings = {}
    for room in rooms:
        reading = room.meter_readings.filter(
            reading_date__gte=current_month,
            reading_date__lt=current_month + timedelta(days=32)
        ).order_by('-reading_date').first()
        readings[room.id] = reading
    
    context = {
        'rooms': rooms,
        'readings': readings,
        'current_month': current_month,
    }
    
    return render(request, 'core/meter_bulk.html', context)


@login_required
def billing_view(request):
    rooms = Room.objects.all()
    
    context = {
        'rooms': rooms,
    }
    
    return render(request, 'core/billing.html', context)


@login_required
def settings_view(request):
    settings = Setting.objects.all()
    
    if request.method == 'POST':
        form = SettingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully.')
            return redirect('settings')
    else:
        form = SettingForm()
    
    context = {
        'settings': settings,
        'form': form,
    }
    
    return render(request, 'core/settings.html', context)


# HTMX partial views
@login_required
@require_http_methods(["POST"])
def add_meter_reading(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        form = MeterReadingForm(request.POST)
        if form.is_valid():
            reading = form.save(commit=False)
            reading.room = room
            reading.save()
            messages.success(request, 'Meter reading added successfully.')
            return render(request, 'core/partials/meter_reading_form.html', {
                'room': room,
                'form': MeterReadingForm()
            })
    
    return render(request, 'core/partials/meter_reading_form.html', {
        'room': room,
        'form': MeterReadingForm()
    })


@login_required
@require_http_methods(["POST"])
def record_rent_payment(request, lease_id):
    lease = get_object_or_404(Lease, id=lease_id)
    
    if request.method == 'POST':
        form = RentPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.lease = lease
            payment.save()
            messages.success(request, 'Rent payment recorded successfully.')
            return render(request, 'core/partials/rent_payment_form.html', {
                'lease': lease,
                'form': RentPaymentForm()
            })
    
    return render(request, 'core/partials/rent_payment_form.html', {
        'lease': lease,
        'form': RentPaymentForm()
    })


@login_required
def compute_electricity_bill(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    month_str = request.GET.get('month', timezone.now().strftime('%Y-%m'))
    
    try:
        year, month = map(int, month_str.split('-'))
        bill_data = calc_month_bill(room_id, year, month)
        
        return render(request, 'core/partials/electricity_bill.html', {
            'room': room,
            'bill_data': bill_data,
            'month': month_str,
        })
    except ValueError as e:
        return render(request, 'core/partials/electricity_bill.html', {
            'room': room,
            'error': str(e),
            'month': month_str,
        })


@login_required
def generate_electricity_invoice(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    month_str = request.GET.get('month', timezone.now().strftime('%Y-%m'))
    
    try:
        year, month = map(int, month_str.split('-'))
        first_of_month = date(year, month, 1)
        
        # Check if invoice already exists
        existing_invoice = Invoice.objects.filter(
            room=room,
            month=first_of_month,
            type='electricity'
        ).first()
        
        if existing_invoice:
            return JsonResponse({
                'message': 'Invoice already exists',
                'invoice_id': existing_invoice.id
            })
        
        # Calculate bill
        bill_data = calc_month_bill(room_id, year, month)
        
        if 'error' in bill_data:
            return JsonResponse({'error': bill_data['error']}, status=400)
        
        # Create invoice
        invoice = Invoice.objects.create(
            room=room,
            month=first_of_month,
            type='electricity',
            subtotal=bill_data['total'],
            tax=Decimal('0'),
            total=bill_data['total'],
            meta={
                'previous_reading': float(bill_data['previous_reading']) if bill_data['previous_reading'] else None,
                'current_reading': float(bill_data['current_reading']) if bill_data['current_reading'] else None,
                'units': float(bill_data['units']),
                'rate': float(bill_data['rate'])
            }
        )
        
        # Create invoice item
        InvoiceItem.objects.create(
            invoice=invoice,
            label=f"Electricity ({month_str}): prev {bill_data['previous_reading'] or 'N/A'}, curr {bill_data['current_reading'] or 'N/A'}, units {bill_data['units']} @ ₹{bill_data['rate']}",
            qty=bill_data['units'],
            rate=bill_data['rate'],
            amount=bill_data['total']
        )
        
        return JsonResponse({
            'message': 'Invoice created successfully',
            'invoice_id': invoice.id
        })
        
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def invoice_pdf(request, invoice_id):
    """Download invoice PDF."""
    from .pdf.invoices import generate_invoice_pdf
    
    try:
        pdf_bytes = generate_invoice_pdf(invoice_id)
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_id}.pdf"'
        return response
        
    except ValueError as e:
        return HttpResponse(f"Error generating PDF: {str(e)}", status=400)


@login_required
def reports_rent_collection(request):
    month_str = request.GET.get('month', timezone.now().strftime('%Y-%m'))
    
    try:
        year, month = map(int, month_str.split('-'))
        first_of_month = date(year, month, 1)
        
        # Get rent payments for the month
        payments = RentPayment.objects.filter(
            paid_on__gte=first_of_month,
            paid_on__lt=first_of_month + timedelta(days=32)
        )
        
        total = sum(payment.amount for payment in payments)
        payment_count = payments.count()
        average = total / payment_count if payment_count > 0 else 0
        
        context = {
            'payments': payments,
            'month': month_str,
            'total': total,
            'average': average,
        }
        
        return render(request, 'core/reports/rent_collection.html', context)
    except ValueError:
        return render(request, 'core/reports/rent_collection.html', {
            'error': 'Invalid month format'
        })


@login_required
def reports_electricity(request):
    month_str = request.GET.get('month', timezone.now().strftime('%Y-%m'))
    
    try:
        year, month = map(int, month_str.split('-'))
        
        # Get electricity invoices for the month
        invoices = Invoice.objects.filter(
            month=date(year, month, 1),
            type='electricity'
        )
        
        total = sum(invoice.total for invoice in invoices)
        invoice_count = invoices.count()
        average = total / invoice_count if invoice_count > 0 else 0
        
        context = {
            'invoices': invoices,
            'month': month_str,
            'total': total,
            'average': average,
        }
        
        return render(request, 'core/reports/electricity.html', context)
    except ValueError:
        return render(request, 'core/reports/electricity.html', {
            'error': 'Invalid month format'
        })


# Building Details Views
@login_required
def building_details(request, building_id):
    """
    Building details page showing all rooms grid with finance snapshots.
    Optimized with prefetch_related to eliminate N+1 queries.
    """
    from django.db.models import Prefetch
    
    today = timezone.now().date()
    current_month = date(today.year, today.month, 1)
    
    # Single optimized query with all related data prefetched
    building = get_object_or_404(Building, id=building_id)
    floors = building.floors.all().order_by('floor_number')
    
    rooms = building.rooms.select_related('floor').prefetch_related(
        Prefetch(
            'leases',
            queryset=Lease.objects.filter(status='active').select_related('tenant'),
            to_attr='active_leases_list'
        ),
        Prefetch(
            'invoices',
            queryset=Invoice.objects.filter(month=current_month),
            to_attr='current_invoices_list'
        )
    ).order_by('floor__floor_number', 'room_number')
    
    # Generate finance snapshot for each room using prefetched data
    rooms_with_snapshot = []
    for room in rooms:
        snapshot = get_room_finance_snapshot(room)
        rooms_with_snapshot.append(snapshot)
    
    context = {
        'building': building,
        'floors': floors,
        'rooms_with_snapshot': rooms_with_snapshot,
    }
    
    return render(request, 'core/building_details.html', context)


@login_required
def building_floor_partial(request, building_id, floor_index):
    """
    Returns a table view for a specific floor in a building (HTMX partial).
    """
    building = get_object_or_404(Building, id=building_id)
    floor = get_object_or_404(Floor, building=building, floor_number=floor_index)
    rooms = floor.rooms.select_related('floor').order_by('room_number')
    
    # Generate finance snapshot for each room in this floor
    rooms_with_snapshot = []
    for room in rooms:
        snapshot = get_room_finance_snapshot(room)
        rooms_with_snapshot.append(snapshot)
    
    context = {
        'building': building,
        'floor': floor,
        'rooms_with_snapshot': rooms_with_snapshot,
    }
    
    return render(request, 'core/partials/floor_table.html', context)


@login_required
def room_details_page(request, room_id):
    """
    Full-page room details view with inline editing forms.
    """
    return room_panel(request, room_id, template='core/room_details.html')


@login_required
def room_panel(request, room_id, template='core/partials/room_panel.html'):
    """
    Returns the room details panel/drawer content (HTMX partial).
    Shows room status, active lease, bills list with inline editing.
    Auto-creates current month's bill if it doesn't exist.
    
    OPTIMIZED: Uses select_related/prefetch_related to minimize queries.
    """
    from django.db.models import Prefetch
    
    # Optimized query with all related data
    room = get_object_or_404(
        Room.objects.select_related(
            'building',
            'floor'
        ).prefetch_related(
            Prefetch(
                'leases',
                queryset=Lease.objects.filter(status='active').select_related('tenant'),
                to_attr='active_leases_list'
            ),
            'meter_readings'
        ),
        id=room_id
    )
    active_lease = room.active_leases_list[0] if room.active_leases_list else None
    
    # Get current month
    today = timezone.now().date()
    current_month = date(today.year, today.month, 1)
    
    # Auto-create current month's bill if active lease exists and bill doesn't exist
    current_month_invoice = None
    if active_lease:
        current_month_invoice, created = Invoice.objects.get_or_create(
            room=room,
            month=current_month,
            defaults={
                'type': 'rent',
                'subtotal': active_lease.monthly_rent,
                'tax': Decimal('0'),
                'total': active_lease.monthly_rent,
                'meta': {'rent': float(active_lease.monthly_rent)}
            }
        )
        
        # Create invoice item if newly created
        if created:
            InvoiceItem.objects.create(
                invoice=current_month_invoice,
                label=f"Rent for {current_month.strftime('%Y-%m')}",
                qty=Decimal('1'),
                rate=active_lease.monthly_rent,
                amount=active_lease.monthly_rent
            )
    
    # Get current month's payment status
    current_month_payment = None
    current_month_status = 'unpaid'
    amount_paid = Decimal('0')
    
    if active_lease and current_month_invoice:
        current_month_payment = RentPayment.objects.filter(
            lease=active_lease,
            paid_on__year=current_month.year,
            paid_on__month=current_month.month
        ).first()
        
        if current_month_payment:
            amount_paid = current_month_payment.amount
            if amount_paid >= current_month_invoice.total:
                current_month_status = 'paid'
            else:
                current_month_status = 'partial'
    
    # Get recent invoices (last 6)
    recent_invoices = []
    if active_lease:
        invoices = Invoice.objects.filter(room=room).order_by('-month')[:6]
        
        for invoice in invoices:
            # Check if paid
            payment = RentPayment.objects.filter(
                lease=active_lease,
                paid_on__year=invoice.month.year,
                paid_on__month=invoice.month.month
            ).first()
            
            # Calculate due date
            from dateutil.relativedelta import relativedelta
            due_date = invoice.month + relativedelta(days=5)
            
            recent_invoices.append({
                'invoice': invoice,
                'period': invoice.month.strftime('%Y-%m'),
                'total': invoice.total,
                'status': 'paid' if payment else 'unpaid',
                'payment': payment,
                'due_date': due_date,
                'elec_units': invoice.meta.get('units') if invoice.meta else None,
                'elec_amount': invoice.meta.get('total') if invoice.meta else None,
            })
    
    # Get meter readings (latest 2)
    latest_reading = room.meter_readings.order_by('-reading_date').first()
    previous_reading = room.meter_readings.order_by('-reading_date')[1] if room.meter_readings.count() > 1 else None
    
    units_used = None
    if latest_reading and previous_reading:
        units_used = latest_reading.reading_value - previous_reading.reading_value
    
    # Get all tenants for dropdown
    all_tenants = Tenant.objects.all().order_by('full_name')
    
    context = {
        'room': room,
        'active_lease': active_lease,
        'recent_invoices': recent_invoices,
        'current_month_invoice': current_month_invoice,
        'current_month_status': current_month_status,
        'current_month_payment': current_month_payment,
        'amount_paid': amount_paid,
        'latest_reading': latest_reading,
        'previous_reading': previous_reading,
        'units_used': units_used,
        'all_tenants': all_tenants,
        'current_month': current_month.strftime('%Y-%m'),
        'today': today.isoformat(),
    }
    
    return render(request, template, context)


@login_required
@require_http_methods(["POST"])
def update_room_status(request, room_id, new_status):
    """
    Update room status (occupied/vacant/maintenance).
    Returns updated room card partial via HTMX.
    """
    room = get_object_or_404(Room, id=room_id)
    
    if new_status not in ['occupied', 'vacant', 'maintenance']:
        return JsonResponse({'error': 'Invalid status'}, status=400)
    
    room.status = new_status
    room.save()
    
    # Generate updated snapshot
    snapshot = get_room_finance_snapshot(room)
    
    context = {
        'snapshot': snapshot,
    }
    
    # Return partial that updates both the card and the panel
    return render(request, 'core/partials/room_status_update.html', context)


@login_required
@require_http_methods(["POST"])
def create_bill(request, lease_id):
    """
    Create a new invoice/bill for a lease.
    POST fields: period (YYYY-MM), rent (int), due_date (date), 
                 optional elec_units (int), elec_amount (int)
    Returns updated bills list via HTMX.
    """
    lease = get_object_or_404(Lease, id=lease_id)
    
    try:
        # Parse form data
        period_str = request.POST.get('period')  # YYYY-MM format
        rent = Decimal(request.POST.get('rent', lease.monthly_rent))
        elec_units = request.POST.get('elec_units', '')
        elec_amount = request.POST.get('elec_amount', '0')
        
        # Parse period
        year, month = map(int, period_str.split('-'))
        first_of_month = date(year, month, 1)
        
        # Calculate total
        elec_amount_decimal = Decimal(elec_amount) if elec_amount else Decimal('0')
        total = rent + elec_amount_decimal
        
        # Check if invoice already exists
        existing_invoice = Invoice.objects.filter(
            room=lease.room,
            month=first_of_month
        ).first()
        
        if existing_invoice:
            messages.error(request, 'Invoice already exists for this period.')
        else:
            # Create invoice
            meta_data = {
                'rent': float(rent),
            }
            
            if elec_units:
                meta_data['units'] = float(elec_units)
            if elec_amount_decimal > 0:
                meta_data['elec_amount'] = float(elec_amount_decimal)
            
            invoice = Invoice.objects.create(
                room=lease.room,
                month=first_of_month,
                type='combined' if elec_amount_decimal > 0 else 'rent',
                subtotal=total,
                tax=Decimal('0'),
                total=total,
                meta=meta_data
            )
            
            # Create invoice items
            InvoiceItem.objects.create(
                invoice=invoice,
                label=f"Rent for {period_str}",
                qty=Decimal('1'),
                rate=rent,
                amount=rent
            )
            
            if elec_amount_decimal > 0:
                InvoiceItem.objects.create(
                    invoice=invoice,
                    label=f"Electricity for {period_str} ({elec_units} units)" if elec_units else f"Electricity for {period_str}",
                    qty=Decimal(elec_units) if elec_units else Decimal('1'),
                    rate=elec_amount_decimal if not elec_units else elec_amount_decimal / Decimal(elec_units),
                    amount=elec_amount_decimal
                )
            
            messages.success(request, 'Invoice created successfully.')
        
        # Return updated room panel
        return room_panel(request, lease.room.id)
        
    except (ValueError, KeyError) as e:
        messages.error(request, f'Error creating invoice: {str(e)}')
        return room_panel(request, lease.room.id)


@login_required
@require_http_methods(["POST"])
def set_bill_status(request, invoice_id, status):
    """
    Mark an invoice as paid/unpaid/partial.
    For 'paid', creates a RentPayment record.
    For 'unpaid', deletes associated RentPayment.
    Returns updated bills list via HTMX.
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)
    active_lease = invoice.room.leases.filter(status='active').first()
    
    if not active_lease:
        return JsonResponse({'error': 'No active lease found'}, status=400)
    
    if status == 'paid':
        # Create payment record if doesn't exist
        payment, created = RentPayment.objects.get_or_create(
            lease=active_lease,
            paid_on=invoice.month,
            defaults={
                'amount': invoice.total,
                'method': 'Cash',
                'notes': f'Payment for {invoice.month.strftime("%Y-%m")}'
            }
        )
        if created:
            messages.success(request, 'Invoice marked as paid.')
        else:
            messages.info(request, 'Invoice already marked as paid.')
            
    elif status == 'unpaid':
        # Delete payment records for this month
        deleted_count = RentPayment.objects.filter(
            lease=active_lease,
            paid_on__year=invoice.month.year,
            paid_on__month=invoice.month.month
        ).delete()[0]
        
        if deleted_count > 0:
            messages.success(request, 'Invoice marked as unpaid.')
        else:
            messages.info(request, 'Invoice was already unpaid.')
            
    elif status == 'partial':
        # For partial, create payment with half amount (simplified)
        payment, created = RentPayment.objects.get_or_create(
            lease=active_lease,
            paid_on=invoice.month,
            defaults={
                'amount': invoice.total / 2,
                'method': 'Partial',
                'notes': f'Partial payment for {invoice.month.strftime("%Y-%m")}'
            }
        )
        if created:
            messages.success(request, 'Invoice marked as partially paid.')
        else:
            messages.info(request, 'Payment record already exists.')
    
    # Return updated room panel
    return room_panel(request, invoice.room.id)


# Inline Editing Views for Room Drawer
@login_required
@require_http_methods(["POST"])
def update_lease_tenant(request, lease_id):
    """
    Update the tenant for a lease (inline editing).
    """
    lease = get_object_or_404(Lease, id=lease_id)
    tenant_id = request.POST.get('tenant_id')
    
    if tenant_id:
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            lease.tenant = tenant
            lease.save()
            messages.success(request, f'Tenant updated to {tenant.full_name}.')
        except Tenant.DoesNotExist:
            messages.error(request, 'Tenant not found.')
    
    return redirect('room_details_page', room_id=lease.room.id)


@login_required
@require_http_methods(["POST"])
def update_lease_rent(request, lease_id):
    """
    Update the monthly rent for a lease (inline editing).
    """
    lease = get_object_or_404(Lease, id=lease_id)
    rent = request.POST.get('rent')
    
    if rent:
        try:
            lease.monthly_rent = Decimal(rent)
            lease.save()
            messages.success(request, f'Rent updated to ₹{rent}.')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid rent amount.')
    
    return redirect('room_details_page', room_id=lease.room.id)


@login_required
@require_http_methods(["POST"])
def update_payment_status(request, room_id):
    """
    Update current month's payment status and amount (inline editing).
    Creates or updates RentPayment record.
    """
    room = get_object_or_404(Room, id=room_id)
    active_lease = room.leases.filter(status='active').first()
    
    if not active_lease:
        messages.error(request, 'No active lease found.')
        return room_panel(request, room_id)
    
    # Get current month
    today = timezone.now().date()
    current_month = date(today.year, today.month, 1)
    
    # Get or create current month's invoice
    current_month_invoice = Invoice.objects.filter(
        room=room,
        month=current_month
    ).first()
    
    if not current_month_invoice:
        messages.error(request, 'No invoice found for current month.')
        return room_panel(request, room_id)
    
    status = request.POST.get('status')
    amount = request.POST.get('amount', '0')
    
    try:
        amount_decimal = Decimal(amount)
        
        if status == 'paid':
            # Create or update payment with full amount
            payment, created = RentPayment.objects.update_or_create(
                lease=active_lease,
                paid_on=current_month,
                defaults={
                    'amount': current_month_invoice.total,
                    'method': 'Cash',
                    'notes': f'Payment for {current_month.strftime("%Y-%m")}'
                }
            )
            messages.success(request, 'Payment marked as Paid.')
            
        elif status == 'partial':
            # Create or update payment with specified amount
            if amount_decimal <= 0:
                messages.error(request, 'Please enter a valid amount for partial payment.')
                return room_panel(request, room_id)
                
            payment, created = RentPayment.objects.update_or_create(
                lease=active_lease,
                paid_on=current_month,
                defaults={
                    'amount': amount_decimal,
                    'method': 'Partial',
                    'notes': f'Partial payment for {current_month.strftime("%Y-%m")}'
                }
            )
            messages.success(request, f'Payment marked as Partial (₹{amount_decimal}).')
            
        elif status == 'unpaid':
            # Delete payment record
            RentPayment.objects.filter(
                lease=active_lease,
                paid_on__year=current_month.year,
                paid_on__month=current_month.month
            ).delete()
            messages.success(request, 'Payment marked as Unpaid.')
            
    except (ValueError, TypeError):
        messages.error(request, 'Invalid amount.')
    
    return redirect('room_details_page', room_id=room_id)


@login_required
@require_http_methods(["POST"])
def add_meter_reading_inline(request, room_id):
    """
    Add a new meter reading for a room (inline editing).
    """
    room = get_object_or_404(Room, id=room_id)
    
    reading_value = request.POST.get('reading_value')
    reading_date = request.POST.get('reading_date')
    
    if not reading_value or not reading_date:
        messages.error(request, 'Please provide both reading value and date.')
        return redirect('room_details_page', room_id=room_id)
    
    try:
        reading_value_decimal = Decimal(reading_value)
        reading_date_obj = datetime.strptime(reading_date, '%Y-%m-%d').date()
        
        # Check if reading already exists for this date
        existing = MeterReading.objects.filter(
            room=room,
            reading_date=reading_date_obj
        ).first()
        
        if existing:
            existing.reading_value = reading_value_decimal
            existing.save()
            messages.success(request, f'Meter reading updated: {reading_value} on {reading_date}.')
        else:
            MeterReading.objects.create(
                room=room,
                reading_value=reading_value_decimal,
                reading_date=reading_date_obj
            )
            messages.success(request, f'Meter reading added: {reading_value} on {reading_date}.')
        
    except (ValueError, TypeError) as e:
        messages.error(request, f'Invalid reading value or date: {str(e)}')
    
    return redirect('room_details_page', room_id=room_id)


@login_required
@require_http_methods(["POST"])
def create_lease_for_room(request, room_id):
    """
    Create a new lease for a vacant room (assign tenant to room).
    """
    room = get_object_or_404(Room, id=room_id)
    
    # Check if room already has an active lease
    if room.leases.filter(status='active').exists():
        messages.error(request, 'This room already has an active lease.')
        return redirect('room_details_page', room_id=room_id)
    
    tenant_id = request.POST.get('tenant_id')
    start_date_str = request.POST.get('start_date')
    monthly_rent = request.POST.get('monthly_rent')
    deposit = request.POST.get('deposit', '0')
    billing_day = request.POST.get('billing_day', '1')
    
    if not tenant_id or not start_date_str or not monthly_rent:
        messages.error(request, 'Please provide tenant, start date, and monthly rent.')
        return redirect('room_details_page', room_id=room_id)
    
    try:
        tenant = get_object_or_404(Tenant, id=tenant_id)
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        monthly_rent_decimal = Decimal(monthly_rent)
        deposit_decimal = Decimal(deposit) if deposit else Decimal('0')
        billing_day_int = int(billing_day) if billing_day else 1
        
        # Validate billing_day
        if billing_day_int < 1 or billing_day_int > 28:
            billing_day_int = 1
        
        # Create the lease
        lease = Lease.objects.create(
            tenant=tenant,
            room=room,
            start_date=start_date,
            monthly_rent=monthly_rent_decimal,
            deposit=deposit_decimal,
            billing_day=billing_day_int,
            status='active'
        )
        
        messages.success(request, f'Successfully assigned {tenant.full_name} to Room {room.room_number}. Room status updated to occupied.')
        
    except Tenant.DoesNotExist:
        messages.error(request, 'Tenant not found.')
    except (ValueError, TypeError) as e:
        messages.error(request, f'Invalid input: {str(e)}')
    except Exception as e:
        messages.error(request, f'Error creating lease: {str(e)}')
    
    return redirect('room_details_page', room_id=room_id)

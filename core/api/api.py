from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils.dateparse import parse_date
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
import json

from core.models import (
    Building, Floor, Room, Tenant, Lease, RentPayment, 
    MeterReading, Invoice, InvoiceItem, Setting
)
from core.billing.electricity import (
    calc_month_bill, validate_monotonic_readings, 
    get_room_billing_summary
)


# Serializers
class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'


class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = '__all__'


class RoomSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source='building.name', read_only=True)
    floor_number = serializers.IntegerField(source='floor.floor_number', read_only=True)
    current_tenant = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = '__all__'

    def get_current_tenant(self, obj):
        active_lease = obj.leases.filter(status='active').first()
        if active_lease:
            return {
                'id': active_lease.tenant.id,
                'name': active_lease.tenant.full_name,
                'lease_id': active_lease.id
            }
        return None


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = '__all__'


class LeaseSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.full_name', read_only=True)
    room_display = serializers.CharField(source='room', read_only=True)

    class Meta:
        model = Lease
        fields = '__all__'

    def validate(self, data):
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError("End date must be after start date.")
        return data


class RentPaymentSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='lease.tenant.full_name', read_only=True)
    room_display = serializers.CharField(source='lease.room', read_only=True)

    class Meta:
        model = RentPayment
        fields = '__all__'


class MeterReadingSerializer(serializers.ModelSerializer):
    room_display = serializers.CharField(source='room', read_only=True)

    class Meta:
        model = MeterReading
        fields = '__all__'

    def validate(self, data):
        room = data.get('room')
        reading_date = data.get('reading_date')
        reading_value = data.get('reading_value')

        if room and reading_date and reading_value is not None:
            if not validate_monotonic_readings(room.id, reading_date, reading_value):
                raise serializers.ValidationError(
                    "Reading value cannot be less than the previous reading for this room."
                )
        return data


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = '__all__'


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    room_display = serializers.CharField(source='room', read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = '__all__'


# API Views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def building_list(request):
    if request.method == 'GET':
        buildings = Building.objects.all()
        serializer = BuildingSerializer(buildings, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = BuildingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def building_detail(request, pk):
    building = get_object_or_404(Building, pk=pk)
    
    if request.method == 'GET':
        serializer = BuildingSerializer(building)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = BuildingSerializer(building, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        building.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def floor_list(request):
    if request.method == 'GET':
        floors = Floor.objects.all()
        serializer = FloorSerializer(floors, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = FloorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def room_list(request):
    if request.method == 'GET':
        rooms = Room.objects.all()
        
        # Filter by building
        building_id = request.query_params.get('building')
        if building_id:
            rooms = rooms.filter(building_id=building_id)
        
        # Filter by floor
        floor_id = request.query_params.get('floor')
        if floor_id:
            rooms = rooms.filter(floor_id=floor_id)
        
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = RoomSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def room_detail(request, pk):
    room = get_object_or_404(Room, pk=pk)
    
    if request.method == 'GET':
        serializer = RoomSerializer(room)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = RoomSerializer(room, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        room.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def tenant_list(request):
    if request.method == 'GET':
        tenants = Tenant.objects.all()
        serializer = TenantSerializer(tenants, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = TenantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def tenant_detail(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    
    if request.method == 'GET':
        serializer = TenantSerializer(tenant)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = TenantSerializer(tenant, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        tenant.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def lease_list(request):
    if request.method == 'GET':
        leases = Lease.objects.all()
        serializer = LeaseSerializer(leases, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = LeaseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def lease_detail(request, pk):
    lease = get_object_or_404(Lease, pk=pk)
    
    if request.method == 'GET':
        serializer = LeaseSerializer(lease)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = LeaseSerializer(lease, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        lease.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def rent_payment_list(request):
    if request.method == 'GET':
        payments = RentPayment.objects.all()
        serializer = RentPaymentSerializer(payments, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = RentPaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def meter_reading_list(request):
    if request.method == 'GET':
        readings = MeterReading.objects.all()
        
        # Filter by room
        room_id = request.query_params.get('room_id')
        if room_id:
            readings = readings.filter(room_id=room_id)
        
        # Filter by year and month
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        if year and month:
            try:
                year = int(year)
                month = int(month)
                first_of_month = date(year, month, 1)
                if month == 12:
                    first_of_next_month = date(year + 1, 1, 1)
                else:
                    first_of_next_month = date(year, month + 1, 1)
                readings = readings.filter(
                    reading_date__gte=first_of_month,
                    reading_date__lt=first_of_next_month
                )
            except (ValueError, TypeError):
                pass
        
        serializer = MeterReadingSerializer(readings, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = MeterReadingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def meter_reading_bulk(request):
    """Bulk create meter readings with validation."""
    data = request.data
    
    if not isinstance(data, list):
        return Response(
            {'error': 'Expected a list of readings'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    errors = []
    created_readings = []
    
    with transaction.atomic():
        for i, reading_data in enumerate(data):
            serializer = MeterReadingSerializer(data=reading_data)
            if serializer.is_valid():
                try:
                    reading = serializer.save()
                    created_readings.append(reading)
                except Exception as e:
                    errors.append({
                        'index': i,
                        'error': str(e),
                        'data': reading_data
                    })
            else:
                errors.append({
                    'index': i,
                    'error': serializer.errors,
                    'data': reading_data
                })
    
    if errors:
        return Response({
            'created': len(created_readings),
            'errors': errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'created': len(created_readings),
        'readings': MeterReadingSerializer(created_readings, many=True).data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def electricity_bill_calc(request):
    """Calculate electricity bill for a room and month."""
    room_id = request.data.get('room_id')
    month_str = request.data.get('month')  # Format: "YYYY-MM"
    
    if not room_id or not month_str:
        return Response(
            {'error': 'room_id and month are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        year, month = map(int, month_str.split('-'))
        result = calc_month_bill(room_id, year, month)
        return Response(result)
    except ValueError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def electricity_invoice_create(request):
    """Create electricity invoice for a room and month."""
    room_id = request.data.get('room_id')
    month_str = request.data.get('month')  # Format: "YYYY-MM"
    
    if not room_id or not month_str:
        return Response(
            {'error': 'room_id and month are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        year, month = map(int, month_str.split('-'))
        first_of_month = date(year, month, 1)
        
        # Check if invoice already exists
        existing_invoice = Invoice.objects.filter(
            room_id=room_id,
            month=first_of_month,
            type='electricity'
        ).first()
        
        if existing_invoice:
            return Response({
                'message': 'Invoice already exists',
                'invoice': InvoiceSerializer(existing_invoice).data
            })
        
        # Calculate bill
        bill_data = calc_month_bill(room_id, year, month)
        
        if 'error' in bill_data:
            return Response(
                {'error': bill_data['error']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create invoice
        with transaction.atomic():
            invoice = Invoice.objects.create(
                room_id=room_id,
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
        
        return Response({
            'message': 'Invoice created successfully',
            'invoice': InvoiceSerializer(invoice).data
        }, status=status.HTTP_201_CREATED)
        
    except ValueError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rent_invoice_create(request):
    """Create rent invoice for a lease and month."""
    lease_id = request.data.get('lease_id')
    month_str = request.data.get('month')  # Format: "YYYY-MM"
    
    if not lease_id or not month_str:
        return Response(
            {'error': 'lease_id and month are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        lease = get_object_or_404(Lease, id=lease_id)
        year, month = map(int, month_str.split('-'))
        first_of_month = date(year, month, 1)
        
        # Check if invoice already exists
        existing_invoice = Invoice.objects.filter(
            room=lease.room,
            month=first_of_month,
            type='rent'
        ).first()
        
        if existing_invoice:
            return Response({
                'message': 'Invoice already exists',
                'invoice': InvoiceSerializer(existing_invoice).data
            })
        
        # Create invoice
        with transaction.atomic():
            invoice = Invoice.objects.create(
                room=lease.room,
                month=first_of_month,
                type='rent',
                subtotal=lease.monthly_rent,
                tax=Decimal('0'),
                total=lease.monthly_rent,
                meta={
                    'lease_id': lease.id,
                    'tenant_id': lease.tenant.id
                }
            )
            
            # Create invoice item
            InvoiceItem.objects.create(
                invoice=invoice,
                label=f"Rent for {month_str}",
                qty=Decimal('1'),
                rate=lease.monthly_rent,
                amount=lease.monthly_rent
            )
        
        return Response({
            'message': 'Invoice created successfully',
            'invoice': InvoiceSerializer(invoice).data
        }, status=status.HTTP_201_CREATED)
        
    except ValueError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def invoice_list(request):
    """List invoices with optional filters."""
    invoices = Invoice.objects.all()
    
    # Filter by room
    room_id = request.query_params.get('room_id')
    if room_id:
        invoices = invoices.filter(room_id=room_id)
    
    # Filter by month
    month = request.query_params.get('month')
    if month:
        try:
            year, month_num = map(int, month.split('-'))
            first_of_month = date(year, month_num, 1)
            invoices = invoices.filter(month=first_of_month)
        except (ValueError, TypeError):
            pass
    
    # Filter by type
    invoice_type = request.query_params.get('type')
    if invoice_type:
        invoices = invoices.filter(type=invoice_type)
    
    serializer = InvoiceSerializer(invoices, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def invoice_detail(request, pk):
    """Get invoice details."""
    invoice = get_object_or_404(Invoice, pk=pk)
    serializer = InvoiceSerializer(invoice)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def setting_list(request):
    """List or update settings."""
    if request.method == 'GET':
        settings = Setting.objects.all()
        serializer = SettingSerializer(settings, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        key = request.data.get('key')
        value = request.data.get('value')
        
        if not key:
            return Response(
                {'error': 'key is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        setting, created = Setting.objects.get_or_create(key=key)
        setting.value = str(value) if value is not None else ''
        setting.save()
        
        serializer = SettingSerializer(setting)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

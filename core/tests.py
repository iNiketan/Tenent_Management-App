import pytest
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, datetime
import json

from core.models import (
    Building, Floor, Room, Tenant, Lease, RentPayment, 
    MeterReading, Invoice, InvoiceItem, Setting
)
from core.billing.electricity import (
    get_rate, compute_units, compute_bill, get_month_readings,
    calc_month_bill, validate_monotonic_readings
)


class ElectricityBillingTests(TestCase):
    """Test electricity billing calculations."""
    
    def setUp(self):
        self.building = Building.objects.create(name="Test Building")
        self.floor = Floor.objects.create(building=self.building, floor_number=1)
        self.room = Room.objects.create(
            building=self.building, 
            floor=self.floor, 
            room_number="101"
        )
        
        # Set electricity rate
        Setting.objects.create(key='electricity_rate_per_unit', value='10.50')
    
    def test_get_rate(self):
        """Test getting electricity rate from settings."""
        rate = get_rate()
        self.assertEqual(rate, Decimal('10.50'))
    
    def test_get_rate_default(self):
        """Test getting default rate when setting doesn't exist."""
        Setting.objects.filter(key='electricity_rate_per_unit').delete()
        rate = get_rate()
        self.assertEqual(rate, Decimal('0'))
    
    def test_compute_units_no_previous(self):
        """Test computing units when there's no previous reading."""
        units = compute_units(None, Decimal('100'))
        self.assertEqual(units, Decimal('0'))
    
    def test_compute_units_normal(self):
        """Test computing units with normal readings."""
        units = compute_units(Decimal('100'), Decimal('150'))
        self.assertEqual(units, Decimal('50'))
    
    def test_compute_units_negative_delta(self):
        """Test computing units with negative delta raises error."""
        with self.assertRaises(ValueError):
            compute_units(Decimal('150'), Decimal('100'))
    
    def test_compute_bill_no_previous(self):
        """Test computing bill with no previous reading."""
        bill = compute_bill(None, Decimal('100'), Decimal('10'))
        self.assertEqual(bill['units'], Decimal('0'))
        self.assertEqual(bill['total'], Decimal('0'))
    
    def test_compute_bill_normal(self):
        """Test computing bill with normal readings."""
        bill = compute_bill(Decimal('100'), Decimal('150'), Decimal('10'))
        self.assertEqual(bill['units'], Decimal('50'))
        self.assertEqual(bill['rate'], Decimal('10'))
        self.assertEqual(bill['total'], Decimal('500'))
    
    def test_get_month_readings(self):
        """Test getting month readings."""
        # Create readings
        MeterReading.objects.create(
            room=self.room,
            reading_date=date(2024, 1, 15),
            reading_value=Decimal('100')
        )
        MeterReading.objects.create(
            room=self.room,
            reading_date=date(2024, 2, 15),
            reading_value=Decimal('150')
        )
        
        previous, current = get_month_readings(self.room.id, 2024, 2)
        self.assertEqual(previous, Decimal('100'))
        self.assertEqual(current, Decimal('150'))
    
    def test_calc_month_bill(self):
        """Test calculating month bill."""
        # Create readings
        MeterReading.objects.create(
            room=self.room,
            reading_date=date(2024, 1, 15),
            reading_value=Decimal('100')
        )
        MeterReading.objects.create(
            room=self.room,
            reading_date=date(2024, 2, 15),
            reading_value=Decimal('150')
        )
        
        bill = calc_month_bill(self.room.id, 2024, 2)
        self.assertEqual(bill['units'], Decimal('50'))
        self.assertEqual(bill['total'], Decimal('525'))  # 50 * 10.50
    
    def test_validate_monotonic_readings(self):
        """Test validating monotonic readings."""
        # Create previous reading
        MeterReading.objects.create(
            room=self.room,
            reading_date=date(2024, 1, 15),
            reading_value=Decimal('100')
        )
        
        # Valid reading
        self.assertTrue(validate_monotonic_readings(
            self.room.id, date(2024, 2, 15), Decimal('150')
        ))
        
        # Invalid reading (less than previous)
        self.assertFalse(validate_monotonic_readings(
            self.room.id, date(2024, 2, 15), Decimal('50')
        ))


class APITests(APITestCase):
    """Test API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.force_authenticate(user=self.user)
        
        self.building = Building.objects.create(name="Test Building")
        self.floor = Floor.objects.create(building=self.building, floor_number=1)
        self.room = Room.objects.create(
            building=self.building, 
            floor=self.floor, 
            room_number="101"
        )
        self.tenant = Tenant.objects.create(
            full_name="Test Tenant",
            phone="1234567890",
            email="test@example.com"
        )
        self.lease = Lease.objects.create(
            tenant=self.tenant,
            room=self.room,
            start_date=date(2024, 1, 1),
            monthly_rent=Decimal('5000'),
            billing_day=1
        )
    
    def test_room_list(self):
        """Test room list API."""
        url = reverse('room-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_room_list_filter(self):
        """Test room list with filters."""
        url = reverse('room-list')
        response = self.client.get(url, {'building': self.building.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_meter_reading_create(self):
        """Test creating meter reading."""
        url = reverse('meter-reading-list')
        data = {
            'room': self.room.id,
            'reading_date': '2024-02-15',
            'reading_value': '150.00'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MeterReading.objects.count(), 1)
    
    def test_meter_reading_bulk(self):
        """Test bulk meter reading creation."""
        url = reverse('meter-reading-bulk')
        data = [
            {
                'room': self.room.id,
                'reading_date': '2024-01-15',
                'reading_value': '100.00'
            },
            {
                'room': self.room.id,
                'reading_date': '2024-02-15',
                'reading_value': '150.00'
            }
        ]
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MeterReading.objects.count(), 2)
    
    def test_electricity_bill_calc(self):
        """Test electricity bill calculation."""
        # Create readings
        MeterReading.objects.create(
            room=self.room,
            reading_date=date(2024, 1, 15),
            reading_value=Decimal('100')
        )
        MeterReading.objects.create(
            room=self.room,
            reading_date=date(2024, 2, 15),
            reading_value=Decimal('150')
        )
        
        # Set rate
        Setting.objects.create(key='electricity_rate_per_unit', value='10.50')
        
        url = reverse('electricity-bill-calc')
        data = {
            'room_id': self.room.id,
            'month': '2024-02'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['units'], Decimal('50'))
        self.assertEqual(response.data['total'], Decimal('525'))
    
    def test_electricity_invoice_create(self):
        """Test creating electricity invoice."""
        # Create readings
        MeterReading.objects.create(
            room=self.room,
            reading_date=date(2024, 1, 15),
            reading_value=Decimal('100')
        )
        MeterReading.objects.create(
            room=self.room,
            reading_date=date(2024, 2, 15),
            reading_value=Decimal('150')
        )
        
        # Set rate
        Setting.objects.create(key='electricity_rate_per_unit', value='10.50')
        
        url = reverse('electricity-invoice-create')
        data = {
            'room_id': self.room.id,
            'month': '2024-02'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Invoice.objects.count(), 1)
        self.assertEqual(InvoiceItem.objects.count(), 1)


class ViewTests(TestCase):
    """Test HTMX views."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.force_login(self.user)
        
        self.building = Building.objects.create(name="Test Building")
        self.floor = Floor.objects.create(building=self.building, floor_number=1)
        self.room = Room.objects.create(
            building=self.building, 
            floor=self.floor, 
            room_number="101"
        )
    
    def test_dashboard_view(self):
        """Test dashboard view."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
    
    def test_map_view(self):
        """Test map view."""
        response = self.client.get(reverse('map'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Room Map')
    
    def test_room_drawer(self):
        """Test room drawer HTMX view."""
        response = self.client.get(reverse('room_drawer', args=[self.room.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.room.room_number)
    
    def test_settings_view(self):
        """Test settings view."""
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Settings')


class ModelTests(TestCase):
    """Test model functionality."""
    
    def setUp(self):
        self.building = Building.objects.create(name="Test Building")
        self.floor = Floor.objects.create(building=self.building, floor_number=1)
        self.room = Room.objects.create(
            building=self.building, 
            floor=self.floor, 
            room_number="101"
        )
        self.tenant = Tenant.objects.create(
            full_name="Test Tenant",
            phone="1234567890",
            email="test@example.com"
        )
    
    def test_room_str(self):
        """Test room string representation."""
        self.assertEqual(str(self.room), "Test Building - Floor 1 - Room 101")
    
    def test_lease_room_status_update(self):
        """Test that lease creation updates room status."""
        # Room should be vacant initially
        self.assertEqual(self.room.status, 'vacant')
        
        # Create active lease
        lease = Lease.objects.create(
            tenant=self.tenant,
            room=self.room,
            start_date=date(2024, 1, 1),
            monthly_rent=Decimal('5000')
        )
        
        # Room should now be occupied
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, 'occupied')
        
        # End lease
        lease.status = 'ended'
        lease.save()
        
        # Room should be vacant again
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, 'vacant')
    
    def test_setting_get_set_value(self):
        """Test setting get and set value methods."""
        # Set value
        Setting.set_value('test_key', 'test_value')
        
        # Get value
        value = Setting.get_value('test_key')
        self.assertEqual(value, 'test_value')
        
        # Get default value
        default_value = Setting.get_value('nonexistent_key', 'default')
        self.assertEqual(default_value, 'default')
    
    def test_meter_reading_unique_constraint(self):
        """Test meter reading unique constraint."""
        MeterReading.objects.create(
            room=self.room,
            reading_date=date(2024, 1, 15),
            reading_value=Decimal('100')
        )
        
        # Should raise IntegrityError for duplicate
        with self.assertRaises(Exception):
            MeterReading.objects.create(
                room=self.room,
                reading_date=date(2024, 1, 15),
                reading_value=Decimal('150')
            )

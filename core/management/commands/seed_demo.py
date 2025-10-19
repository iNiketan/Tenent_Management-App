from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, timedelta
import random

from core.models import (
    Building, Floor, Room, Tenant, Lease, RentPayment, 
    MeterReading, Invoice, InvoiceItem, Setting
)


class Command(BaseCommand):
    help = 'Seed the database with demo data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()

        self.stdout.write('Creating demo data...')
        
        # Create superuser if it doesn't exist
        self.create_superuser()
        
        # Create buildings and floors
        buildings = self.create_buildings()
        
        # Create rooms
        rooms = self.create_rooms(buildings)
        
        # Create tenants
        tenants = self.create_tenants()
        
        # Create leases
        leases = self.create_leases(tenants, rooms)
        
        # Create meter readings
        self.create_meter_readings(rooms)
        
        # Create rent payments
        self.create_rent_payments(leases)
        
        # Create settings
        self.create_settings()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created demo data!')
        )

    def clear_data(self):
        """Clear existing data."""
        InvoiceItem.objects.all().delete()
        Invoice.objects.all().delete()
        RentPayment.objects.all().delete()
        MeterReading.objects.all().delete()
        Lease.objects.all().delete()
        Tenant.objects.all().delete()
        Room.objects.all().delete()
        Floor.objects.all().delete()
        Building.objects.all().delete()
        Setting.objects.all().delete()

    def create_superuser(self):
        """Create superuser if it doesn't exist."""
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write('Created superuser: admin/admin123')

    def create_buildings(self):
        """Create buildings and floors."""
        buildings = []
        
        # Create main building
        building = Building.objects.create(name="Main Building")
        buildings.append(building)
        
        # Create floors
        floors = []
        for floor_num in range(1, 4):  # 3 floors
            floor = Floor.objects.create(
                building=building,
                floor_number=floor_num
            )
            floors.append(floor)
        
        self.stdout.write(f'Created {len(buildings)} building(s) with {len(floors)} floor(s)')
        return buildings

    def create_rooms(self, buildings):
        """Create rooms."""
        rooms = []
        building = buildings[0]
        floors = Floor.objects.filter(building=building)
        
        room_counter = 1
        for floor in floors:
            for room_num in range(1, 5):  # 4 rooms per floor
                room = Room.objects.create(
                    building=building,
                    floor=floor,
                    room_number=f"{room_counter:03d}",
                    status=random.choice(['vacant', 'occupied', 'maintenance']),
                    notes=f"Room {room_counter} on floor {floor.floor_number}"
                )
                rooms.append(room)
                room_counter += 1
        
        self.stdout.write(f'Created {len(rooms)} room(s)')
        return rooms

    def create_tenants(self):
        """Create tenants."""
        tenant_names = [
            "John Smith", "Sarah Johnson", "Mike Davis", "Emily Wilson",
            "David Brown", "Lisa Anderson", "Tom Miller", "Anna Taylor",
            "Chris Garcia", "Maria Rodriguez", "James Martinez", "Jennifer Lee"
        ]
        
        tenants = []
        for i, name in enumerate(tenant_names):
            tenant = Tenant.objects.create(
                full_name=name,
                phone=f"555-{1000 + i:04d}",
                email=f"{name.lower().replace(' ', '.')}@example.com",
                id_proof_url=f"https://example.com/id-proof/{i+1}.pdf"
            )
            tenants.append(tenant)
        
        self.stdout.write(f'Created {len(tenants)} tenant(s)')
        return tenants

    def create_leases(self, tenants, rooms):
        """Create leases."""
        leases = []
        occupied_rooms = [room for room in rooms if room.status == 'occupied']
        
        for i, room in enumerate(occupied_rooms[:len(tenants)]):
            tenant = tenants[i]
            
            # Create lease
            lease = Lease.objects.create(
                tenant=tenant,
                room=room,
                start_date=date.today() - timedelta(days=random.randint(30, 365)),
                end_date=None,  # No end date for active leases
                monthly_rent=Decimal(str(random.randint(3000, 8000))),
                deposit=Decimal(str(random.randint(5000, 15000))),
                billing_day=random.randint(1, 28),
                status='active'
            )
            leases.append(lease)
        
        self.stdout.write(f'Created {len(leases)} lease(s)')
        return leases

    def create_meter_readings(self, rooms):
        """Create meter readings."""
        readings_created = 0
        
        # Create readings for last 3 months
        for month_offset in range(3):
            reading_date = date.today().replace(day=15) - timedelta(days=30 * month_offset)
            
            for room in rooms:
                # Base reading value
                base_value = random.randint(1000, 5000)
                reading_value = base_value + (month_offset * random.randint(50, 200))
                
                MeterReading.objects.create(
                    room=room,
                    reading_date=reading_date,
                    reading_value=Decimal(str(reading_value))
                )
                readings_created += 1
        
        self.stdout.write(f'Created {readings_created} meter reading(s)')

    def create_rent_payments(self, leases):
        """Create rent payments."""
        payments_created = 0
        
        for lease in leases:
            # Create 2-4 payments per lease
            num_payments = random.randint(2, 4)
            
            for i in range(num_payments):
                payment_date = date.today() - timedelta(days=random.randint(1, 90))
                
                RentPayment.objects.create(
                    lease=lease,
                    paid_on=payment_date,
                    amount=lease.monthly_rent,
                    method=random.choice(['Cash', 'Bank Transfer', 'Cheque', 'UPI']),
                    notes=f"Payment for {payment_date.strftime('%B %Y')}"
                )
                payments_created += 1
        
        self.stdout.write(f'Created {payments_created} rent payment(s)')

    def create_settings(self):
        """Create settings."""
        settings_data = [
            ('electricity_rate_per_unit', '10.50'),
            ('currency_symbol', '₹'),
            ('timezone', 'Asia/Kolkata'),
            ('org_name', 'Demo Rental Management'),
            ('address', '123 Demo Street, Demo City, Demo State 12345'),
            ('gstin', '12ABCDE1234F1Z5'),
        ]
        
        for key, value in settings_data:
            Setting.objects.get_or_create(key=key, defaults={'value': value})
        
        self.stdout.write(f'Created {len(settings_data)} setting(s)')

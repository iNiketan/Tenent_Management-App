from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from simple_history.models import HistoricalRecords
import json


class Building(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Floor(models.Model):
    id = models.AutoField(primary_key=True)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='floors')
    floor_number = models.IntegerField(validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['building', 'floor_number']
        ordering = ['building', 'floor_number']

    def __str__(self):
        return f"{self.building.name} - Floor {self.floor_number}"


class Room(models.Model):
    STATUS_CHOICES = [
        ('vacant', 'Vacant'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Maintenance'),
    ]

    id = models.AutoField(primary_key=True)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='rooms')
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='vacant')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    class Meta:
        unique_together = ['building', 'room_number']
        ordering = ['building', 'floor__floor_number', 'room_number']

    def __str__(self):
        return f"{self.building.name} - Floor {self.floor.floor_number} - Room {self.room_number}"

    def clean(self):
        if self.floor.building != self.building:
            raise ValidationError("Floor must belong to the same building as the room.")


class Tenant(models.Model):
    id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    id_proof_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class Lease(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('ended', 'Ended'),
    ]

    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name='leases')
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='leases')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    billing_day = models.SmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        default=1
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.tenant.full_name} - {self.room}"

    def clean(self):
        if self.end_date and self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date.")
        
        # For NEW active leases, check if room already has an active lease
        # (Don't check room.status because it will be updated to 'occupied' on save)
        if self.status == 'active' and not self.pk:
            # Check for existing active lease on this room
            existing_active = Lease.objects.filter(
                room=self.room,
                status='active'
            ).exclude(pk=self.pk if self.pk else None).exists()
            
            if existing_active:
                raise ValidationError("This room already has an active lease.")
        
        # For existing leases being updated to active, verify room isn't already occupied by another lease
        elif self.status == 'active' and self.pk:
            existing_active = Lease.objects.filter(
                room=self.room,
                status='active'
            ).exclude(pk=self.pk).exists()
            
            if existing_active:
                raise ValidationError("This room already has another active lease.")

    def save(self, *args, **kwargs):
        self.clean()
        if self.status == 'active' and not self.pk:
            # New active lease - set room to occupied
            self.room.status = 'occupied'
            self.room.save()
        elif self.status == 'ended' and self.pk:
            # Lease ended - set room to vacant
            self.room.status = 'vacant'
            self.room.save()
        super().save(*args, **kwargs)


class RentPayment(models.Model):
    id = models.AutoField(primary_key=True)
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name='payments')
    paid_on = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=40, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-paid_on']

    def __str__(self):
        return f"{self.lease} - {self.amount} on {self.paid_on}"


class MeterReading(models.Model):
    id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='meter_readings')
    reading_date = models.DateField()
    reading_value = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    class Meta:
        unique_together = ['room', 'reading_date']
        ordering = ['room', '-reading_date']

    def __str__(self):
        return f"{self.room} - {self.reading_value} on {self.reading_date}"


class Invoice(models.Model):
    TYPE_CHOICES = [
        ('rent', 'Rent'),
        ('electricity', 'Electricity'),
        ('combined', 'Combined'),
    ]

    id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='invoices')
    month = models.DateField()  # Truncated to first of month
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    pdf_url = models.CharField(max_length=500, blank=True)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    class Meta:
        unique_together = ['room', 'month', 'type']
        ordering = ['-month', 'room']

    def __str__(self):
        return f"{self.room} - {self.type} - {self.month.strftime('%Y-%m')}"


class InvoiceItem(models.Model):
    id = models.AutoField(primary_key=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    label = models.TextField()
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['invoice', 'id']

    def __str__(self):
        return f"{self.invoice} - {self.label}"


class Setting(models.Model):
    key = models.CharField(max_length=50, primary_key=True)
    value = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['key']

    def __str__(self):
        return f"{self.key}: {self.value}"

    @classmethod
    def get_value(cls, key, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(cls, key, value):
        setting, created = cls.objects.get_or_create(key=key)
        setting.value = str(value)
        setting.save()
        return setting

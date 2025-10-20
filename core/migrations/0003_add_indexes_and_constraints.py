# Generated migration - Add database indexes and constraints for performance and data integrity

from django.db import migrations, models
import django.db.models.functions


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_historicalinvoice_historicallease_and_more'),
    ]

    operations = [
        # 1. Add unique constraint - room_number per building
        migrations.AddConstraint(
            model_name='room',
            constraint=models.UniqueConstraint(
                fields=['building', 'room_number'],
                name='unique_room_per_building'
            ),
        ),
        
        # 2. Add unique constraint - only one active lease per room
        migrations.AddConstraint(
            model_name='lease',
            constraint=models.UniqueConstraint(
                fields=['room'],
                condition=models.Q(status='active'),
                name='unique_active_lease_per_room'
            ),
        ),
        
        # 3. Add check constraint - end_date after start_date
        migrations.AddConstraint(
            model_name='lease',
            constraint=models.CheckConstraint(
                check=models.Q(end_date__isnull=True) | models.Q(end_date__gt=models.F('start_date')),
                name='end_date_after_start_date'
            ),
        ),
        
        # 4. Add check constraint - monthly_rent > 0
        migrations.AddConstraint(
            model_name='lease',
            constraint=models.CheckConstraint(
                check=models.Q(monthly_rent__gt=0),
                name='monthly_rent_positive'
            ),
        ),
        
        # 5. Add indexes for common queries
        migrations.AddIndex(
            model_name='lease',
            index=models.Index(
                fields=['status', 'start_date'],
                name='lease_status_start_idx'
            ),
        ),
        
        migrations.AddIndex(
            model_name='lease',
            index=models.Index(
                fields=['room', 'status'],
                name='lease_room_status_idx'
            ),
        ),
        
        migrations.AddIndex(
            model_name='rentpayment',
            index=models.Index(
                fields=['lease', 'paid_on'],
                name='payment_lease_date_idx'
            ),
        ),
        
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(
                fields=['room', 'month'],
                name='invoice_room_month_idx'
            ),
        ),
        
        migrations.AddIndex(
            model_name='meterreading',
            index=models.Index(
                fields=['room', 'reading_date'],
                name='meter_room_date_idx'
            ),
        ),
        
        # 6. Add index on tenant phone (for lookups)
        migrations.AddIndex(
            model_name='tenant',
            index=models.Index(
                fields=['phone'],
                name='tenant_phone_idx'
            ),
        ),
    ]


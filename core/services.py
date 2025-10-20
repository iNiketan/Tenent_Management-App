"""
Business Logic Services for Tenant Management System

This module contains all business logic extracted from views for:
- Better testability
- Reusability across views/API/CLI
- Transactional consistency
- Clear business rules
"""

from decimal import Decimal
from datetime import date
from django.db import transaction
from django.core.exceptions import ValidationError
from core.models import Lease, Room, RentPayment, Invoice, InvoiceItem


class LeaseService:
    """
    Centralize all lease-related business logic.
    """
    
    @staticmethod
    @transaction.atomic
    def create_lease(*, tenant, room, start_date, monthly_rent, deposit=0, 
                     billing_day=1, created_by=None):
        """
        Create a new lease with all validations and side effects.
        
        Rules:
        - Room must be vacant
        - No overlapping active leases
        - Auto-update room status
        - Create first invoice
        
        Args:
            tenant: Tenant model instance
            room: Room model instance
            start_date: Date when lease starts
            monthly_rent: Decimal, must be > 0
            deposit: Decimal, security deposit (default 0)
            billing_day: Int, day of month for billing (1-28, default 1)
            created_by: User who created the lease (optional)
            
        Returns:
            Lease instance
            
        Raises:
            ValidationError: If validation fails
        """
        # Validation - check if room already has an active lease
        existing_active = Lease.objects.filter(room=room, status='active').first()
        if existing_active:
            raise ValidationError(
                f"Room {room.room_number} already has an active lease "
                f"with {existing_active.tenant.full_name}"
            )
        
        if monthly_rent <= 0:
            raise ValidationError("Monthly rent must be positive")
        
        if not (1 <= billing_day <= 28):
            raise ValidationError("Billing day must be between 1 and 28")
        
        # Create lease
        lease = Lease.objects.create(
            tenant=tenant,
            room=room,
            start_date=start_date,
            monthly_rent=monthly_rent,
            deposit=deposit,
            billing_day=billing_day,
            status='active',
        )
        
        # Room status is auto-updated by Lease.save() 
        # But let's make it explicit for clarity:
        room.status = 'occupied'
        room.save(update_fields=['status'])
        
        # Create first month's invoice
        current_month = date(start_date.year, start_date.month, 1)
        invoice = Invoice.objects.create(
            room=room,
            month=current_month,
            type='rent',
            subtotal=monthly_rent,
            tax=Decimal('0'),
            total=monthly_rent,
            meta={'rent': float(monthly_rent)}
        )
        
        InvoiceItem.objects.create(
            invoice=invoice,
            label=f"Rent for {current_month.strftime('%B %Y')}",
            qty=Decimal('1'),
            rate=monthly_rent,
            amount=monthly_rent
        )
        
        return lease
    
    @staticmethod
    @transaction.atomic
    def end_lease(lease, end_date, reason='', ended_by=None):
        """
        End a lease with proper cleanup.
        
        Args:
            lease: Lease instance to end
            end_date: Date when lease ends
            reason: Reason for termination (optional)
            ended_by: User who ended the lease (optional)
            
        Returns:
            Updated Lease instance
            
        Raises:
            ValidationError: If validation fails
        """
        if lease.status != 'active':
            raise ValidationError("Lease is not active")
        
        if end_date < lease.start_date:
            raise ValidationError("End date cannot be before start date")
        
        lease.status = 'ended'
        lease.end_date = end_date
        lease.save()
        
        # Update room status
        lease.room.status = 'vacant'
        lease.room.save(update_fields=['status'])
        
        return lease
    
    @staticmethod
    def get_lease_balance(lease, as_of_date=None):
        """
        Calculate total balance for a lease.
        
        Args:
            lease: Lease instance
            as_of_date: Calculate balance as of this date (default: today)
            
        Returns:
            Decimal: Total outstanding balance (positive = owed, negative = overpaid)
        """
        as_of_date = as_of_date or date.today()
        
        # Get all invoices up to date
        invoices = Invoice.objects.filter(
            room=lease.room,
            month__lte=as_of_date
        )
        total_due = sum(inv.total for inv in invoices)
        
        # Get all payments
        payments = RentPayment.objects.filter(
            lease=lease,
            paid_on__lte=as_of_date
        )
        total_paid = sum(pay.amount for pay in payments)
        
        return total_due - total_paid


class PaymentService:
    """
    Handle all payment operations.
    """
    
    @staticmethod
    @transaction.atomic
    def record_payment(*, lease, amount, paid_on, method='', notes='', 
                      recorded_by=None):
        """
        Record a rent payment with validation.
        
        Args:
            lease: Lease instance
            amount: Decimal, payment amount (must be > 0)
            paid_on: Date payment was received
            method: Payment method (e.g., 'cash', 'bank', 'upi')
            notes: Additional notes (optional)
            recorded_by: User who recorded the payment (optional)
            
        Returns:
            RentPayment instance
            
        Raises:
            ValidationError: If validation fails
        """
        if amount <= 0:
            raise ValidationError("Payment amount must be positive")
        
        if not lease or lease.status != 'active':
            raise ValidationError("Lease must be active")
        
        payment = RentPayment.objects.create(
            lease=lease,
            amount=amount,
            paid_on=paid_on,
            method=method,
            notes=notes
        )
        
        return payment
    
    @staticmethod
    @transaction.atomic
    def mark_invoice_paid(invoice, amount, paid_on, method=''):
        """
        Mark an invoice as paid by creating/updating a payment.
        
        Args:
            invoice: Invoice instance
            amount: Decimal, amount paid
            paid_on: Date payment was received
            method: Payment method
            
        Returns:
            RentPayment instance
            
        Raises:
            ValidationError: If no active lease for room
        """
        lease = Lease.objects.filter(
            room=invoice.room,
            status='active'
        ).first()
        
        if not lease:
            raise ValidationError("No active lease for this room")
        
        # Check for existing payment this month
        existing = RentPayment.objects.filter(
            lease=lease,
            paid_on__year=paid_on.year,
            paid_on__month=paid_on.month
        ).first()
        
        if existing:
            # Update existing payment
            existing.amount = amount
            existing.method = method
            existing.paid_on = paid_on
            existing.save()
            return existing
        else:
            # Create new payment
            return PaymentService.record_payment(
                lease=lease,
                amount=amount,
                paid_on=paid_on,
                method=method
            )


class InvoiceService:
    """
    Handle invoice/billing operations.
    """
    
    @staticmethod
    @transaction.atomic
    def create_monthly_invoice(room, month, rent_amount, electricity_units=None, 
                              electricity_rate=None):
        """
        Create a monthly invoice for a room.
        
        Args:
            room: Room instance
            month: Date (first day of the month)
            rent_amount: Decimal, monthly rent
            electricity_units: Optional units consumed
            electricity_rate: Optional rate per unit
            
        Returns:
            Invoice instance
        """
        subtotal = rent_amount
        electricity_amount = Decimal('0')
        
        if electricity_units and electricity_rate:
            electricity_amount = Decimal(str(electricity_units)) * Decimal(str(electricity_rate))
            subtotal += electricity_amount
        
        invoice = Invoice.objects.create(
            room=room,
            month=month,
            type='rent',
            subtotal=subtotal,
            tax=Decimal('0'),
            total=subtotal,
            meta={
                'rent': float(rent_amount),
                'units': electricity_units,
                'rate': float(electricity_rate) if electricity_rate else None,
                'electricity_total': float(electricity_amount)
            }
        )
        
        # Create invoice items
        InvoiceItem.objects.create(
            invoice=invoice,
            label=f"Rent for {month.strftime('%B %Y')}",
            qty=Decimal('1'),
            rate=rent_amount,
            amount=rent_amount
        )
        
        if electricity_amount > 0:
            InvoiceItem.objects.create(
                invoice=invoice,
                label=f"Electricity ({electricity_units} units)",
                qty=Decimal(str(electricity_units)),
                rate=Decimal(str(electricity_rate)),
                amount=electricity_amount
            )
        
        return invoice


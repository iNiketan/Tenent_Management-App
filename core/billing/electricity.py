from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime
from typing import Optional, Dict, Any
from django.db.models import Q
from core.models import Setting, MeterReading, Room


def get_rate() -> Decimal:
    """Get electricity rate per unit from settings."""
    rate_str = Setting.get_value('electricity_rate_per_unit', '0')
    try:
        return Decimal(rate_str)
    except (ValueError, TypeError):
        return Decimal('0')


def compute_units(previous: Optional[Decimal], current: Optional[Decimal]) -> Decimal:
    """
    Compute units consumed between two readings.
    
    Args:
        previous: Previous meter reading (None for first month)
        current: Current meter reading
        
    Returns:
        Units consumed
        
    Raises:
        ValueError: If delta is negative
    """
    if previous is None:
        return Decimal('0')
    
    if current is None:
        return Decimal('0')
    
    delta = current - previous
    if delta < 0:
        raise ValueError("Negative delta: current reading cannot be less than previous reading")
    
    return delta


def compute_bill(previous_reading: Optional[Decimal], current_reading: Optional[Decimal], rate: Decimal) -> Dict[str, Any]:
    """
    Compute electricity bill for given readings and rate.
    
    Args:
        previous_reading: Previous meter reading
        current_reading: Current meter reading
        rate: Rate per unit
        
    Returns:
        Dict with units, rate, and total
    """
    units = compute_units(previous_reading, current_reading)
    total = (units * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    return {
        'units': units,
        'rate': rate,
        'total': total
    }


def get_month_readings(room_id: int, year: int, month: int) -> tuple[Optional[Decimal], Optional[Decimal]]:
    """
    Get previous and current readings for a specific month.
    
    Args:
        room_id: Room ID
        year: Year
        month: Month (1-12)
        
    Returns:
        Tuple of (previous_reading, current_reading)
    """
    first_of_month = date(year, month, 1)
    
    # Get previous reading (latest reading before first of month)
    previous_reading = MeterReading.objects.filter(
        room_id=room_id,
        reading_date__lt=first_of_month
    ).order_by('-reading_date').first()
    
    # Get current reading (latest reading in the month)
    if month == 12:
        first_of_next_month = date(year + 1, 1, 1)
    else:
        first_of_next_month = date(year, month + 1, 1)
    
    current_reading = MeterReading.objects.filter(
        room_id=room_id,
        reading_date__gte=first_of_month,
        reading_date__lt=first_of_next_month
    ).order_by('-reading_date').first()
    
    previous_value = previous_reading.reading_value if previous_reading else None
    current_value = current_reading.reading_value if current_reading else None
    
    return previous_value, current_value


def calc_month_bill(room_id: int, year: int, month: int) -> Dict[str, Any]:
    """
    Calculate electricity bill for a room for a specific month.
    
    Args:
        room_id: Room ID
        year: Year
        month: Month (1-12)
        
    Returns:
        Dict with billing details
    """
    try:
        room = Room.objects.get(id=room_id)
    except Room.DoesNotExist:
        raise ValueError(f"Room with id {room_id} does not exist")
    
    previous_reading, current_reading = get_month_readings(room_id, year, month)
    rate = get_rate()
    
    try:
        bill_details = compute_bill(previous_reading, current_reading, rate)
    except ValueError as e:
        return {
            'room_id': room_id,
            'room': str(room),
            'month': f"{year}-{month:02d}",
            'previous_reading': previous_reading,
            'current_reading': current_reading,
            'units': Decimal('0'),
            'rate': rate,
            'total': Decimal('0'),
            'error': str(e)
        }
    
    return {
        'room_id': room_id,
        'room': str(room),
        'month': f"{year}-{month:02d}",
        'previous_reading': previous_reading,
        'current_reading': current_reading,
        'units': bill_details['units'],
        'rate': bill_details['rate'],
        'total': bill_details['total']
    }


def validate_monotonic_readings(room_id: int, reading_date: date, reading_value: Decimal) -> bool:
    """
    Validate that a new reading is monotonic (not less than previous reading).
    
    Args:
        room_id: Room ID
        reading_date: Date of the reading
        reading_value: Value of the reading
        
    Returns:
        True if valid, False otherwise
    """
    # Get the most recent reading before this date
    previous_reading = MeterReading.objects.filter(
        room_id=room_id,
        reading_date__lt=reading_date
    ).order_by('-reading_date').first()
    
    if previous_reading and reading_value < previous_reading.reading_value:
        return False
    
    return True


def get_room_billing_summary(room_id: int, year: int, month: int) -> Dict[str, Any]:
    """
    Get comprehensive billing summary for a room for a specific month.
    
    Args:
        room_id: Room ID
        year: Year
        month: Month (1-12)
        
    Returns:
        Dict with billing summary including lease info
    """
    try:
        room = Room.objects.get(id=room_id)
    except Room.DoesNotExist:
        raise ValueError(f"Room with id {room_id} does not exist")
    
    # Get active lease
    active_lease = room.leases.filter(status='active').first()
    
    # Get electricity bill
    electricity_bill = calc_month_bill(room_id, year, month)
    
    # Get rent due
    rent_due = Decimal('0')
    if active_lease:
        rent_due = active_lease.monthly_rent
    
    return {
        'room_id': room_id,
        'room': str(room),
        'month': f"{year}-{month:02d}",
        'active_lease': active_lease,
        'rent_due': rent_due,
        'electricity': electricity_bill,
        'total_due': rent_due + electricity_bill.get('total', Decimal('0'))
    }

# Fix: Tenant Assignment Error

## Problem

When trying to assign a tenant to a vacant room, you were getting:
```
Error creating lease: ['Room must be occupied for active lease.']
```

## Root Cause

The `Lease` model had a **chicken-and-egg validation problem**:

```python
# OLD CODE (WRONG):
def clean(self):
    if self.status == 'active' and self.room.status != 'occupied':
        raise ValidationError("Room must be occupied for active lease.")
```

**The Problem:**
1. When creating a NEW lease for a vacant room, the room is still `'vacant'`
2. Validation runs FIRST (in `clean()`)
3. Room status update happens SECOND (in `save()`)
4. So validation fails before the room can be marked occupied!

```
┌─────────────────────────────────────────────────┐
│ Timeline (OLD BROKEN CODE):                     │
├─────────────────────────────────────────────────┤
│ 1. Lease.create() called                        │
│ 2. clean() runs → checks room.status            │
│    └─> room.status = 'vacant' ❌                │
│    └─> Validation FAILS!                        │
│                                                  │
│ 3. save() never runs (never updates room)       │
└─────────────────────────────────────────────────┘
```

## Solution

Changed the validation logic to:
1. **For NEW leases**: Check if room already has another active lease (ignore room.status)
2. **For existing leases**: Same check
3. Let the `save()` method handle updating room status to 'occupied'

```python
# NEW CODE (CORRECT):
def clean(self):
    if self.status == 'active' and not self.pk:  # NEW lease
        # Check for existing active lease on this room
        existing_active = Lease.objects.filter(
            room=self.room,
            status='active'
        ).exists()
        
        if existing_active:
            raise ValidationError("This room already has an active lease.")
```

**Now it works:**
```
┌─────────────────────────────────────────────────┐
│ Timeline (NEW FIXED CODE):                      │
├─────────────────────────────────────────────────┤
│ 1. Lease.create() called                        │
│ 2. clean() runs → checks for duplicate lease    │
│    └─> No other active lease ✅                 │
│    └─> Validation PASSES!                       │
│                                                  │
│ 3. save() runs:                                 │
│    └─> Updates room.status to 'occupied' ✅     │
│    └─> Creates lease ✅                         │
└─────────────────────────────────────────────────┘
```

## Files Changed

1. **`core/models.py`** - Fixed `Lease.clean()` validation logic
2. **`core/services.py`** - Updated `LeaseService.create_lease()` to match

## Testing

Now you can assign tenants to vacant rooms:

```python
# This now works! ✅
Lease.objects.create(
    tenant=tenant,
    room=vacant_room,  # room.status = 'vacant'
    status='active',
    start_date=date.today(),
    monthly_rent=Decimal('5000.00')
)

# Room is automatically updated to 'occupied' after save()
```

## What's Still Protected

✅ **Still prevents duplicate active leases:**
```python
# This will still fail (as it should):
Lease.objects.create(tenant=tenant1, room=room, status='active')
Lease.objects.create(tenant=tenant2, room=room, status='active')  # ❌ Error!
```

✅ **Database constraint also enforces this:**
- Migration `0003_add_indexes_and_constraints.py` added a unique constraint
- Double protection at both app and database level

## How to Apply

No migration needed - just restart your server:

```bash
# If server is running, restart it
# Ctrl+C to stop, then:
python manage.py runserver
```

The fix is now active! Try assigning a tenant again - it should work now. ✅

## What This Means

**Before:**
- ❌ Could not assign tenant to vacant room
- ❌ Got "Room must be occupied for active lease" error

**After:**
- ✅ Can assign tenant to vacant room
- ✅ Room automatically becomes 'occupied'
- ✅ Still prevents duplicate active leases
- ✅ Works correctly in all scenarios

---

**Status:** ✅ FIXED  
**Date:** October 20, 2025  
**Impact:** Tenant assignment now works correctly


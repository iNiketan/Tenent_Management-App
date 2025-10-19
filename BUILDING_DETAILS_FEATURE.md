# Building Details Feature

## Overview

This feature adds a comprehensive Building Details page that provides an interactive view of all rooms in a building with financial tracking, lease management, and bill management capabilities.

## Features Implemented

### 1. Building Details Page (`/building/<id>/`)

The main building details page shows:
- **All Rooms Grid View** (default): A responsive grid showing all rooms across all floors
- **Floors Table View** (optional): A collapsible table view organized by floors

#### Room Cards Display:
Each room card shows:
- Room number and floor
- Status badge (Occupied/Vacant/Maintenance)
- Status indicator (OK/Due Soon/Overdue/Vacant/Maintenance)
- Tenant name (if active lease exists)
- Monthly rent
- Last bill period and status
- Electricity units (if applicable)

### 2. Room Details Drawer

Clicking any room card opens a right-side drawer panel with:

#### Section A: Room Status Controls
- Quick toggle buttons to change room status (Occupied/Vacant/Maintenance)
- Updates both the drawer and the room card in real-time via HTMX

#### Section B: Active Lease Information
- Tenant name and phone
- Monthly rent amount
- Lease start and end dates
- Deposit amount

#### Section C: Recent Bills (Last 6)
Each bill entry shows:
- Period (YYYY-MM format)
- Total amount
- Payment status (Paid/Unpaid)
- Due date
- Electricity units (if applicable)

**Quick Action Buttons** on each bill:
- **Mark Paid**: Creates a RentPayment record
- **Mark Unpaid**: Removes payment records
- **Mark Partial**: Creates a partial payment record

#### Section D: Create New Bill Form
- Period selection (month picker)
- Rent amount (pre-filled with lease rent)
- Optional electricity units
- Optional electricity amount
- Creates Invoice and InvoiceItem records

### 3. Floor Table View (Collapsible)

An alternate view showing rooms organized by floors in table format:
- Loads floor data on-demand via HTMX
- Shows all room information in a tabular layout
- Click any row to open the room details drawer

### 4. Navigation Updates

- Added "Buildings" link to the sidebar navigation
- Buildings list on the Map page with direct links to building details
- Back button on building details page to return to map

## Technical Implementation

### New Views (core/views.py)

1. **`get_room_finance_snapshot(room)`**
   - Helper function that generates financial snapshot for a room
   - Calculates badge status based on payment history and due dates
   - Returns structured data about leases, invoices, and payments

2. **`building_details(request, building_id)`**
   - Main view for building details page
   - Generates snapshots for all rooms
   - Passes data to template

3. **`building_floor_partial(request, building_id, floor_index)`**
   - HTMX partial view for floor table
   - Returns HTML table for a specific floor

4. **`room_panel(request, room_id)`**
   - HTMX partial view for room details drawer
   - Shows lease, bills, and create bill form
   - Handles real-time updates

5. **`update_room_status(request, room_id, new_status)`**
   - POST endpoint to update room status
   - Returns updated partial via HTMX
   - Updates both drawer and grid card

6. **`create_bill(request, lease_id)`**
   - POST endpoint to create new invoice
   - Handles rent and electricity billing
   - Returns refreshed room panel

7. **`set_bill_status(request, invoice_id, status)`**
   - POST endpoint to mark bills as paid/unpaid/partial
   - Manages RentPayment records
   - Returns refreshed room panel

### New URLs (core/urls.py)

```python
# Building details
path('building/<int:building_id>/', views.building_details, name='building_details')
path('building/<int:building_id>/floor/<int:floor_index>/', views.building_floor_partial, name='building_floor_partial')

# Room management
path('room/<int:room_id>/panel/', views.room_panel, name='room_panel')
path('room/<int:room_id>/status/<str:new_status>/', views.update_room_status, name='update_room_status')

# Bill management
path('lease/<int:lease_id>/bill/create/', views.create_bill, name='create_bill')
path('invoice/<int:invoice_id>/status/<str:status>/', views.set_bill_status, name='set_bill_status')
```

### New Templates

1. **`templates/core/building_details.html`**
   - Main building details page
   - Rooms grid with Alpine.js for drawer control
   - Floor table collapsible sections
   - Responsive design with Tailwind CSS

2. **`templates/core/partials/room_panel.html`**
   - Room details drawer content
   - Status toggles, lease info, bills list, create bill form
   - HTMX-powered interactive buttons

3. **`templates/core/partials/floor_table.html`**
   - Table view for a specific floor
   - Loaded on-demand via HTMX
   - Clickable rows to open drawer

4. **`templates/core/partials/room_status_update.html`**
   - Partial returned after status update
   - Updates both drawer and grid card using JavaScript

### Updated Templates

1. **`templates/core/map.html`**
   - Added buildings list section with links to building details
   - Improved visual hierarchy

2. **`templates/core/base.html`**
   - Added "Buildings" navigation link in sidebar

## Data Flow

### Room Finance Snapshot
1. Check for active lease
2. If no lease: return Vacant or Maintenance badge
3. If lease exists:
   - Get recent invoices (last 6)
   - Check payment status for each invoice
   - Calculate due dates (5 days after month start)
   - Determine badge: OK / Due Soon / Overdue
   - Extract electricity data from invoice metadata

### Bill Status Management
- **Paid**: Creates RentPayment record with invoice amount
- **Unpaid**: Deletes associated RentPayment records
- **Partial**: Creates RentPayment with 50% of invoice amount

### Invoice Creation
1. Validate period (YYYY-MM format)
2. Check for existing invoice
3. Create Invoice record with type (rent/combined)
4. Create InvoiceItem records for rent and electricity
5. Store metadata (units, amounts)
6. Return refreshed room panel

## UI/UX Features

### Responsive Design
- Grid adapts from 1 to 4 columns based on screen size
- Drawer is full-width on mobile, fixed width on desktop
- Touch targets are minimum 44px for accessibility

### Dark Theme Compatibility
- Uses Tailwind CSS with consistent color scheme
- Slate-800 sidebar with blue accents
- Gray-based cards with colored status badges

### Interactive Elements
- HTMX for seamless partial updates
- Alpine.js for drawer open/close
- Hover effects on cards and buttons
- Smooth transitions and animations

### Status Badge Colors
- 🟢 **Green (OK)**: Bill paid or no overdue amounts
- 🟠 **Orange (Due Soon)**: Due within 3 days
- 🔴 **Red (Overdue)**: Past due date
- ⚪ **Gray (Vacant)**: No active lease
- 🟡 **Yellow (Maintenance)**: Room under maintenance

## Dependencies Added

- `python-dateutil==2.8.2`: For date calculations in badge logic

## Testing

### Manual Testing Steps

1. **Navigate to Buildings**:
   - Click "Buildings" in sidebar
   - Verify buildings list appears
   - Click on a building card

2. **View All Rooms Grid**:
   - Verify all rooms display with correct information
   - Check status badges and colors
   - Verify tenant names and rent amounts

3. **Open Room Drawer**:
   - Click any room card
   - Verify drawer slides in from right
   - Check all sections load correctly

4. **Change Room Status**:
   - Click status buttons in drawer
   - Verify drawer updates
   - Check grid card updates without refresh

5. **Manage Bills**:
   - Click "Mark Paid" on an unpaid bill
   - Verify status changes to paid
   - Try "Mark Unpaid" to reverse
   - Test "Mark Partial" option

6. **Create New Bill**:
   - Fill in the create bill form
   - Submit and verify invoice is created
   - Check it appears in bills list

7. **Floor Table View**:
   - Click "View by Floors (Table)" toggle
   - Verify table view loads
   - Click a room row to open drawer

8. **Responsive Testing**:
   - Test on mobile (320px width)
   - Test on tablet (768px width)
   - Test on desktop (1920px width)

### Seeded Data Testing

```bash
python manage.py seed_demo
```

This creates demo data including buildings, floors, rooms, tenants, leases, and invoices for testing.

## Future Enhancements

Potential improvements for future iterations:

1. **Bulk Operations**: Select multiple rooms for bulk status updates
2. **Advanced Filtering**: Filter rooms by status, tenant, payment status
3. **Export Features**: Export room/billing data to CSV/PDF
4. **Payment History**: Detailed payment history with receipts
5. **Notifications**: Alert for overdue bills
6. **Custom Due Dates**: Per-lease due date configuration
7. **Recurring Bills**: Auto-generate monthly bills
8. **Analytics Dashboard**: Building-level financial analytics

## Troubleshooting

### Drawer Doesn't Open
- Check browser console for JavaScript errors
- Verify Alpine.js is loaded
- Check HTMX version compatibility

### Bills Not Updating
- Verify CSRF token is included in forms
- Check network tab for failed requests
- Ensure proper HTMX attributes

### Status Badge Incorrect
- Verify invoice dates are correct
- Check RentPayment records exist
- Review `get_room_finance_snapshot` logic

### Floor Table Not Loading
- Check HTMX `hx-trigger="intersect once"` works
- Verify URL patterns match
- Check for template errors in console

## Performance Considerations

- **Database Queries**: Uses `select_related()` for efficient queries
- **Lazy Loading**: Floor tables load on-demand via HTMX
- **Caching**: Consider adding caching for building snapshots
- **Pagination**: For buildings with many rooms, consider pagination

## Security

- All views require `@login_required` decorator
- CSRF protection on all POST requests
- Input validation for status values and dates
- GET/POST method restrictions with `@require_http_methods`

## Accessibility

- Minimum 44px touch targets
- Semantic HTML structure
- ARIA labels where needed
- Keyboard navigation support
- Screen reader friendly

## Browser Compatibility

Tested and compatible with:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Requires:
- JavaScript enabled
- Modern CSS support (Flexbox, Grid)
- HTMX 1.9.10
- Alpine.js 3.x


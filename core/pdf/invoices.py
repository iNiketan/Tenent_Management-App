from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import os
from datetime import datetime

from ..models import Invoice, Setting


def generate_invoice_pdf(invoice_id):
    """Generate PDF for an invoice."""
    try:
        invoice = Invoice.objects.get(id=invoice_id)
    except Invoice.DoesNotExist:
        raise ValueError(f"Invoice with id {invoice_id} does not exist")
    
    # Get organization settings
    org_name = Setting.get_value('org_name', 'Rental Management System')
    org_address = Setting.get_value('address', '')
    gstin = Setting.get_value('gstin', '')
    currency_symbol = Setting.get_value('currency_symbol', '₹')
    
    # Get tenant info if available
    tenant_info = None
    if invoice.meta and 'tenant_id' in invoice.meta:
        from ..models import Tenant
        try:
            tenant = Tenant.objects.get(id=invoice.meta['tenant_id'])
            tenant_info = {
                'name': tenant.full_name,
                'phone': tenant.phone,
                'email': tenant.email,
            }
        except Tenant.DoesNotExist:
            pass
    
    # Get room info
    room = invoice.room
    building = room.building
    floor = room.floor
    
    context = {
        'invoice': invoice,
        'org_name': org_name,
        'org_address': org_address,
        'gstin': gstin,
        'currency_symbol': currency_symbol,
        'tenant_info': tenant_info,
        'room': room,
        'building': building,
        'floor': floor,
        'generated_at': datetime.now(),
    }
    
    # Render HTML template
    html_string = render_to_string('core/pdf/invoice.html', context)
    
    # Generate PDF
    font_config = FontConfiguration()
    html_doc = HTML(string=html_string)
    
    css_string = """
    @page {
        size: A4;
        margin: 1cm;
    }
    body {
        font-family: Arial, sans-serif;
        font-size: 12px;
        line-height: 1.4;
    }
    .header {
        border-bottom: 2px solid #333;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .invoice-title {
        font-size: 24px;
        font-weight: bold;
        color: #333;
    }
    .invoice-number {
        font-size: 14px;
        color: #666;
    }
    .org-info {
        margin-bottom: 20px;
    }
    .org-name {
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .org-address {
        color: #666;
        margin-bottom: 5px;
    }
    .gstin {
        color: #666;
        font-size: 11px;
    }
    .invoice-details {
        margin-bottom: 20px;
    }
    .detail-row {
        display: flex;
        margin-bottom: 5px;
    }
    .detail-label {
        font-weight: bold;
        width: 150px;
    }
    .detail-value {
        flex: 1;
    }
    .items-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
    }
    .items-table th,
    .items-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    .items-table th {
        background-color: #f5f5f5;
        font-weight: bold;
    }
    .items-table .text-right {
        text-align: right;
    }
    .totals {
        margin-top: 20px;
        text-align: right;
    }
    .total-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
    }
    .total-label {
        font-weight: bold;
    }
    .total-value {
        font-weight: bold;
    }
    .grand-total {
        font-size: 16px;
        border-top: 2px solid #333;
        padding-top: 10px;
    }
    .footer {
        margin-top: 30px;
        text-align: center;
        color: #666;
        font-size: 10px;
    }
    """
    
    css_doc = CSS(string=css_string, font_config=font_config)
    
    # Generate PDF bytes
    pdf_bytes = html_doc.write_pdf(stylesheets=[css_doc], font_config=font_config)
    
    return pdf_bytes


def save_invoice_pdf(invoice_id):
    """Generate and save PDF for an invoice, returning the file path."""
    pdf_bytes = generate_invoice_pdf(invoice_id)
    
    # Create media directory if it doesn't exist
    media_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
    os.makedirs(media_dir, exist_ok=True)
    
    # Generate filename
    invoice = Invoice.objects.get(id=invoice_id)
    filename = f"invoice_{invoice_id}_{invoice.month.strftime('%Y%m')}.pdf"
    file_path = os.path.join(media_dir, filename)
    
    # Save PDF file
    with open(file_path, 'wb') as f:
        f.write(pdf_bytes)
    
    # Update invoice with PDF URL
    invoice.pdf_url = f"/media/invoices/{filename}"
    invoice.save()
    
    return file_path


def generate_electricity_invoice_pdf(room_id, year, month):
    """Generate PDF for electricity invoice."""
    from ..billing.electricity import calc_month_bill
    
    # Calculate bill
    bill_data = calc_month_bill(room_id, year, month)
    
    if 'error' in bill_data:
        raise ValueError(bill_data['error'])
    
    # Get room info
    from ..models import Room
    room = Room.objects.get(id=room_id)
    
    # Get organization settings
    org_name = Setting.get_value('org_name', 'Rental Management System')
    org_address = Setting.get_value('address', '')
    gstin = Setting.get_value('gstin', '')
    currency_symbol = Setting.get_value('currency_symbol', '₹')
    
    # Get tenant info if available
    tenant_info = None
    active_lease = room.leases.filter(status='active').first()
    if active_lease:
        tenant_info = {
            'name': active_lease.tenant.full_name,
            'phone': active_lease.tenant.phone,
            'email': active_lease.tenant.email,
        }
    
    context = {
        'bill_data': bill_data,
        'org_name': org_name,
        'org_address': org_address,
        'gstin': gstin,
        'currency_symbol': currency_symbol,
        'tenant_info': tenant_info,
        'room': room,
        'building': room.building,
        'floor': room.floor,
        'generated_at': datetime.now(),
        'month': f"{year}-{month:02d}",
    }
    
    # Render HTML template
    html_string = render_to_string('core/pdf/electricity_invoice.html', context)
    
    # Generate PDF
    font_config = FontConfiguration()
    html_doc = HTML(string=html_string)
    
    css_string = """
    @page {
        size: A4;
        margin: 1cm;
    }
    body {
        font-family: Arial, sans-serif;
        font-size: 12px;
        line-height: 1.4;
    }
    .header {
        border-bottom: 2px solid #333;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .invoice-title {
        font-size: 24px;
        font-weight: bold;
        color: #333;
    }
    .invoice-number {
        font-size: 14px;
        color: #666;
    }
    .org-info {
        margin-bottom: 20px;
    }
    .org-name {
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .org-address {
        color: #666;
        margin-bottom: 5px;
    }
    .gstin {
        color: #666;
        font-size: 11px;
    }
    .invoice-details {
        margin-bottom: 20px;
    }
    .detail-row {
        display: flex;
        margin-bottom: 5px;
    }
    .detail-label {
        font-weight: bold;
        width: 150px;
    }
    .detail-value {
        flex: 1;
    }
    .billing-details {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .billing-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .billing-label {
        font-weight: bold;
    }
    .billing-value {
        font-weight: bold;
    }
    .total-amount {
        font-size: 18px;
        color: #333;
        border-top: 2px solid #333;
        padding-top: 10px;
        margin-top: 15px;
    }
    .footer {
        margin-top: 30px;
        text-align: center;
        color: #666;
        font-size: 10px;
    }
    """
    
    css_doc = CSS(string=css_string, font_config=font_config)
    
    # Generate PDF bytes
    pdf_bytes = html_doc.write_pdf(stylesheets=[css_doc], font_config=font_config)
    
    return pdf_bytes

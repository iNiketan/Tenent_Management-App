from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Building, Floor, Room, Tenant, Lease, RentPayment, 
    MeterReading, Invoice, InvoiceItem, Setting
)


class BuildingForm(forms.ModelForm):
    """Form for creating/editing buildings."""
    class Meta:
        model = Building
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 min-h-[44px]',
                'placeholder': 'e.g., Sunshine Apartments'
            })
        }


class BuildingWithFloorsForm(forms.Form):
    """Form for creating a building with multiple floors and rooms in one go."""
    building_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 min-h-[44px]',
            'placeholder': 'e.g., Sunshine Apartments'
        })
    )
    num_floors = forms.IntegerField(
        min_value=1,
        max_value=50,
        initial=3,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 min-h-[44px]',
            'min': '1',
            'max': '50'
        })
    )
    rooms_per_floor = forms.IntegerField(
        min_value=1,
        max_value=100,
        initial=10,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 min-h-[44px]',
            'min': '1',
            'max': '100'
        })
    )
    room_number_prefix = forms.CharField(
        max_length=10,
        required=False,
        initial='',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 min-h-[44px]',
            'placeholder': 'e.g., A, B, or leave blank'
        })
    )
    
    def clean_building_name(self):
        name = self.cleaned_data.get('building_name')
        if Building.objects.filter(name__iexact=name).exists():
            raise ValidationError(f'A building with the name "{name}" already exists.')
        return name


class FloorForm(forms.ModelForm):
    class Meta:
        model = Floor
        fields = ['building', 'floor_number']
        widgets = {
            'building': forms.Select(attrs={
                'class': 'form-select rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'floor_number': forms.NumberInput(attrs={
                'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'min': '0'
            })
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['building', 'floor', 'room_number', 'status', 'notes']
        widgets = {
            'building': forms.Select(attrs={
                'class': 'form-select rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'hx-get': '/api/floors/',
                'hx-target': '#id_floor',
                'hx-trigger': 'change'
            }),
            'floor': forms.Select(attrs={
                'class': 'form-select rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'id': 'id_floor'
            }),
            'room_number': forms.TextInput(attrs={
                'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'Room number'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'rows': 3,
                'placeholder': 'Additional notes'
            })
        }


class TenantForm(forms.ModelForm):
    # Add room and lease fields
    room = forms.ModelChoiceField(
        queryset=Room.objects.filter(status='vacant'),
        required=False,
        empty_label="Select a room (optional)",
        widget=forms.Select(attrs={
            'class': 'form-select rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
        })
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
            'type': 'date'
        })
    )
    monthly_rent = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Monthly rent'
        })
    )
    deposit = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Security deposit'
        })
    )
    
    class Meta:
        model = Tenant
        fields = ['full_name', 'phone', 'email', 'id_proof_url']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'Full name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'Phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'Email address'
            }),
            'id_proof_url': forms.URLInput(attrs={
                'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'ID proof URL (optional)'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        room = cleaned_data.get('room')
        start_date = cleaned_data.get('start_date')
        monthly_rent = cleaned_data.get('monthly_rent')
        
        # If room is selected, require lease details
        if room:
            if not start_date:
                self.add_error('start_date', 'Start date is required when assigning a room')
            if not monthly_rent:
                self.add_error('monthly_rent', 'Monthly rent is required when assigning a room')
        
        return cleaned_data


class LeaseForm(forms.ModelForm):
    class Meta:
        model = Lease
        fields = ['tenant', 'room', 'start_date', 'end_date', 'monthly_rent', 'deposit', 'billing_day', 'status']
        widgets = {
            'tenant': forms.Select(attrs={
                'class': 'form-select rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'room': forms.Select(attrs={
                'class': 'form-select rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'type': 'date'
            }),
            'monthly_rent': forms.NumberInput(attrs={
                'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'step': '0.01',
                'min': '0'
            }),
            'deposit': forms.NumberInput(attrs={
                'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'step': '0.01',
                'min': '0'
            }),
            'billing_day': forms.NumberInput(attrs={
                'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'min': '1',
                'max': '28'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if end_date and start_date and end_date <= start_date:
            raise ValidationError("End date must be after start date.")
        
        return cleaned_data


class RentPaymentForm(forms.ModelForm):
    class Meta:
        model = RentPayment
        fields = ['lease', 'paid_on', 'amount', 'method', 'notes']
        widgets = {
            'lease': forms.Select(attrs={
                'class': 'form-select rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'paid_on': forms.DateInput(attrs={
                'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'type': 'date'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'step': '0.01',
                'min': '0'
            }),
            'method': forms.TextInput(attrs={
                'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'Payment method (Cash, Bank Transfer, etc.)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'rows': 3,
                'placeholder': 'Additional notes'
            })
        }


class MeterReadingForm(forms.ModelForm):
    class Meta:
        model = MeterReading
        fields = ['reading_date', 'reading_value']
        widgets = {
            'reading_date': forms.DateInput(attrs={
                'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'type': 'date'
            }),
            'reading_value': forms.NumberInput(attrs={
                'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'step': '0.01',
                'min': '0'
            })
        }


class SettingForm(forms.Form):
    electricity_rate_per_unit = forms.DecimalField(
        label='Electricity Rate per Unit (₹)',
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
            'step': '0.01',
            'min': '0'
        })
    )
    currency_symbol = forms.CharField(
        label='Currency Symbol',
        max_length=5,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
            'placeholder': '₹'
        })
    )
    timezone = forms.CharField(
        label='Timezone',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
            'placeholder': 'Asia/Kolkata'
        })
    )
    org_name = forms.CharField(
        label='Organization Name',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
            'placeholder': 'Organization name'
        })
    )
    address = forms.CharField(
        label='Address',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
            'rows': 3,
            'placeholder': 'Organization address'
        })
    )
    gstin = forms.CharField(
        label='GSTIN',
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
            'placeholder': 'GSTIN number'
        })
    )

    def save(self):
        """Save settings to the database."""
        for field_name, value in self.cleaned_data.items():
            if value is not None and value != '':
                Setting.set_value(field_name, value)

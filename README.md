# Rental Management System

A comprehensive Django-based tenant management web application with electricity billing, invoice generation, and modern HTMX frontend.

## Features

- **Room Management**: Track buildings, floors, and rooms with status monitoring
- **Tenant Management**: Complete tenant profiles with contact information
- **Lease Management**: Handle lease agreements with automatic room status updates
- **Electricity Billing**: Automated meter reading processing and bill calculation
- **Invoice Generation**: PDF invoice generation for rent and electricity bills
- **Payment Tracking**: Record and track rent payments
- **Modern UI**: HTMX-powered frontend with Tailwind CSS
- **REST API**: Complete API for all operations
- **Admin Interface**: Django admin with advanced filtering and search

## Tech Stack

- **Backend**: Django 5, Django REST Framework, PostgreSQL/SQLite
- **Frontend**: HTMX, Tailwind CSS, Alpine.js
- **PDF Generation**: WeasyPrint
- **Testing**: pytest, pytest-django
- **Development**: django-debug-toolbar, django-environ

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (optional, SQLite for development)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd rental-manager
   ```

2. **Install dependencies**
   ```bash
   make install
   # or manually:
   pip install -r requirements.txt
   npm install
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run migrations**
   ```bash
   make migrate
   # or manually:
   python manage.py migrate
   ```

5. **Seed demo data**
   ```bash
   make seed
   # or manually:
   python manage.py seed_demo
   ```

6. **Build CSS**
   ```bash
   make build-css
   # or manually:
   npm run build-css-prod
   ```

7. **Start development server**
   ```bash
   make dev
   # or manually:
   python manage.py runserver
   ```

8. **Access the application**
   - Web interface: http://localhost:8000
   - Admin interface: http://localhost:8000/admin
   - API: http://localhost:8000/api/

### Default Login

- **Username**: admin
- **Password**: admin123

## Environment Variables

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=sqlite:///db.sqlite3
# For PostgreSQL: postgres://user:password@localhost:5432/dbname

# Security
SECRET_KEY=your-secret-key-here
DEBUG=True

# Hosts
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Available Commands

### Development
- `make dev` - Start development server
- `make test` - Run tests
- `make lint` - Run linting
- `make format` - Format code
- `make build-css` - Build Tailwind CSS
- `make build-css-dev` - Build CSS in watch mode

### Database
- `make migrate` - Run migrations
- `make seed` - Seed demo data
- `make seed-clear` - Clear and seed demo data
- `make superuser` - Create superuser

### Utilities
- `make clean` - Clean temporary files
- `make check` - Run all checks
- `make setup` - Complete initial setup

## API Endpoints

### Authentication
- Session-based authentication (CSRF protected)
- Staff-only access

### Core Endpoints
- `GET/POST /api/buildings/` - Building management
- `GET/POST /api/floors/` - Floor management
- `GET/POST /api/rooms/` - Room management
- `GET/POST /api/tenants/` - Tenant management
- `GET/POST /api/leases/` - Lease management
- `GET/POST /api/rent-payments/` - Payment management

### Meter Readings
- `GET/POST /api/meter/readings/` - Single meter reading
- `POST /api/meter/readings/bulk/` - Bulk meter readings
- `GET /api/meter/readings/?room_id=&year=&month=` - Filtered readings

### Billing
- `POST /api/billing/electricity/calc/` - Calculate electricity bill
- `POST /api/invoices/electricity/` - Create electricity invoice
- `POST /api/invoices/rent/` - Create rent invoice
- `GET /api/invoices/` - List invoices

### Settings
- `GET/POST /api/settings/` - Application settings

## Electricity Billing

The system includes comprehensive electricity billing functionality:

### Features
- **Rate Management**: Configurable electricity rate per unit
- **Meter Reading Validation**: Ensures monotonic readings (no negative deltas)
- **Bulk Processing**: Efficient bulk meter reading entry
- **Bill Calculation**: Automatic unit consumption and total calculation
- **Invoice Generation**: PDF invoice generation with detailed breakdown

### Usage
1. Set electricity rate in Settings (`electricity_rate_per_unit`)
2. Record meter readings (bulk or individual)
3. Calculate bills for specific months
4. Generate PDF invoices

### API Example
```bash
# Calculate electricity bill
curl -X POST http://localhost:8000/api/billing/electricity/calc/ \
  -H "Content-Type: application/json" \
  -d '{"room_id": 1, "month": "2024-02"}'

# Create electricity invoice
curl -X POST http://localhost:8000/api/invoices/electricity/ \
  -H "Content-Type: application/json" \
  -d '{"room_id": 1, "month": "2024-02"}'
```

## PDF Generation

The system generates professional PDF invoices using WeasyPrint:

### Features
- **Electricity Invoices**: Detailed consumption breakdown
- **Rent Invoices**: Standard rent invoices
- **Organization Branding**: Customizable company information
- **Automatic Storage**: PDFs saved to media directory

### Usage
1. Generate invoice via API or UI
2. PDF automatically created and stored
3. Download via `/invoices/{id}/pdf/` endpoint

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
make test

# Run specific test categories
python manage.py test core.tests.ElectricityBillingTests
pytest core/tests.py::APITests::test_electricity_bill_calc
```

### Test Coverage
- Unit tests for billing calculations
- API endpoint tests
- HTMX view tests
- Model validation tests
- PDF generation tests

## Deployment

### Production Setup

1. **Environment Configuration**
   ```env
   DEBUG=False
   SECRET_KEY=your-production-secret-key
   DATABASE_URL=postgres://user:password@host:port/dbname
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```

2. **Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Database Migration**
   ```bash
   python manage.py migrate
   ```

4. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

### Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN npm install && npm run build-css-prod

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 style guidelines
- Write tests for new features
- Update documentation as needed
- Use meaningful commit messages

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the test cases for usage examples

## Roadmap

- [ ] Multi-tenant support
- [ ] SMS/WhatsApp notifications
- [ ] Advanced reporting
- [ ] Mobile app
- [ ] Integration with payment gateways
- [ ] Automated rent reminders
- [ ] Maintenance request tracking

# Regalion AML System

سیستم Anti Money Laundering (AML) برای نظارت بر تراکنش‌ها، تشخیص فعالیت‌های مشکوک و گزارش‌دهی به رگولاتور.

## ویژگی‌ها

- ✅ نظارت بر تراکنش‌ها در زمان واقعی
- ✅ محاسبه امتیاز ریسک خودکار
- ✅ تولید هشدار برای تراکنش‌های مشکوک
- ✅ مدیریت هشدارها و workflow بررسی
- ✅ تولید گزارش‌های رگولاتوری (SAR, CTR)
- ✅ لاگ‌گیری کامل برای audit trail

## نصب و راه‌اندازی

### پیش‌نیازها

- Python 3.9+
- PostgreSQL 12+
- Redis (برای Celery - اختیاری)

### راه‌اندازی

1. کلون کردن پروژه:
```bash
git clone <repository-url>
cd Regalion
```

2. ایجاد محیط مجازی:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. نصب وابستگی‌ها:
```bash
cd backend
pip install -r requirements.txt
```

4. تنظیم فایل `.env` (از ریشه پروژه):
```bash
cp .env.example .env
# ویرایش .env و تنظیم مقادیر مناسب
```

5. اجرای migrations:
```bash
python manage.py migrate
```

6. ایجاد superuser:
```bash
python manage.py createsuperuser
```

7. ایجاد قوانین نمونه:
```bash
python manage.py create_sample_rules
```

8. اجرای سرور (به‌صورت پیش‌فرض با تنظیمات development):
```bash
# از ریشه پروژه با Make
make run

# یا از پوشه backend
cd backend && python manage.py runserver
```

برای محیط production از همان پوشه:
```bash
DJANGO_ENV=production python manage.py runserver
```
یا `make run-prod` (از ریشه پروژه).

## ساختار پروژه

```
Regalion/
├── backend/
│   ├── aml/                    # Django app اصلی AML
│   │   ├── models.py           # Customer, Transaction, Alert, RiskScore
│   │   ├── serializers.py      # DRF serializers
│   │   ├── views.py            # API endpoints
│   │   ├── services/           # Business logic
│   │   ├── rules/              # Rule engine
│   │   └── ml/                 # ML models (optional)
│   ├── config/
│   │   ├── settings/           # Django settings (base, development, production)
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   └── urls.py
│   └── requirements.txt
├── Makefile                    # make run, make migrate, make test
├── ROADMAP.md                  # Development roadmap & timeline
└── README.md
```

### Django settings (best practice)

- **Development (default):** `DJANGO_ENV=development` یا مقدار ندادن — DEBUG=True، SQLite مجاز.
- **Production:** `DJANGO_ENV=production` — DEBUG=False، security headers، فقط JSON API.
- تنظیمات مشترک در `config/settings/base.py`؛ مخصوص محیط در `development.py` و `production.py`.

## API Endpoints

### API Authentication (Token)

API requests require authentication. Use **Token Authentication** (DRF):

1. **Obtain a token** (POST with a valid Django user):
   ```bash
   curl -X POST http://localhost:8000/api/auth/token/ \
     -H "Content-Type: application/json" \
     -d '{"username": "your_username", "password": "your_password"}'
   ```
   Response: `{"token": "abc123..."}`

2. **Call API** with the token:
   ```bash
   curl -H "Authorization: Token abc123..." http://localhost:8000/api/customers/
   ```

Create a user first via Django Admin or `python manage.py createsuperuser`. Token is also available in Django Admin: User → Auth token.

**Rate limiting:** Authenticated users 100 req/hour; anonymous 20 req/hour. Health/ready endpoints are not throttled.

**Filtering, search, ordering:** List endpoints support `?search=`, `?ordering=`, and filter fields (e.g. `?status=OPEN`, `?current_risk_level=HIGH`). See API schema at `/api/schema/`.

### Customers
- `GET /api/customers/` - لیست مشتریان
- `POST /api/customers/` - ایجاد مشتری جدید
- `GET /api/customers/{customer_id}/` - جزئیات مشتری
- `GET /api/customers/{customer_id}/risk_scores/` - امتیازهای ریسک مشتری
- `GET /api/customers/{customer_id}/alerts/` - هشدارهای مشتری
- `GET /api/customers/{customer_id}/transactions/` - تراکنش‌های مشتری

### Transactions
- `GET /api/transactions/` - لیست تراکنش‌ها
- `POST /api/transactions/` - ایجاد تراکنش جدید
- `GET /api/transactions/{transaction_id}/` - جزئیات تراکنش
- `POST /api/transactions/monitor/` - نظارت بر تراکنش (body: `{"transaction_id": "..."}`)

### Alerts
- `GET /api/alerts/` - لیست هشدارها
- `GET /api/alerts/{alert_id}/` - جزئیات هشدار
- `POST /api/alerts/{alert_id}/review/` - بررسی هشدار (body: `{"status": "...", "notes": "..."}`)
- `GET /api/alerts/statistics/` - آمار هشدارها
- `GET /api/alerts/open_count/` - تعداد هشدارهای باز

### Rules
- `GET /api/rules/` - لیست قوانین
- `POST /api/rules/` - ایجاد قانون جدید
- `GET /api/rules/{id}/` - جزئیات قانون
- `PUT /api/rules/{id}/` - به‌روزرسانی قانون

### Reports
- `GET /api/reports/` - لیست گزارش‌ها
- `GET /api/reports/{report_id}/` - جزئیات گزارش
- `POST /api/reports/generate/` - تولید گزارش جدید
- `GET /api/reports/{report_id}/download/` - دانلود فایل گزارش
- `POST /api/reports/{report_id}/submit/` - ارسال گزارش به رگولاتور

### Risk Scores
- `GET /api/risk-scores/` - لیست امتیازهای ریسک

### Audit Log (compliance)
- `GET /api/audit-log/` - لیست خواندنی و صفحه‌بندی‌شده رویدادهای audit (فقط خواندن)

## تست

```bash
python manage.py test
```

## ماژول‌های اصلی

### Rule Engine (`aml/rules/aml_rules.py`)
- ارزیابی قوانین AML بر اساس تراکنش‌ها
- پشتیبانی از قوانین: Threshold, Pattern, Behavioral, Geographic
- قوانین قابل تنظیم از طریق دیتابیس

### Risk Scorer (`aml/services/risk_scorer.py`)
- محاسبه امتیاز ریسک برای مشتریان و تراکنش‌ها
- در نظر گیری عوامل مختلف: مبلغ، فرکانس، جغرافیا، تاریخچه، الگوهای رفتاری

### Transaction Monitor (`aml/services/transaction_monitor.py`)
- نظارت بر تراکنش‌ها در زمان واقعی
- اعمال قوانین AML و محاسبه ریسک
- تولید خودکار هشدار برای تراکنش‌های مشکوک

### Alert Generator (`aml/services/alert_generator.py`)
- تولید و مدیریت هشدارها
- اولویت‌بندی و workflow بررسی
- آمار و گزارش‌گیری از هشدارها

### Report Generator (`aml/services/report_generator.py`)
- تولید گزارش‌های رگولاتوری (SAR, CTR)
- خروجی در فرمت‌های JSON, CSV, PDF
- مدیریت ارسال گزارش‌ها به رگولاتور

## لاگ‌گیری و Audit Trail

- تمام درخواست‌های API در فایل `logs/audit_trail.log` ثبت می‌شوند
- لاگ‌های سیستم در فایل `logs/aml_system.log` ذخیره می‌شوند
- Middleware برای ثبت خودکار تمام فعالیت‌ها

## مجوز

این پروژه برای چالش RegMeet طراحی شده است.


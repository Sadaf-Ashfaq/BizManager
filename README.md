1. BizManager
Django-based ERP system for wholesale businesses with role-based portals for Admin, Customers, and Brokers.

2. Tech Stack
- Backend: Django 6.0
- Database: SQLite
- Frontend: Tailwind CSS, Font Awesome
- PDF Generation: ReportLab

3. Features

a. Admin Portal
- Manage Products (KG / Bag units)
- Manage Customers & Brokers
- Create Invoices with live preview
- Auto loading charge: Rs. 10/bag
- Payment tracking: Paid / Partial / Unpaid
- Stock auto-deduct on invoice confirmation
- PDF invoice download
- Reports: Daily / Weekly / Monthly / Yearly
- Broker commission auto-calculation

b. Customer Portal
- View own invoices and payment history
- See outstanding balance
- Edit profile & change password

c. Broker Portal
- View linked sales
- Track commission (Pending / Paid)
- View customers handled
- Edit profile & change password

4. Access URLs
- Admin Login → `/login/` then redirects to `/` (Admin Dashboard)
- Customer Portal → `/my/`
- Broker Portal → `/broker/`

5. Business Logic
- Loading charges: Rs. 10 per bag (auto-calculated)
- Stock: Auto-deducted when invoice is confirmed
- Payment status: Auto-updates from Unpaid → Partial → Paid
- Commission: Auto-created on invoice confirmation based on broker's commission rate
- Invoice number: Auto-generated format `INV-YYYYMMDD-001`

6. Role Access
To give a customer or broker portal access, go to Admin → Customers/Brokers → Click Key icon → Set username & password.

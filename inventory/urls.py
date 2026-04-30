from django.urls import path
from . import views
from . import portal_views

urlpatterns = [

    # ── Smart Login Redirect ──
    path('portal/', portal_views.portal_redirect, name='portal_redirect'),

    # ════════════════════════════════════
    # ADMIN PANEL
    # ════════════════════════════════════

    path('', views.dashboard, name='dashboard'),

    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),

    # Customers
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    path('customers/<int:pk>/assign-login/', views.customer_assign_login, name='customer_assign_login'),
    path('customers/quick-add/', views.customer_quick_add, name='customer_quick_add'),

    # Brokers
    path('brokers/', views.broker_list, name='broker_list'),
    path('brokers/add/', views.broker_create, name='broker_create'),
    path('brokers/<int:pk>/edit/', views.broker_edit, name='broker_edit'),
    path('brokers/<int:pk>/delete/', views.broker_delete, name='broker_delete'),
    path('brokers/<int:pk>/assign-login/', views.broker_assign_login, name='broker_assign_login'),
    path('brokers/quick-add/', views.broker_quick_add, name='broker_quick_add'),

    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/preview/', views.invoice_preview, name='invoice_preview'),
    path('invoices/confirm/', views.invoice_confirm, name='invoice_confirm'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    path('invoices/<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),

    # Payments
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/add/<int:invoice_pk>/', views.payment_add, name='payment_add'),

    # Stock
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/add/', views.stock_add, name='stock_add'),

    # Reports
    path('reports/', views.reports, name='reports'),

    # Commission (Admin)
    path('commissions/', views.commission_list, name='commission_list'),
    path('commissions/<int:pk>/mark-paid/', views.commission_mark_paid, name='commission_mark_paid'),

    # ════════════════════════════════════
    # CUSTOMER PORTAL  →  /my/...
    # ════════════════════════════════════

    path('my/', portal_views.customer_portal_dashboard, name='customer_portal_dashboard'),
    path('my/invoices/', portal_views.customer_portal_invoices, name='customer_portal_invoices'),
    path('my/invoices/<int:pk>/', portal_views.customer_portal_invoice_detail, name='customer_portal_invoice_detail'),
    path('my/payments/', portal_views.customer_portal_payments, name='customer_portal_payments'),
    path('my/outstanding/', portal_views.customer_portal_outstanding, name='customer_portal_outstanding'),
    path('my/profile/', portal_views.customer_portal_profile, name='customer_portal_profile'),

    # ════════════════════════════════════
    # BROKER PORTAL  →  /broker/...
    # ════════════════════════════════════

    path('broker/', portal_views.broker_portal_dashboard, name='broker_portal_dashboard'),
    path('broker/sales/', portal_views.broker_portal_sales, name='broker_portal_sales'),
    path('broker/sales/<int:pk>/', portal_views.broker_portal_sale_detail, name='broker_portal_sale_detail'),
    path('broker/customers/', portal_views.broker_portal_customers, name='broker_portal_customers'),
    path('broker/commission/', portal_views.broker_portal_commission, name='broker_portal_commission'),
    path('broker/profile/', portal_views.broker_portal_profile, name='broker_portal_profile'),
]
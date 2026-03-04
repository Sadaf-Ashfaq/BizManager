from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
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
    path('customers/quick-add/', views.customer_quick_add, name='customer_quick_add'),

    # Brokers
    path('brokers/', views.broker_list, name='broker_list'),
    path('brokers/add/', views.broker_create, name='broker_create'),
    path('brokers/<int:pk>/edit/', views.broker_edit, name='broker_edit'),
    path('brokers/<int:pk>/delete/', views.broker_delete, name='broker_delete'),
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
]
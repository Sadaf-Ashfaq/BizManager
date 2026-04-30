from django.contrib import admin
from .models import (Product, Customer, Broker, Invoice,
                     InvoiceItem, Payment, StockEntry, BrokerCommission)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit', 'bag_weight_kg', 'is_active']
    list_filter = ['unit', 'is_active']
    search_fields = ['name']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'user', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'phone']


@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'commission_rate', 'user', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'phone']


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ['line_total']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'broker',
                    'date', 'grand_total', 'payment_status']
    list_filter = ['payment_status', 'status', 'date']
    search_fields = ['invoice_number', 'customer__name']
    readonly_fields = ['subtotal', 'loading_charges',
                       'grand_total', 'balance_due']
    inlines = [InvoiceItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'date', 'note']
    list_filter = ['date']


@admin.register(StockEntry)
class StockEntryAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'date', 'note']
    list_filter = ['date', 'product']


@admin.register(BrokerCommission)
class BrokerCommissionAdmin(admin.ModelAdmin):
    list_display = ['broker', 'invoice', 'commission_amount', 'is_paid', 'paid_date']
    list_filter = ['is_paid', 'broker']
    search_fields = ['broker__name', 'invoice__invoice_number']
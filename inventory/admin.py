from django.contrib import admin
from .models import Product, Customer, Broker, Invoice, InvoiceItem, Payment, StockEntry


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit', 'bag_weight_kg', 'is_active', 'created_at']
    list_filter = ['unit', 'is_active']
    search_fields = ['name']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'phone']


@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'phone']


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ['line_total']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'broker', 'date', 'grand_total', 'payment_status']
    list_filter = ['payment_status', 'status', 'date']
    search_fields = ['invoice_number', 'customer__name']
    readonly_fields = ['subtotal', 'loading_charges', 'grand_total', 'balance_due']
    inlines = [InvoiceItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'date', 'note']
    list_filter = ['date']
    search_fields = ['invoice__invoice_number', 'invoice__customer__name']


@admin.register(StockEntry)
class StockEntryAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'date', 'note']
    list_filter = ['date', 'product']
    search_fields = ['product__name']
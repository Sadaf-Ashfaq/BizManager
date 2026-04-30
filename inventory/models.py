from django.db import models
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth.models import User


class Product(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('bag', 'Bag'),
    ]
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='kg')
    bag_weight_kg = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Weight per bag in KG (only for bag type)"
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"

    def total_sold_kg(self):
        items = self.invoiceitem_set.filter(invoice__status='confirmed')
        total = 0
        for item in items:
            if self.unit == 'kg':
                total += float(item.quantity)
            else:
                total += float(item.quantity) * float(self.bag_weight_kg or 0)
        return total

    class Meta:
        ordering = ['name']


class Customer(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='customer_profile'
    )
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def total_purchases(self):
        return self.invoice_set.filter(status='confirmed').aggregate(
            total=Sum('grand_total'))['total'] or 0

    def total_paid(self):
        return self.invoice_set.filter(status='confirmed').aggregate(
            total=Sum('amount_paid'))['total'] or 0

    def outstanding_balance(self):
        return float(self.total_purchases()) - float(self.total_paid())

    class Meta:
        ordering = ['name']


class Broker(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='broker_profile'
    )
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Default commission percentage per invoice"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def total_sales(self):
        return self.invoice_set.filter(status='confirmed').aggregate(
            total=Sum('grand_total'))['total'] or 0

    def total_invoices(self):
        return self.invoice_set.filter(status='confirmed').count()

    def total_commission_earned(self):
        return self.commissions.aggregate(
            total=Sum('commission_amount'))['total'] or 0

    def total_commission_paid(self):
        return self.commissions.filter(is_paid=True).aggregate(
            total=Sum('commission_amount'))['total'] or 0

    def total_commission_pending(self):
        return self.commissions.filter(is_paid=False).aggregate(
            total=Sum('commission_amount'))['total'] or 0

    def customers_handled(self):
        return Customer.objects.filter(
            invoice__broker=self,
            invoice__status='confirmed'
        ).distinct()

    class Meta:
        ordering = ['name']


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    broker = models.ForeignKey(Broker, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid'
    )

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loading_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.customer.name}"

    def calculate_totals(self):
        subtotal = 0
        loading_charges = 0
        for item in self.invoiceitem_set.all():
            subtotal += float(item.line_total)
            if item.product.unit == 'bag':
                loading_charges += float(item.quantity) * 10
        self.subtotal = subtotal
        self.loading_charges = loading_charges
        self.grand_total = subtotal + loading_charges
        self.balance_due = self.grand_total - float(self.amount_paid)
        self.save()
        # Auto create commission if broker is set
        if self.broker and self.broker.commission_rate > 0:
            commission_amount = float(self.grand_total) * float(self.broker.commission_rate) / 100
            BrokerCommission.objects.update_or_create(
                invoice=self,
                broker=self.broker,
                defaults={
                    'commission_rate': self.broker.commission_rate,
                    'commission_amount': commission_amount,
                    'is_paid': False,
                }
            )

    def update_payment_status(self):
        if float(self.amount_paid) <= 0:
            self.payment_status = 'unpaid'
        elif float(self.amount_paid) >= float(self.grand_total):
            self.payment_status = 'paid'
        else:
            self.payment_status = 'partial'
        self.balance_due = max(0, float(self.grand_total) - float(self.amount_paid))
        self.save()

    @staticmethod
    def generate_invoice_number():
        from datetime import date
        today = date.today()
        prefix = f"INV-{today.strftime('%Y%m%d')}"
        last = Invoice.objects.filter(invoice_number__startswith=prefix).count()
        return f"{prefix}-{str(last + 1).zfill(3)}"

    class Meta:
        ordering = ['-date', '-created_at']


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.line_total = float(self.quantity) * float(self.price_per_unit)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def loading_charge(self):
        if self.product.unit == 'bag':
            return float(self.quantity) * 10
        return 0


class Payment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    note = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of Rs.{self.amount} for {self.invoice.invoice_number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invoice = self.invoice
        total_paid = invoice.payments.aggregate(total=Sum('amount'))['total'] or 0
        invoice.amount_paid = total_paid
        invoice.update_payment_status()

    class Meta:
        ordering = ['-date']


class StockEntry(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    note = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} on {self.date}"

    class Meta:
        ordering = ['-date']


class BrokerCommission(models.Model):
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE, related_name='commissions')
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name='commission')
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commission: {self.broker.name} — {self.invoice.invoice_number} — Rs.{self.commission_amount}"

    class Meta:
        ordering = ['-created_at']
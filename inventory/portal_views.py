from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from datetime import date
from .models import Customer, Broker, Invoice, InvoiceItem, Payment, BrokerCommission


# ════════════════════════════════════════
# ROLE HELPERS
# ════════════════════════════════════════

def get_user_role(user):
    if not user.is_authenticated:
        return None
    if user.is_staff or user.is_superuser:
        return 'admin'
    try:
        _ = user.customer_profile
        return 'customer'
    except Exception:
        pass
    try:
        _ = user.broker_profile
        return 'broker'
    except Exception:
        pass
    return None


@login_required
def portal_redirect(request):
    role = get_user_role(request.user)
    if role == 'admin':
        return redirect('dashboard')
    elif role == 'customer':
        return redirect('customer_portal_dashboard')
    elif role == 'broker':
        return redirect('broker_portal_dashboard')
    else:
        messages.error(request, 'Your account is not linked to any profile. Contact admin.')
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')


# ════════════════════════════════════════
# CUSTOMER PORTAL
# ════════════════════════════════════════

def customer_login_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        try:
            customer = request.user.customer_profile
        except Exception:
            messages.error(request, 'Access denied.')
            return redirect('portal_redirect')
        return view_func(request, *args, customer=customer, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


@customer_login_required
def customer_portal_dashboard(request, customer):
    invoices = Invoice.objects.filter(customer=customer, status='confirmed')
    total_invoices = invoices.count()
    total_purchases = invoices.aggregate(t=Sum('grand_total'))['t'] or 0
    total_paid = invoices.aggregate(t=Sum('amount_paid'))['t'] or 0
    outstanding = float(total_purchases) - float(total_paid)
    unpaid_invoices = invoices.filter(payment_status__in=['unpaid', 'partial']).order_by('-date')
    recent_invoices = invoices.order_by('-date')[:5]

    context = {
        'customer': customer,
        'total_invoices': total_invoices,
        'total_purchases': total_purchases,
        'total_paid': total_paid,
        'outstanding': outstanding,
        'unpaid_invoices': unpaid_invoices,
        'recent_invoices': recent_invoices,
    }
    return render(request, 'portal/customer/dashboard.html', context)


@customer_login_required
def customer_portal_invoices(request, customer):
    invoices = Invoice.objects.filter(customer=customer, status='confirmed').order_by('-date')
    status_filter = request.GET.get('status', '')
    if status_filter:
        invoices = invoices.filter(payment_status=status_filter)

    return render(request, 'portal/customer/invoices.html', {
        'customer': customer,
        'invoices': invoices,
        'selected_status': status_filter,
    })


@customer_login_required
def customer_portal_invoice_detail(request, pk, customer):
    invoice = get_object_or_404(Invoice, pk=pk, customer=customer, status='confirmed')
    items = invoice.invoiceitem_set.select_related('product').all()
    payments = invoice.payments.all()
    return render(request, 'portal/customer/invoice_detail.html', {
        'customer': customer,
        'invoice': invoice,
        'items': items,
        'payments': payments,
    })


@customer_login_required
def customer_portal_payments(request, customer):
    payments = Payment.objects.filter(
        invoice__customer=customer,
        invoice__status='confirmed'
    ).select_related('invoice').order_by('-date')

    total_paid = payments.aggregate(t=Sum('amount'))['t'] or 0

    return render(request, 'portal/customer/payments.html', {
        'customer': customer,
        'payments': payments,
        'total_paid': total_paid,
    })


@customer_login_required
def customer_portal_outstanding(request, customer):
    invoices = Invoice.objects.filter(
        customer=customer,
        status='confirmed',
        payment_status__in=['unpaid', 'partial']
    ).order_by('-date')

    total_due = invoices.aggregate(t=Sum('balance_due'))['t'] or 0

    return render(request, 'portal/customer/outstanding.html', {
        'customer': customer,
        'invoices': invoices,
        'total_due': total_due,
    })


@customer_login_required
def customer_portal_profile(request, customer):
    if request.method == 'POST':
        customer.phone = request.POST.get('phone', '').strip()
        customer.address = request.POST.get('address', '').strip()
        customer.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('customer_portal_profile')

    return render(request, 'portal/customer/profile.html', {
        'customer': customer,
    })


# ════════════════════════════════════════
# BROKER PORTAL
# ════════════════════════════════════════

def broker_login_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        try:
            broker = request.user.broker_profile
        except Exception:
            messages.error(request, 'Access denied.')
            return redirect('portal_redirect')
        return view_func(request, *args, broker=broker, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


@broker_login_required
def broker_portal_dashboard(request, broker):
    invoices = Invoice.objects.filter(broker=broker, status='confirmed')
    total_invoices = invoices.count()
    total_sales = invoices.aggregate(t=Sum('grand_total'))['t'] or 0
    customers_handled = broker.customers_handled()
    total_customers = customers_handled.count()

    commission_earned = broker.total_commission_earned()
    commission_paid = broker.total_commission_paid()
    commission_pending = broker.total_commission_pending()

    recent_invoices = invoices.select_related('customer').order_by('-date')[:5]

    # Customer-wise breakdown
    customer_breakdown = {}
    for inv in invoices.select_related('customer'):
        c = inv.customer.name
        if c not in customer_breakdown:
            customer_breakdown[c] = {'invoices': 0, 'total': 0}
        customer_breakdown[c]['invoices'] += 1
        customer_breakdown[c]['total'] += float(inv.grand_total)

    context = {
        'broker': broker,
        'total_invoices': total_invoices,
        'total_sales': total_sales,
        'total_customers': total_customers,
        'commission_earned': commission_earned,
        'commission_paid': commission_paid,
        'commission_pending': commission_pending,
        'recent_invoices': recent_invoices,
        'customer_breakdown': customer_breakdown,
    }
    return render(request, 'portal/broker/dashboard.html', context)


@broker_login_required
def broker_portal_sales(request, broker):
    invoices = Invoice.objects.filter(
        broker=broker, status='confirmed'
    ).select_related('customer').order_by('-date')

    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        invoices = invoices.filter(date__gte=date_from)
    if date_to:
        invoices = invoices.filter(date__lte=date_to)

    total_amount = invoices.aggregate(t=Sum('grand_total'))['t'] or 0

    return render(request, 'portal/broker/sales.html', {
        'broker': broker,
        'invoices': invoices,
        'total_amount': total_amount,
        'date_from': date_from,
        'date_to': date_to,
    })


@broker_login_required
def broker_portal_sale_detail(request, pk, broker):
    invoice = get_object_or_404(Invoice, pk=pk, broker=broker, status='confirmed')
    items = invoice.invoiceitem_set.select_related('product').all()
    commission = None
    try:
        commission = invoice.commission
    except Exception:
        pass
    return render(request, 'portal/broker/sale_detail.html', {
        'broker': broker,
        'invoice': invoice,
        'items': items,
        'commission': commission,
    })


@broker_login_required
def broker_portal_customers(request, broker):
    customers = broker.customers_handled().order_by('name')
    # For each customer, calculate their total with this broker
    customer_data = []
    for c in customers:
        inv = Invoice.objects.filter(customer=c, broker=broker, status='confirmed')
        customer_data.append({
            'customer': c,
            'total_invoices': inv.count(),
            'total_amount': inv.aggregate(t=Sum('grand_total'))['t'] or 0,
        })

    return render(request, 'portal/broker/customers.html', {
        'broker': broker,
        'customer_data': customer_data,
    })


@broker_login_required
def broker_portal_commission(request, broker):
    commissions = BrokerCommission.objects.filter(
        broker=broker
    ).select_related('invoice', 'invoice__customer').order_by('-created_at')

    total_earned = broker.total_commission_earned()
    total_paid_comm = broker.total_commission_paid()
    total_pending_comm = broker.total_commission_pending()

    return render(request, 'portal/broker/commission.html', {
        'broker': broker,
        'commissions': commissions,
        'total_earned': total_earned,
        'total_paid': total_paid_comm,
        'total_pending': total_pending_comm,
    })


@broker_login_required
def broker_portal_profile(request, broker):
    if request.method == 'POST':
        broker.phone = request.POST.get('phone', '').strip()
        broker.address = request.POST.get('address', '').strip()
        broker.save()
        messages.success(request, 'Profile updated!')
        return redirect('broker_portal_profile')

    return render(request, 'portal/broker/profile.html', {
        'broker': broker,
    })
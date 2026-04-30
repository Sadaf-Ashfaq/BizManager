from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum
import json
from datetime import date, timedelta

from .models import (Product, Customer, Broker, Invoice, InvoiceItem,
                     Payment, StockEntry, BrokerCommission)


# ─────────────────────────────────────────
# ROLE HELPERS
# ─────────────────────────────────────────
def get_role(user):
    if user.is_staff or user.is_superuser:
        return 'admin'
    if hasattr(user, 'customer_profile'):
        return 'customer'
    if hasattr(user, 'broker_profile'):
        return 'broker'
    return None


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if get_role(request.user) != 'admin':
            return redirect('portal_redirect')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ─────────────────────────────────────────
# PORTAL REDIRECT (smart login redirect)
# ─────────────────────────────────────────
@login_required
def portal_redirect(request):
    role = get_role(request.user)
    if role == 'admin':
        return redirect('dashboard')
    elif role == 'customer':
        return redirect('customer_dashboard')
    elif role == 'broker':
        return redirect('broker_dashboard')
    else:
        messages.error(request, 'Your account is not linked. Contact admin.')
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')


# ─────────────────────────────────────────
# ADMIN DASHBOARD
# ─────────────────────────────────────────
@admin_required
def dashboard(request):
    today = date.today()
    month_start = today.replace(day=1)

    total_customers = Customer.objects.filter(is_active=True).count()
    total_products = Product.objects.filter(is_active=True).count()
    total_brokers = Broker.objects.filter(is_active=True).count()

    total_sales = Invoice.objects.filter(status='confirmed').aggregate(
        total=Sum('grand_total'))['total'] or 0
    monthly_sales = Invoice.objects.filter(
        status='confirmed', date__gte=month_start).aggregate(
        total=Sum('grand_total'))['total'] or 0
    total_due = Invoice.objects.filter(
        status='confirmed',
        payment_status__in=['unpaid', 'partial']).aggregate(
        total=Sum('balance_due'))['total'] or 0
    today_invoices = Invoice.objects.filter(
        status='confirmed', date=today).count()
    recent_invoices = Invoice.objects.filter(
        status='confirmed').select_related('customer')[:5]

    context = {
        'total_customers': total_customers,
        'total_products': total_products,
        'total_brokers': total_brokers,
        'total_sales': total_sales,
        'monthly_sales': monthly_sales,
        'total_due': total_due,
        'today_invoices': today_invoices,
        'recent_invoices': recent_invoices,
    }
    return render(request, 'inventory/dashboard.html', context)


# ─────────────────────────────────────────
# PRODUCTS
# ─────────────────────────────────────────
@admin_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'inventory/product_list.html', {'products': products})


@admin_required
def product_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        unit = request.POST.get('unit', 'kg')
        bag_weight = request.POST.get('bag_weight_kg') or None
        description = request.POST.get('description', '').strip()
        if not name:
            messages.error(request, 'Product name is required.')
            return render(request, 'inventory/product_form.html', {'action': 'Add'})
        Product.objects.create(name=name, unit=unit,
                               bag_weight_kg=bag_weight,
                               description=description)
        messages.success(request, f'Product "{name}" added!')
        return redirect('product_list')
    return render(request, 'inventory/product_form.html', {'action': 'Add'})


@admin_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.name = request.POST.get('name', '').strip()
        product.unit = request.POST.get('unit', 'kg')
        product.bag_weight_kg = request.POST.get('bag_weight_kg') or None
        product.description = request.POST.get('description', '').strip()
        product.is_active = request.POST.get('is_active') == 'on'
        product.save()
        messages.success(request, f'Product "{product.name}" updated!')
        return redirect('product_list')
    return render(request, 'inventory/product_form.html',
                  {'action': 'Edit', 'product': product})


@admin_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted.')
        return redirect('product_list')
    return render(request, 'inventory/confirm_delete.html',
                  {'object': product, 'type': 'Product'})


# ─────────────────────────────────────────
# CUSTOMERS
# ─────────────────────────────────────────
@admin_required
def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'inventory/customer_list.html',
                  {'customers': customers})


@admin_required
def customer_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        if not name:
            messages.error(request, 'Customer name is required.')
            return render(request, 'inventory/customer_form.html',
                          {'action': 'Add'})
        Customer.objects.create(name=name, phone=phone, address=address)
        messages.success(request, f'Customer "{name}" added!')
        return redirect('customer_list')
    return render(request, 'inventory/customer_form.html', {'action': 'Add'})


@admin_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.name = request.POST.get('name', '').strip()
        customer.phone = request.POST.get('phone', '').strip()
        customer.address = request.POST.get('address', '').strip()
        customer.is_active = request.POST.get('is_active') == 'on'
        customer.save()
        messages.success(request, f'Customer "{customer.name}" updated!')
        return redirect('customer_list')
    return render(request, 'inventory/customer_form.html',
                  {'action': 'Edit', 'customer': customer})


@admin_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted.')
        return redirect('customer_list')
    return render(request, 'inventory/confirm_delete.html',
                  {'object': customer, 'type': 'Customer'})


@login_required
def customer_quick_add(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Name required'})
        c = Customer.objects.create(
            name=name,
            phone=data.get('phone', ''),
            address=data.get('address', ''))
        return JsonResponse({'success': True, 'id': c.id, 'name': c.name})
    return JsonResponse({'success': False})


@admin_required
def customer_assign_login(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        if action == 'remove' and customer.user:
            old = customer.user
            customer.user = None
            customer.save()
            old.delete()
            messages.success(request,
                             f'Login removed from {customer.name}')
            return redirect('customer_list')

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        if not username or not password:
            messages.error(request, 'Username and password required.')
            return render(request, 'inventory/assign_login.html',
                          {'object': customer, 'type': 'Customer'})
        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" already taken.')
            return render(request, 'inventory/assign_login.html',
                          {'object': customer, 'type': 'Customer'})
        user = User.objects.create_user(username=username, password=password)
        customer.user = user
        customer.save()
        messages.success(
            request,
            f'Login created for {customer.name} | Username: {username}')
        return redirect('customer_list')
    return render(request, 'inventory/assign_login.html',
                  {'object': customer, 'type': 'Customer'})


# ─────────────────────────────────────────
# BROKERS
# ─────────────────────────────────────────
@admin_required
def broker_list(request):
    brokers = Broker.objects.all()
    return render(request, 'inventory/broker_list.html', {'brokers': brokers})


@admin_required
def broker_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        commission = request.POST.get('commission_rate', 0) or 0
        if not name:
            messages.error(request, 'Broker name is required.')
            return render(request, 'inventory/broker_form.html',
                          {'action': 'Add'})
        Broker.objects.create(name=name, phone=phone, address=address,
                              commission_rate=commission)
        messages.success(request, f'Broker "{name}" added!')
        return redirect('broker_list')
    return render(request, 'inventory/broker_form.html', {'action': 'Add'})


@admin_required
def broker_edit(request, pk):
    broker = get_object_or_404(Broker, pk=pk)
    if request.method == 'POST':
        broker.name = request.POST.get('name', '').strip()
        broker.phone = request.POST.get('phone', '').strip()
        broker.address = request.POST.get('address', '').strip()
        broker.commission_rate = request.POST.get('commission_rate', 0) or 0
        broker.is_active = request.POST.get('is_active') == 'on'
        broker.save()
        messages.success(request, f'Broker "{broker.name}" updated!')
        return redirect('broker_list')
    return render(request, 'inventory/broker_form.html',
                  {'action': 'Edit', 'broker': broker})


@admin_required
def broker_delete(request, pk):
    broker = get_object_or_404(Broker, pk=pk)
    if request.method == 'POST':
        broker.delete()
        messages.success(request, 'Broker deleted.')
        return redirect('broker_list')
    return render(request, 'inventory/confirm_delete.html',
                  {'object': broker, 'type': 'Broker'})


@login_required
def broker_quick_add(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Name required'})
        b = Broker.objects.create(name=name, phone=data.get('phone', ''))
        return JsonResponse({'success': True, 'id': b.id, 'name': b.name})
    return JsonResponse({'success': False})


@admin_required
def broker_assign_login(request, pk):
    broker = get_object_or_404(Broker, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        if action == 'remove' and broker.user:
            old = broker.user
            broker.user = None
            broker.save()
            old.delete()
            messages.success(request, f'Login removed from {broker.name}')
            return redirect('broker_list')

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        if not username or not password:
            messages.error(request, 'Username and password required.')
            return render(request, 'inventory/assign_login.html',
                          {'object': broker, 'type': 'Broker'})
        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" already taken.')
            return render(request, 'inventory/assign_login.html',
                          {'object': broker, 'type': 'Broker'})
        user = User.objects.create_user(username=username, password=password)
        broker.user = user
        broker.save()
        messages.success(
            request,
            f'Login created for {broker.name} | Username: {username}')
        return redirect('broker_list')
    return render(request, 'inventory/assign_login.html',
                  {'object': broker, 'type': 'Broker'})


# ─────────────────────────────────────────
# INVOICES
# ─────────────────────────────────────────
def _parse_items(post):
    total = int(post.get('total_item_count', 0))
    items = []
    for i in range(1, total + 1):
        pid = post.get(f'product_{i}')
        qty = post.get(f'quantity_{i}')
        price = post.get(f'price_{i}')
        if pid and qty and price:
            try:
                product = Product.objects.get(pk=pid)
                q = float(qty)
                p = float(price)
                items.append({
                    'product': product,
                    'product_id': pid,
                    'quantity': q,
                    'price_per_unit': p,
                    'line_total': q * p,
                    'loading_charge': q * 10 if product.unit == 'bag' else 0,
                })
            except (Product.DoesNotExist, ValueError):
                pass
    return items


@admin_required
def invoice_list(request):
    invoices = Invoice.objects.select_related('customer', 'broker').all()
    payment_status = request.GET.get('payment_status', '')
    customer_id = request.GET.get('customer', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if payment_status:
        invoices = invoices.filter(payment_status=payment_status)
    if customer_id:
        invoices = invoices.filter(customer_id=customer_id)
    if date_from:
        invoices = invoices.filter(date__gte=date_from)
    if date_to:
        invoices = invoices.filter(date__lte=date_to)

    customers = Customer.objects.filter(is_active=True)
    return render(request, 'inventory/invoice_list.html', {
        'invoices': invoices,
        'customers': customers,
        'selected_payment_status': payment_status,
        'selected_customer': customer_id,
    })


@admin_required
def invoice_create(request):
    if request.method == 'POST':
        request.session['invoice_draft'] = dict(request.POST)
        return redirect('invoice_preview')

    products = Product.objects.filter(is_active=True)
    customers = Customer.objects.filter(is_active=True)
    brokers = Broker.objects.filter(is_active=True)
    products_data = list(products.values('id', 'name', 'unit', 'bag_weight_kg'))

    return render(request, 'inventory/invoice_create.html', {
        'products': products,
        'customers': customers,
        'brokers': brokers,
        'products_data': json.dumps(products_data, default=str),
        'today': date.today(),
    })


@admin_required
def invoice_preview(request):
    draft = request.session.get('invoice_draft')
    if not draft:
        messages.error(request, 'No draft found.')
        return redirect('invoice_create')

    post = {k: v[0] if isinstance(v, list) else v for k, v in draft.items()}
    customer_id = post.get('customer')
    broker_id = post.get('broker') or None
    inv_date = post.get('date', str(date.today()))
    notes = post.get('notes', '')

    try:
        customer = Customer.objects.get(pk=customer_id)
    except Customer.DoesNotExist:
        messages.error(request, 'Invalid customer.')
        return redirect('invoice_create')

    broker = None
    if broker_id:
        try:
            broker = Broker.objects.get(pk=broker_id)
        except Broker.DoesNotExist:
            pass

    items = _parse_items(post)
    if not items:
        messages.error(request, 'Add at least one product.')
        return redirect('invoice_create')

    subtotal = sum(i['line_total'] for i in items)
    loading = sum(i['loading_charge'] for i in items)
    grand_total = subtotal + loading

    return render(request, 'inventory/invoice_preview.html', {
        'customer': customer,
        'broker': broker,
        'inv_date': inv_date,
        'notes': notes,
        'items': items,
        'subtotal': subtotal,
        'loading_charges': loading,
        'grand_total': grand_total,
    })


@admin_required
def invoice_confirm(request):
    if request.method != 'POST':
        return redirect('invoice_create')

    draft = request.session.get('invoice_draft')
    if not draft:
        messages.error(request, 'Session expired.')
        return redirect('invoice_create')

    post = {k: v[0] if isinstance(v, list) else v for k, v in draft.items()}
    customer_id = post.get('customer')
    broker_id = post.get('broker') or None
    inv_date = post.get('date', str(date.today()))
    notes = post.get('notes', '')

    try:
        customer = Customer.objects.get(pk=customer_id)
    except Customer.DoesNotExist:
        messages.error(request, 'Invalid customer.')
        return redirect('invoice_create')

    items = _parse_items(post)
    if not items:
        messages.error(request, 'No valid items.')
        return redirect('invoice_create')

    invoice = Invoice.objects.create(
        invoice_number=Invoice.generate_invoice_number(),
        customer=customer,
        broker_id=broker_id,
        date=inv_date,
        notes=notes,
        status='confirmed'
    )

    for item in items:
        InvoiceItem.objects.create(
            invoice=invoice,
            product=item['product'],
            quantity=item['quantity'],
            price_per_unit=item['price_per_unit'],
        )
        # Auto stock deduct
        StockEntry.objects.create(
            product=item['product'],
            quantity=-item['quantity'],
            date=inv_date,
            note=f'Auto-deducted: Invoice #{invoice.invoice_number}'
        )

    invoice.calculate_totals()

    # Auto-create broker commission
    if invoice.broker and invoice.broker.commission_rate > 0:
        commission_amt = float(invoice.grand_total) * float(
            invoice.broker.commission_rate) / 100
        BrokerCommission.objects.create(
            broker=invoice.broker,
            invoice=invoice,
            commission_rate=invoice.broker.commission_rate,
            commission_amount=commission_amt
        )


    del request.session['invoice_draft']
    messages.success(
        request, f'Invoice #{invoice.invoice_number} created!')
    return redirect('invoice_detail', pk=invoice.pk)


@admin_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.invoiceitem_set.select_related('product').all()
    payments = invoice.payments.all()
    commission = getattr(invoice, 'commission', None)
    return render(request, 'inventory/invoice_detail.html', {
        'invoice': invoice,
        'items': items,
        'payments': payments,
        'commission': commission,
    })


@admin_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, 'Invoice deleted.')
        return redirect('invoice_list')
    return render(request, 'inventory/confirm_delete.html',
                  {'object': invoice, 'type': 'Invoice'})


@admin_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.invoiceitem_set.select_related('product').all()
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import (SimpleDocTemplate, Table,
                                         TableStyle, Paragraph, Spacer)
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=1.5*cm, leftMargin=1.5*cm,
                                topMargin=1.5*cm, bottomMargin=1.5*cm)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            'title', fontSize=18, fontName='Helvetica-Bold',
            spaceAfter=4, textColor=colors.HexColor('#1e3a8a'))
        sub_style = ParagraphStyle(
            'sub', fontSize=9, textColor=colors.gray, spaceAfter=2)

        story.append(Paragraph("BizManager", title_style))
        story.append(Paragraph("Business Management System", sub_style))
        story.append(Spacer(1, 0.3*cm))

        info_data = [
            ['Invoice #:', invoice.invoice_number,
             'Date:', str(invoice.date)],
            ['Customer:', invoice.customer.name,
             'Broker:', invoice.broker.name if invoice.broker else '—'],
            ['Status:', invoice.get_payment_status_display(), '', ''],
        ]
        info_table = Table(info_data,
                           colWidths=[3*cm, 7*cm, 3*cm, 5*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#1e40af')),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.4*cm))

        item_data = [['Product', 'Unit', 'Qty',
                      'Price/Unit', 'Loading', 'Total']]
        for item in items:
            loading = item.quantity * 10 if item.product.unit == 'bag' else 0
            item_data.append([
                item.product.name,
                item.product.get_unit_display(),
                str(item.quantity),
                f'Rs. {item.price_per_unit:,.2f}',
                f'Rs. {loading:,.0f}' if loading else '—',
                f'Rs. {item.line_total:,.2f}',
            ])

        n = len(items)
        item_data.append(['', '', '', '', 'Subtotal:',
                          f'Rs. {invoice.subtotal:,.2f}'])
        item_data.append(['', '', '', '', 'Loading:',
                          f'Rs. {invoice.loading_charges:,.2f}'])
        item_data.append(['', '', '', '', 'Grand Total:',
                          f'Rs. {invoice.grand_total:,.2f}'])
        item_data.append(['', '', '', '', 'Paid:',
                          f'Rs. {invoice.amount_paid:,.2f}'])
        item_data.append(['', '', '', '', 'Balance Due:',
                          f'Rs. {invoice.balance_due:,.2f}'])

        col_widths = [5.5*cm, 2*cm, 2*cm, 3.5*cm, 2.5*cm, 3.5*cm]
        item_table = Table(item_data, colWidths=col_widths)
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, n),
             [colors.white, colors.HexColor('#eff6ff')]),
            ('GRID', (0, 0), (-1, n), 0.3, colors.HexColor('#e2e8f0')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('FONTNAME', (4, n+1), (4, n+4), 'Helvetica-Bold'),
            ('TEXTCOLOR', (5, n+3), (5, n+3), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (5, n+4), (5, n+4), colors.HexColor('#dc2626')),
            ('LINEABOVE', (4, n+3), (5, n+3), 1,
             colors.HexColor('#1e40af')),
        ]))
        story.append(item_table)
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(
            "Thank you for your business!",
            ParagraphStyle('footer', fontSize=8, textColor=colors.gray,
                           alignment=TA_CENTER)))

        doc.build(story)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"')
        return response
    except ImportError:
        messages.error(request, 'ReportLab not installed.')
        return redirect('invoice_detail', pk=pk)


# ─────────────────────────────────────────
# PAYMENTS
# ─────────────────────────────────────────
@admin_required
def payment_list(request):
    payments = Payment.objects.select_related(
        'invoice', 'invoice__customer').all()
    return render(request, 'inventory/payment_list.html',
                  {'payments': payments})


@admin_required
def payment_add(request, invoice_pk):
    invoice = get_object_or_404(Invoice, pk=invoice_pk)
    if request.method == 'POST':
        amount = request.POST.get('amount', 0)
        pay_date = request.POST.get('date', date.today())
        note = request.POST.get('note', '')
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, 'Enter a valid amount.')
            return redirect('payment_add', invoice_pk=invoice_pk)
        Payment.objects.create(
            invoice=invoice, amount=amount, date=pay_date, note=note)
        messages.success(request, f'Payment of Rs. {amount:,.0f} recorded!')
        return redirect('invoice_detail', pk=invoice_pk)
    return render(request, 'inventory/payment_form.html',
                  {'invoice': invoice, 'today': date.today()})


# ─────────────────────────────────────────
# BROKER COMMISSION (Admin)
# ─────────────────────────────────────────
@admin_required
def commission_list(request):
    commissions = BrokerCommission.objects.select_related(
        'broker', 'invoice').all()
    total_pending = commissions.filter(status='pending').aggregate(
        total=Sum('amount'))['total'] or 0
    total_paid = commissions.filter(status='paid').aggregate(
        total=Sum('amount'))['total'] or 0
    return render(request, 'inventory/commission_list.html', {
        'commissions': commissions,
        'total_pending': total_pending,
        'total_paid': total_paid,
    })


@admin_required
def commission_mark_paid(request, pk):
    commission = get_object_or_404(BrokerCommission, pk=pk)
    if request.method == 'POST':
        commission.is_paid = True
        commission.paid_date = date.today()
        commission.note = request.POST.get('note', '')
        commission.save()
        messages.success(
            request,
            f'Commission marked paid for {commission.broker.name}')
        return redirect('commission_list')
    return render(request, 'inventory/commission_mark_paid.html',
                  {'commission': commission})


# ─────────────────────────────────────────
# STOCK
# ─────────────────────────────────────────
@admin_required
def stock_list(request):
    products = Product.objects.filter(is_active=True)
    stock_data = []
    for product in products:
        from django.db.models import Sum as S
        total_in = StockEntry.objects.filter(
            product=product, quantity__gt=0).aggregate(
            total=S('quantity'))['total'] or 0
        total_out = StockEntry.objects.filter(
            product=product, quantity__lt=0).aggregate(
            total=S('quantity'))['total'] or 0
        net = float(total_in) + float(total_out)
        stock_data.append({
            'product': product,
            'total_in': float(total_in),
            'total_sold': abs(float(total_out)),
            'remaining': max(0, net),
        })
    return render(request, 'inventory/stock_list.html',
                  {'stock_data': stock_data})


@admin_required
def stock_add(request):
    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity = request.POST.get('quantity')
        entry_date = request.POST.get('date', date.today())
        note = request.POST.get('note', '')
        if not product_id or not quantity:
            messages.error(request, 'Product and quantity required.')
            return redirect('stock_add')
        StockEntry.objects.create(
            product_id=product_id,
            quantity=float(quantity),
            date=entry_date,
            note=note)
        messages.success(request, 'Stock entry added!')
        return redirect('stock_list')
    products = Product.objects.filter(is_active=True)
    return render(request, 'inventory/stock_form.html',
                  {'products': products, 'today': date.today()})


# ─────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────
@admin_required
def reports(request):
    period = request.GET.get('period', 'monthly')
    today = date.today()
    period_map = {
        'daily': today,
        'weekly': today - timedelta(days=7),
        '15days': today - timedelta(days=15),
        'monthly': today - timedelta(days=30),
        '6months': today - timedelta(days=180),
        'yearly': today - timedelta(days=365),
    }
    from_date = period_map.get(period, today - timedelta(days=30))
    invoices = Invoice.objects.filter(
        status='confirmed', date__gte=from_date)

    total_revenue = invoices.aggregate(
        total=Sum('grand_total'))['total'] or 0
    total_collected = invoices.aggregate(
        total=Sum('amount_paid'))['total'] or 0
    total_pending = invoices.aggregate(
        total=Sum('balance_due'))['total'] or 0
    total_invoices = invoices.count()

    product_report = {}
    for item in InvoiceItem.objects.filter(
            invoice__in=invoices).select_related('product'):
        p = item.product.name
        if p not in product_report:
            product_report[p] = {
                'qty': 0, 'total': 0, 'unit': item.product.unit}
        product_report[p]['qty'] += float(item.quantity)
        product_report[p]['total'] += float(item.line_total)

    customer_report = {}
    for inv in invoices.select_related('customer'):
        c = inv.customer.name
        if c not in customer_report:
            customer_report[c] = {'invoices': 0, 'total': 0, 'paid': 0}
        customer_report[c]['invoices'] += 1
        customer_report[c]['total'] += float(inv.grand_total)
        customer_report[c]['paid'] += float(inv.amount_paid)

    broker_report = {}
    for inv in invoices.filter(
            broker__isnull=False).select_related('broker'):
        b = inv.broker.name
        if b not in broker_report:
            broker_report[b] = {'invoices': 0, 'total': 0, 'commission': 0}
        broker_report[b]['invoices'] += 1
        broker_report[b]['total'] += float(inv.grand_total)
        broker_report[b]['commission'] += inv.broker_commission()

    return render(request, 'inventory/reports.html', {
        'period': period,
        'total_revenue': total_revenue,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'total_invoices': total_invoices,
        'product_report': product_report,
        'customer_report': customer_report,
        'broker_report': broker_report,
    })


# ========================
# COMMISSION (ADMIN)
# ========================
@login_required
def commission_list(request):
    commissions = BrokerCommission.objects.select_related(
        'broker', 'invoice', 'invoice__customer'
    ).all()

    broker_filter = request.GET.get('broker', '')
    paid_filter = request.GET.get('paid', '')
    if broker_filter:
        commissions = commissions.filter(broker_id=broker_filter)
    if paid_filter == 'paid':
        commissions = commissions.filter(is_paid=True)
    elif paid_filter == 'unpaid':
        commissions = commissions.filter(is_paid=False)

    brokers = Broker.objects.filter(is_active=True)
    total_earned = commissions.aggregate(t=Sum('commission_amount'))['t'] or 0
    total_paid_c = commissions.filter(is_paid=True).aggregate(t=Sum('commission_amount'))['t'] or 0
    total_pending_c = commissions.filter(is_paid=False).aggregate(t=Sum('commission_amount'))['t'] or 0

    context = {
        'commissions': commissions,
        'brokers': brokers,
        'total_earned': total_earned,
        'total_paid': total_paid_c,
        'total_pending': total_pending_c,
        'selected_broker': broker_filter,
        'selected_paid': paid_filter,
    }
    return render(request, 'inventory/commission_list.html', context)


@login_required
def commission_mark_paid(request, pk):
    commission = get_object_or_404(BrokerCommission, pk=pk)
    if request.method == 'POST':
        commission.is_paid = True
        commission.paid_date = date.today()
        commission.note = request.POST.get('note', '')
        commission.save()
        messages.success(request, f'Commission of Rs. {commission.commission_amount} marked as paid!')
        return redirect('commission_list')
    return render(request, 'inventory/commission_mark_paid.html', {'commission': commission})
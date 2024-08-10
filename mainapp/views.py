from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from mainapp.forms import SignupForm, AddMoneyForm, OrderForm
from .models import Profile, Order, Transaction, MatchOrder, CancelOrder, Category, SubCategory, Event,  SettledEvent
from decimal import Decimal
import logging
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum




logger = logging.getLogger(__name__)

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data.get('password'))
            user.save()
            login(request, user)
            return redirect('index')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def index_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()
    events = Event.objects.all()
    
    
            
            
    context = {
        'categories': categories,
        'subcategories': subcategories,
        'events': events,
        'profile':profile,
        
    }
    return render(request, 'index.html', context)


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def lending_view(request):
    return render(request, 'lending.html')

@login_required
def dashboard(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=request.user)
    matchorders = MatchOrder.objects.filter(user=request.user)
    cancelorders = CancelOrder.objects.filter(user=request.user)
    
    return render(request, 'dashboard.html', {'profile': profile, 'orders': orders, 'matchorders': matchorders, 'cancelorders': cancelorders})

@login_required
def add_money(request):
    if request.method == 'POST':
        form = AddMoneyForm(request.POST)
        if form.is_valid():
            amount = Decimal(form.cleaned_data['amount'])  # Ensure amount is Decimal
            profile, created = Profile.objects.get_or_create(user=request.user)
            profile.balance = Decimal(profile.balance or '0.00')  # Ensure balance is Decimal
            profile.balance += amount  # Perform addition with Decimal
            profile.save()
            Transaction.objects.create(user=request.user, profile=profile, amount=amount, transaction_type='credit')
            return redirect('dashboard')
    else:
        form = AddMoneyForm()
    return render(request, 'addmoney.html', {'form': form})

@login_required
def place_order(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user

            # Get cleaned data from the form
            quantity = form.cleaned_data['quantity']
            price_per_quantity = form.cleaned_data['price_per_quantity']

            # Set total_price based on cleaned_data
            order.total_price = quantity * price_per_quantity

            profile, created = Profile.objects.get_or_create(user=request.user)
            profile.balance = Decimal(profile.balance or '0.00')  # Ensure it's a Decimal

            logger.debug(f"User: {request.user}, Profile balance: {profile.balance}, Order total price: {order.total_price}")

            if profile.balance >= order.total_price:
                profile.balance -= order.total_price
                profile.save()
                Transaction.objects.create(user=request.user, profile=profile, amount=order.total_price, transaction_type='debit')
                order.save()
                match_order(order)
                return redirect('dashboard')
            else:
                form.add_error(None, 'Insufficient balance')
        else:
            logger.debug(f"Form errors: {form.errors}")
    else:
        form = OrderForm()

    return render(request, 'placeorder.html', {'form': form})

@login_required
def match_order(order):
    # Define the price matching logic based on given patterns
    match_logic = {
        Decimal('9.00'): Decimal('1.00'),
        Decimal('8.00'): Decimal('2.00'),
        Decimal('7.00'): Decimal('3.00'),
        Decimal('6.00'): Decimal('4.00'),
        Decimal('5.00'): Decimal('5.00'),
        Decimal('4.00'): Decimal('6.00'),
        Decimal('3.00'): Decimal('7.00'),
        Decimal('2.00'): Decimal('8.00'),
        Decimal('1.00'): Decimal('9.00'),
    }

    order_price_per_quantity = Decimal(order.price_per_quantity)
    order_quantity = Decimal(order.quantity)
    order_matched_quantity = Decimal(order.matched_quantity)

    opposite_response = 'yes' if order.response == 'no' else 'no'
    
    # Filter for opposite response, matching event, pending status, and exclude same user
    opposite_orders = Order.objects.filter(
        event=order.event,
        response=opposite_response,
        status='pending'
    ).exclude(user=order.user).order_by('timestamp')  # Exclude orders from the same user and sort by timestamp, earliest first

    for opposite_order in opposite_orders:
        if order_quantity > 0 and opposite_order.quantity > 0:
            opposite_order_price_per_quantity = Decimal(opposite_order.price_per_quantity)
            required_opposite_price = match_logic.get(order_price_per_quantity, None)
            
            if required_opposite_price != opposite_order_price_per_quantity:
                continue  # Skip if price_per_quantity does not match
            
            # Determine the quantity that can be matched
            match_quantity = min(order_quantity, opposite_order.quantity)
            
            # Calculate the total match price for the current match
            total_match_price = Decimal(match_quantity) * order_price_per_quantity
            
            # Update quantities
            order_quantity -= match_quantity
            opposite_order.quantity -= match_quantity
            order_matched_quantity += match_quantity
            opposite_order.matched_quantity += match_quantity
            
            # Save changes
            order.quantity = order_quantity
            order.matched_quantity = order_matched_quantity
            order.save()
            
            opposite_order.save()
            
            # Check for existing entries in MatchOrder and update or create a new one
            match_order, created = MatchOrder.objects.get_or_create(
                user=order.user,
                event=order.event,
                response=order.response,
                price_per_quantity=order_price_per_quantity,
                defaults={'match_quantity': match_quantity, 'total_match_price': total_match_price}
            )
            if not created:
                match_order.match_quantity += match_quantity
                match_order.total_match_price += total_match_price
                match_order.save()
            
            # Check for existing entries in MatchOrder for the opposite order
            opposite_match_order, created = MatchOrder.objects.get_or_create(
                user=opposite_order.user,
                event=opposite_order.event,
                response=opposite_response,
                price_per_quantity=opposite_order_price_per_quantity,
                defaults={'match_quantity': match_quantity, 'total_match_price': total_match_price}
            )
            if not created:
                opposite_match_order.match_quantity += match_quantity
                opposite_match_order.total_match_price += total_match_price
                opposite_match_order.save()

            # Mark opposite order as completed if fully matched
            if opposite_order.quantity == 0:
                opposite_order.status = 'completed'
                opposite_order.save()
                opposite_order.delete()  # Remove the fully matched opposite order from the Order table
                
            # If the current order is fully matched, mark it as completed and delete it
            if order_quantity == 0:
                order.status = 'completed'
                order.save()
                order.delete()  # Remove the fully matched order from the Order table
                break
    
    # If there is still quantity left, the current order remains pending
    if order_quantity > 0:
        order.status = 'pending'
        order.save()
    else:
        order.status = 'completed'
        order.save()
        order.delete()  # Ensure the completed order is removed from the Order table


# @login_required
# def cancel_order(request, order_id):
#     try:
#         # Retrieve the order and ensure it's associated with the current user
#         order = get_object_or_404(Order, id=order_id, user=request.user)

#         # Check if the order is still pending
#         if order.status == 'pending':
#             # Refund the order amount to the user's balance
#             profile = get_object_or_404(Profile, user=request.user)
#             profile.balance = Decimal(profile.balance or '0.00')  # Ensure it's a Decimal
#             profile.balance += order.total_price  # Ensure total_price is Decimal
#             profile.save()

#             # Record the transaction
#             Transaction.objects.create(
#                 user=request.user,
#                 profile=profile,
#                 amount=order.total_price,
#                 transaction_type='refund'
#             )

#             # Mark the order as cancelled
#             order.status = 'cancelled'
#             order.delete()

#             # Save the cancelled order in the CancelOrder table
#             CancelOrder.objects.create(
#                 user=request.user,
#                 event=order.event,
#                 response='yes',  # or set it based on your logic
#                 cancel_quantity=order.quantity,
#                 price_per_quantity=order.price_per_quantity,
#                 total_cancel_price=order.total_price
#             )

#             messages.success(request, 'Order cancelled successfully.')
#         else:
#             messages.error(request, 'Only pending orders can be cancelled.')

#     except ObjectDoesNotExist:
#         messages.error(request, 'Order does not exist.')

#     return redirect('dashboard')

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib import messages

@login_required
def cancel_order(request, order_id):
    if request.method == 'POST':  # Ensure this view only handles POST requests
        try:
            # Retrieve the order and ensure it's associated with the current user
            order = get_object_or_404(Order, id=order_id, user=request.user)

            # Check if the order is still pending
            if order.status == 'pending':
                # Refund the order amount to the user's balance
                profile = get_object_or_404(Profile, user=request.user)
                profile.balance = Decimal(profile.balance or '0.00')  # Ensure it's a Decimal
                profile.balance += order.total_price  # Ensure total_price is Decimal
                profile.save()

                # Record the transaction
                Transaction.objects.create(
                    user=request.user,
                    profile=profile,
                    amount=order.total_price,
                    transaction_type='refund'
                )

                # Mark the order as cancelled
                order.status = 'cancelled'
                order.delete()

                # Save the cancelled order in the CancelOrder table
                CancelOrder.objects.create(
                    user=request.user,
                    event=order.event,
                    response='yes',  # or set it based on your logic
                    cancel_quantity=order.quantity,
                    price_per_quantity=order.price_per_quantity,
                    total_cancel_price=order.total_price
                )

                response = {
                    'status': 'success',
                    'message': 'Order cancelled successfully.'
                }
            else:
                response = {
                    'status': 'error',
                    'message': 'Only pending orders can be cancelled.'
                }

        except ObjectDoesNotExist:
            response = {
                'status': 'error',
                'message': 'Order does not exist.'
            }

        return JsonResponse(response)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})






@login_required
@user_passes_test(lambda u: u.is_superuser)
def settle_event(request, event_id, settle_response):
    event = get_object_or_404(Event, id=event_id)
    
    if settle_response not in ['yes', 'no']:
        messages.error(request, 'Invalid settlement response.')
        return redirect('dashboard')
    
    event.response = settle_response
    event.save()

    match_orders = MatchOrder.objects.filter(event=event, response=settle_response)
    
    for match_order in match_orders:
        user_profile = get_object_or_404(Profile, user=match_order.user)
        user_profile.balance = Decimal(user_profile.balance or '0.00')
        credit_amount = Decimal(match_order.match_quantity * 10)
        user_profile.balance += credit_amount
        user_profile.save()

        Transaction.objects.create(
            user=match_order.user,
            profile=user_profile,
            amount=credit_amount,
            transaction_type='credit'
        )

    # Create an entry in SettledEvent
    SettledEvent.objects.create(event=event, response=settle_response)

    messages.success(request, 'event settled successfully.')
    return redirect('dashboard')



@csrf_exempt
def fetch_order_data(request):
    response_type = request.GET.get('response_type', None)
    
    # Filter based on response_type
    if response_type == 'yes':
        orders = Order.objects.filter(response='no')
    elif response_type == 'no':
        orders = Order.objects.filter(response='yes')
    else:
        orders = Order.objects.all()
    
    # Define the mapping for price_per_quantity
    price_mapping = {
        1: 9,
        2: 8,
        3: 7,
        4: 6,
        5: 4,
        6: 4,
        7: 3,
        8: 2,
        9: 1
    }
    
    # Aggregate orders by price_per_quantity and sum quantities
    aggregated_data = orders.values('price_per_quantity').annotate(
        total_quantity=Sum('quantity')
    )

    # Apply the price mapping
    mapped_data = [
        {
            'price_per_quantity': price_mapping.get(entry['price_per_quantity'], entry['price_per_quantity']),
            'quantity': entry['total_quantity']
        }
        for entry in aggregated_data
    ]
    
    # Sort by quantity in descending order and take the top 5
    sorted_data = sorted(mapped_data, key=lambda x: x['quantity'], reverse=True)[:5]
    
    # Format the response data
    data = [
        {
            'price_per_quantity': str(item['price_per_quantity']),
            'quantity': item['quantity']
        }
        for item in sorted_data
    ]
    
    return JsonResponse(data, safe=False)






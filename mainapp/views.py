from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from mainapp.forms import SignupForm, AddMoneyForm, OrderForm
from .models import Profile, Order, Transaction, MatchOrder, CancelOrder, Category, SubCategory, Event,  SettledEvent, OrderStatus, ClosedEvent
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

def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')  # Redirect to index if the user is already logged in

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()  # Ensure your form has a method to get the user
            auth_login(request, user)  # Use auth_login for logging in the user
            return redirect('index')  # Redirect to index after successful login
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


@login_required
def index_view(request):
    # Ensure profile exists or create it if not
    profile, created = Profile.objects.get_or_create(user=request.user)

    # Fetch categories, subcategories, and events
    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()
    events = Event.objects.all()

    # Fetch orders for the current user
    orders = Order.objects.filter(user=request.user)

    price_per_quantity_yes = defaultdict(list)
    price_per_quantity_no = defaultdict(list)

    # Populate the dictionaries with price per quantity values
    for order in orders:
        if order.response == 'yes':
            price_per_quantity_yes[order.event.id].append(order.price_per_quantity)
        elif order.response == 'no':
            price_per_quantity_no[order.event.id].append(order.price_per_quantity)

    # Find the maximum price per quantity for each event ID
    max_price_per_quantity_yes = {event_id: max(prices, default=None) for event_id, prices in price_per_quantity_yes.items()}
    max_price_per_quantity_no = {event_id: max(prices, default=None) for event_id, prices in price_per_quantity_no.items()}
    
    context = {
        'categories': categories,
        'subcategories': subcategories,
        'events': events,
        'profile': profile,
        'max_price_per_quantity_yes': max_price_per_quantity_yes,
        'max_price_per_quantity_no': max_price_per_quantity_no        
    }

    return render(request, 'index.html', context)




def lending(request):
    if request.user.is_authenticated:
        return redirect('index')
    return render(request, 'lending.html')

def profile(request):
    
    return render(request, 'profile.html')

def event_active(request, event_id):
    # Fetch the specific event
    event = get_object_or_404(Event, id=event_id)
    
    
    # Fetch orders related to the event
    orders = Order.objects.filter(event=event,user=request.user)

    # Fetch matched orders related to the event
    match_orders = MatchOrder.objects.filter(event=event, user=request.user)

    # Fetch canceled orders related to the event
    cancel_orders = CancelOrder.objects.filter(event=event, user=request.user)
    
    # Render the event_active.html template with the event and grouped events data
    return render(request, 'event_active.html', {
        'event': event,
        'orders': orders,
        'match_orders': match_orders,
        'cancel_orders': cancel_orders,
    })

def event_closed(request, event_id):
    # Fetch the event object or return a 404 error if not found
    event = get_object_or_404(Event, id=event_id)
    
    # Add any additional logic if necessary, e.g., fetching related data or checking conditions
    
    # Context to pass to the template
    context = {
        'event': event,
        # Add more context variables here as needed
    }
    
    # Render the template with the provided context
    return render(request, 'event_closed.html', context)


from collections import defaultdict
def portfolio(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=request.user)
    matchorders = MatchOrder.objects.filter(user=request.user)
    cancelorders = CancelOrder.objects.filter(user=request.user)
    closedevents = ClosedEvent.objects.filter(user=request.user)

    grouped_events = defaultdict(lambda: {'orders': [], 'matchorders': [], 'cancelorders': [], 'total_match_price': 0})
    
    total_investment = 0
    
    for order in orders:
        grouped_events[order.event]['orders'].append(order)
    
    for matchorder in matchorders:
        grouped_events[matchorder.event]['matchorders'].append(matchorder)
        grouped_events[matchorder.event]['total_match_price'] += matchorder.total_match_price
        total_investment += matchorder.total_match_price
    
    for cancelorder in cancelorders:
        grouped_events[cancelorder.event]['cancelorders'].append(cancelorder)

    return render(request, 'portfolio.html', {
        'profile': profile, 
        'grouped_events': dict(grouped_events),
        'cancelorders': cancelorders,
        'closedevents': closedevents,
        'total_investment': total_investment
    })
    
@login_required
def dashboard(request):
    profile = Profile.objects.get(user=request.user)
    return render(request, 'dashboard.html', {'profile': profile})


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

                # Create or update OrderStatus object
                order_status, created = OrderStatus.objects.update_or_create(
                    user=order.user,
                    event=order.event,
                    defaults={
                        'response': order.response,
                        'quantity': order.quantity,
                        'price_per_quantity': order.price_per_quantity,
                        'total_price': order.total_price,
                        'matched_quantity': order.matched_quantity,
                        'cancelled_quantity': 0,  # Initialize cancelled_quantity to 0
                        'status': order.status,
                        'timestamp': order.timestamp
                    }
                )

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
            
            # Update OrderStatus object
            OrderStatus.objects.filter(
                user=order.user,
                event=order.event
            ).update(
                matched_quantity=order_matched_quantity,
                status='partial' if order_quantity > 0 else 'matched'
            )
            
            # Update OrderStatus for the opposite order
            OrderStatus.objects.filter(
                user=opposite_order.user,
                event=opposite_order.event
            ).update(
                matched_quantity=opposite_order.matched_quantity,
                status='partial' if opposite_order.quantity > 0 else 'matched'
            )

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

@login_required
def cancel_order(request, order_id):
    if request.method == 'POST':
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

                # Update the OrderStatus object
                order_status = OrderStatus.objects.filter(
                    user=order.user,
                    event=order.event
                ).first()

                if order_status:
                    order_status.cancelled_quantity += order.quantity
                    order_status.status = 'cancelled'
                    order_status.save()
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'OrderStatus does not exist.'
                    })

                # Save the cancelled order in the CancelOrder table
                CancelOrder.objects.create(
                    user=request.user,
                    event=order.event,
                    response=order.response,
                    cancel_quantity=order.quantity,
                    price_per_quantity=order.price_per_quantity,
                    total_cancel_price=order.total_price
                )

                # Delete the order record
                order.delete()

                return JsonResponse({
                    'status': 'success',
                    'message': 'Order cancelled and deleted successfully.'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Only pending orders can be cancelled.'
                })

        except ObjectDoesNotExist as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Object does not exist: {str(e)}'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'An error occurred: {str(e)}'
            })

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

    # Create an entry in SettledEvent first
    settled_event = SettledEvent.objects.create(event=event, response=settle_response)

    # Filter match orders related to the event
    match_orders = MatchOrder.objects.filter(event=event)
    
    for match_order in match_orders:
        user_profile = get_object_or_404(Profile, user=match_order.user)
        user_profile.balance = Decimal(user_profile.balance or '0.00')

        # Calculate the credit or debit amount based on whether the user wins or loses
        if match_order.response == settle_response:  # The user won
            credit_amount = Decimal(match_order.match_quantity * 10)  # Example winning calculation
            return_amount = credit_amount - match_order.total_match_price # Positive amount for winnings
            user_profile.balance += credit_amount  # Update the user's balance with winnings
        else:  # The user lost
            credit_amount = Decimal('0.00')
            return_amount = -Decimal(match_order.total_match_price)  # Negative amount for losses

        # Save the updated user profile if the balance was adjusted
        if credit_amount > 0:
            user_profile.save()

            # Record the transaction for winnings
            Transaction.objects.create(
                user=match_order.user,
                profile=user_profile,
                amount=credit_amount,
                transaction_type='credit'
            )

        # Calculate total investment, return amount, and other quantities
        total_investment = match_order.total_match_price

        settled_quantity = match_order.match_quantity
        cancel_quantity = CancelOrder.objects.filter(event=event, user=match_order.user).aggregate(total_cancel=Sum('cancel_quantity'))['total_cancel'] or Decimal('0.00')

        # Create an entry in ClosedEvent for all users, whether they won or lost
        ClosedEvent.objects.create(
            user=match_order.user,
            settled_event=settled_event,
            settled_quantity=settled_quantity,
            cancel_quantity=cancel_quantity,
            total_investment=total_investment,
            return_amount=return_amount  # Positive for wins, negative for losses
        )

    # Automatically cancel all pending orders for the event
    pending_orders = Order.objects.filter(event=event, status='pending')
    for order in pending_orders:
        profile = get_object_or_404(Profile, user=order.user)
        profile.balance = Decimal(profile.balance or '0.00')
        profile.balance += order.total_price
        profile.save()

        # Record the transaction for the refund
        Transaction.objects.create(
            user=order.user,
            profile=profile,
            amount=order.total_price,
            transaction_type='refund'
        )

        # Update the OrderStatus object
        order_status = OrderStatus.objects.filter(
            user=order.user,
            event=order.event
        ).first()

        if order_status:
            order_status.cancelled_quantity += order.quantity
            order_status.status = 'cancelled'
            order_status.save()

        # Save the cancelled order in the CancelOrder table
        CancelOrder.objects.create(
            user=order.user,
            event=order.event,
            response=order.response,
            cancel_quantity=order.quantity,
            price_per_quantity=order.price_per_quantity,
            total_cancel_price=order.total_price
        )

        # Delete the pending order
        order.delete()

    # Delete match orders related to the event
    MatchOrder.objects.filter(event=event).delete()

    # Delete cancel orders related to the event
    CancelOrder.objects.filter(event=event).delete()

    messages.success(request, 'Event settled, all pending orders cancelled, and related match/cancel records deleted successfully.')
    return redirect('dashboard')


@csrf_exempt
def fetch_order_data(request):
    response_type = request.GET.get('response_type', None)
    event_id = request.GET.get('event_id', None)
    
    # Validate event_id
    if not event_id:
        return JsonResponse({'error': 'Event ID is required'}, status=400)

    # Filter orders based on event_id
    orders = Order.objects.filter(event_id=event_id)
    
    # Filter based on response_type
    if response_type == 'yes':
        orders = orders.filter(response='no')
    elif response_type == 'no':
        orders = orders.filter(response='yes')
    
    # Exclude orders placed by the requesting user
    if request.user.is_authenticated:
        orders = orders.exclude(user=request.user)
    
    # Define the mapping for price_per_quantity
    price_mapping = {
        1: 9,
        2: 8,
        3: 7,
        4: 6,
        5: 5,
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

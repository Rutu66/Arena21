from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.ImageField(upload_to='icons/')

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    icon = models.ImageField(upload_to='subcategory_icons/', blank=True, null=True)
    is_live = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Event(models.Model):
    sub_category = models.ForeignKey(SubCategory, on_delete=models.CASCADE, null=True, blank=True, related_name='Events')
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    traders_count = models.IntegerField()
    icon = models.ImageField(upload_to='images/')

    def __str__(self):
        return self.title

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return self.user.username

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    transaction_type = models.CharField(max_length=10, choices=[('credit', 'Credit'), ('debit', 'Debit')])

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount}"

class Order(models.Model):
    RESPONSE_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    response = models.CharField(max_length=3, choices=RESPONSE_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)  # Make this field non-editable
    matched_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cancelled_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Calculate total_price only if quantity and price_per_quantity are valid
        if self.quantity and self.price_per_quantity:
            try:
                self.total_price = self.quantity * self.price_per_quantity
            except (ValueError, TypeError) as e:
                # Handle the exception appropriately
                self.total_price = Decimal('0.00')  # Default value if calculation fails
                print(f"Error calculating total_price: {e}")
        else:
            # Set total_price to 0 if quantity or price_per_quantity is zero or invalid
            self.total_price = Decimal('0.00')

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.event.title} - {self.response}"
    
class OrderStatus(models.Model):
    RESPONSE_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    response = models.CharField(max_length=3, choices=RESPONSE_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)  # Make this field non-editable
    matched_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cancelled_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)
    

    

    
class MatchOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    response = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    match_quantity = models.IntegerField()
    price_per_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    total_match_price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_match_price = self.match_quantity * self.price_per_quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.event.title} - {self.response} - {self.match_quantity}"

class CancelOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    response = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    cancel_quantity = models.IntegerField()
    price_per_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    total_cancel_price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_cancel_price = self.cancel_quantity * self.price_per_quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.event.title} - {self.response} - {self.cancel_quantity}"


class SettledEvent(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    response = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')])
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.Event.title} - {self.response}"

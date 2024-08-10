from django import forms
from django.contrib.auth.models import User

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data
    
    
# forms.py
from django import forms
from .models import *

class AddMoneyForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2)

from django import forms
from .models import Order, Event

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['event', 'response', 'quantity', 'price_per_quantity']
        widgets = {
            'response': forms.RadioSelect(choices=Order.RESPONSE_CHOICES),
            'quantity': forms.NumberInput(attrs={'step': '0.01'}),
            'price_per_quantity': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize form fields if needed
        # self.fields['user'].queryset = User.objects.all()
        # self.fields['event'].queryset = Event.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        price_per_quantity = cleaned_data.get('price_per_quantity')

        if quantity is not None and price_per_quantity is not None:
            self.instance.total_price = quantity * price_per_quantity

        return cleaned_data

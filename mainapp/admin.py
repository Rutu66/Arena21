from django.contrib import admin
from .models import Category, SubCategory, Event, Profile, Transaction, Order, MatchOrder, CancelOrder, SettledEvent

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)

class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_live', 'icon')
    search_fields = ('name', 'category__name')
    list_filter = ('is_live', 'category')

class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'sub_category', 'traders_count', 'icon')
    search_fields = ('title', 'sub_category__name')
    list_filter = ('sub_category',)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    search_fields = ('user__username',)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile', 'amount', 'timestamp', 'transaction_type')
    search_fields = ('user__username', 'profile__user__username')
    list_filter = ('transaction_type', 'timestamp')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'response', 'quantity', 'price_per_quantity', 'total_price', 'matched_quantity', 'cancelled_quantity', 'status', 'timestamp')
    list_filter = ('status', 'response')
    search_fields = ('user__username', 'event__title')

class MatchOrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'response', 'match_quantity', 'price_per_quantity', 'total_match_price', 'timestamp')
    search_fields = ('user__username', 'event__title')
    list_filter = ('response', 'timestamp')

class CancelOrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'response', 'cancel_quantity', 'price_per_quantity', 'total_cancel_price', 'timestamp')
    search_fields = ('user__username', 'event__title')
    list_filter = ('response', 'timestamp')

class SettledEventAdmin(admin.ModelAdmin):
    list_display = ('event', 'response', 'timestamp')
    search_fields = ('event__title',)
    list_filter = ('response', 'timestamp')
    


admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(MatchOrder, MatchOrderAdmin)
admin.site.register(CancelOrder, CancelOrderAdmin)
admin.site.register(SettledEvent, SettledEventAdmin)

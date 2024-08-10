# urls.py
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    
    path('signup/', signup_view, name='signup'),
    path('index/', index_view, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', lending_view, name='lending'),
    path('dashboard/', dashboard, name='dashboard'),
    path('add_money/', add_money, name='add_money'),
    path('place_order/', place_order, name='place_order'),
    path('cancel_order/<int:order_id>/', cancel_order, name='cancel_order'),
    path('settle_event/<int:event_id>/<str:settle_response>/', settle_event, name='settle_event'),
    path('fetch-order-data/', fetch_order_data, name='fetch_order_data'),
    

    
    

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




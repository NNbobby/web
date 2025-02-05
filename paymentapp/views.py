# paymentapp/views.py (пример для будущей логики)
from django.shortcuts import render



def payment_form(request):
    return render(request, 'paymentapp/payment_form.html')

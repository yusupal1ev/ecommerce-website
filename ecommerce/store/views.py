import json
import datetime
import decimal

from django.views.generic import ListView, TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect

from .models import *
from .utils import cookieCart, cartData, guestCheckout


class StoreView(TemplateView):
    model = Product
    template_name = 'store/store.html'

    def get(self, request, *args, **kwargs):
        data = cartData(request)
        cartItems = data["cartItems"]

        context = self.get_context_data(cartItems=cartItems, **kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = Product.objects.all()
        context["cartItems"] = kwargs['cartItems']
        return context


class CartView(TemplateView):
    model = Order
    template_name = 'store/cart.html'

    def get(self, request, *args, **kwargs):
        data = cartData(request)
        cartItems = data["cartItems"]
        order = data["order"]
        items = data["items"]

        context = self.get_context_data(items=items, order=order, cartItems=cartItems, **kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["items"] = kwargs['items']
        context["order"] = kwargs['order']
        context["cartItems"] = kwargs['cartItems']
        return context


class CheckoutView(TemplateView):
    model = Order
    template_name = 'store/checkout.html'

    def get(self, request, *args, **kwargs):
        data = cartData(request)
        cartItems = data["cartItems"]
        order = data["order"]
        items = data["items"]

        context = self.get_context_data(items=items, order=order, cartItems=cartItems, **kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["items"] = kwargs["items"]
        context["order"] = kwargs["order"]
        context["cartItems"] = kwargs['cartItems']
        return context


def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']

    print('productId: ', productId)
    print('action: ', action)

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)


def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)

    else:
        customer, order = guestCheckout(data, request)

    total = decimal.Decimal(data['form']['total'].replace(',', '.'))
    order.transaction_id = transaction_id

    if total == order.get_cart_total:
        order.complete = True
    order.save()

    if order.shipping == True:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )

    return JsonResponse('Payment complete..', safe=False)

from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.
def index(request):
    return HttpResponse('Главная страница')


def groups(request):
    return HttpResponse('Группы')


def group_details(request, slug):
    return HttpResponse('GROUP #')

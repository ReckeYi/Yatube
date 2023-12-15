# Импортируем CreateView, чтобы создать ему наследника
from django.contrib.auth import login, get_user_model
from django.core.exceptions import PermissionDenied
from django.views.generic import CreateView, UpdateView

# Функция reverse_lazy позволяет получить URL по параметрам функции path()
# Берём, тоже пригодится
from django.urls import reverse_lazy

# Импортируем класс формы, чтобы сослаться на неё во view-классе
from .forms import CreationForm

User = get_user_model()


class SignUp(CreateView):
    form_class = CreationForm
    # После успешной регистрации перенаправляем пользователя на главную.
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'

    def form_valid(self, form):
        valid = super().form_valid(form)
        login(self.request, self.object)
        return valid


class UserUpdateView(UpdateView):
    model = User
    fields = (
        "first_name",
        "last_name",
        "username",
        "email",
        "profile_picture",
    )
    success_url = "/"

    def get_object(self):
        obj = super().get_object()
        if obj != self.request.user:
            raise PermissionDenied()
        return obj
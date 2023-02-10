from django.views import generic
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin

from .forms import CustomUserCreationForm


class SignUpView(UserPassesTestMixin, generic.CreateView):
    form_class = CustomUserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")

    def test_func(self):
        return not self.request.user.is_authenticated

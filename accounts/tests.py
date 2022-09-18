from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class SignUpTest(TestCase):
    username = "fatemeh"
    email = "fatemeh@gmail.com"
    phone_number = "0911685978"

    def test_signup_page_url(self):
        response = self.client.get("/accounts/signup/")
        self.assertEqual(response.status_code, 200)

    def test_signup_page_url_by_name(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)

    def test_signup_form(self):
        user = get_user_model().objects.create(
            username=self.username,
            email=self.email,
            phone_number=self.phone_number,
        )

        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(get_user_model().objects.first().username, self.username)
        self.assertEqual(get_user_model().objects.first().email, self.email)
        self.assertEqual(get_user_model().objects.first().phone_number, self.phone_number)

    def test_signup_page_template_used(self):
        response = self.client.get(reverse("signup"))
        self.assertTemplateUsed(response, "registration/signup.html")

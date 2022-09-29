from django.test import TestCase
from django.shortcuts import reverse

from .models import Report


class NewsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.report_1 = Report.objects.create(
            title="title 1",
            description="description 1",
            author="author 1",
        )

    def test_report_list_url(self):
        response = self.client.get("/news/")
        self.assertEqual(response.status_code, 200)

    def test_report_list_url_by_name(self):
        response = self.client.get(reverse("report_list"))
        self.assertEqual(response.status_code, 200)

    def test_report_detail_url(self):
        response = self.client.get(f"/news/{self.report_1.id}/")
        self.assertEqual(response.status_code, 200)

    def test_report_detail_url_by_name(self):
        response = self.client.get(reverse("report_detail", args=[self.report_1.id]))
        self.assertEqual(response.status_code, 200)

    def test_report_create_url(self):
        response = self.client.get("/news/create/")
        self.assertEqual(response.status_code, 200)

    def test_report_create_url_by_name(self):
        response = self.client.get(reverse("report_create"))
        self.assertEqual(response.status_code, 200)

    def test_report_update_url(self):
        response = self.client.get(f"/news/{self.report_1.id}/update/")
        self.assertEqual(response.status_code, 200)

    def test_report_update_url_by_name(self):
        response = self.client.get(reverse("report_update", args=[self.report_1.id]))
        self.assertEqual(response.status_code, 200)

    def test_report_delete_url(self):
        response = self.client.get(f"/news/{self.report_1.id}/delete/")
        self.assertEqual(response.status_code, 200)

    def test_report_delete_url_by_name(self):
        response = self.client.get(reverse("report_delete", args=[self.report_1.id]))
        self.assertEqual(response.status_code, 200)

    def test_report_list_template_used(self):
        response = self.client.get(reverse("report_list"))
        self.assertTemplateUsed(response, "news/report_list.html")

    def test_report_detail_template_used(self):
        response = self.client.get(reverse("report_detail", args=[self.report_1.id]))
        self.assertTemplateUsed(response, "news/report_detail.html")

    def test_report_create_template_used(self):
        response = self.client.get(reverse("report_create"))
        self.assertTemplateUsed(response, "news/report_create_and_update.html")

    def test_report_update_template_used(self):
        response = self.client.get(reverse("report_update", args=[self.report_1.id]))
        self.assertTemplateUsed(response, "news/report_create_and_update.html")

    def test_report_delete_template_used(self):
        response = self.client.get(reverse("report_delete", args=[self.report_1.id]))
        self.assertTemplateUsed(response, "news/report_delete.html")

    def test_str_report_model(self):
        self.assertEqual(str(self.report_1), "title 1")

    def test_report_list_view(self):
        response = self.client.get(reverse("report_list"))
        self.assertContains(response, self.report_1.title)
        self.assertContains(response, self.report_1.description)

    def test_report_detail_view(self):
        response = self.client.get(reverse("report_detail", args=[self.report_1.id]))
        self.assertContains(response, self.report_1.title)
        self.assertContains(response, self.report_1.author)
        self.assertContains(response, self.report_1.description)

    def test_page_404_if_report_not_exist(self):
        response = self.client.get(reverse("report_detail", args=[2]))
        self.assertEqual(response.status_code, 404)

    def test_report_create_view(self):
        response = self.client.post(reverse("report_create"), {
            "title": "title 2",
            "description": "description 2",
            "author": "author 2",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Report.objects.count(), 2)
        self.assertRedirects(response, reverse("report_detail", args=[2]))

    def test_report_update_view(self):
        response = self.client.post(reverse("report_update", args=[self.report_1.id]), {
            "title": "title 1 update",
            "description": "description 1 update",
            "author": "author 1 update",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("report_detail", args=[self.report_1.id]))

    def test_report_delete_view(self):
        response = self.client.post(reverse("report_delete", args=[self.report_1.id]), {})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("report_list"))
        self.assertEqual(Report.objects.count(), 0)

        response_2 = self.client.get(reverse("report_list"))
        self.assertNotContains(response_2, self.report_1.title)
        self.assertNotContains(response_2, self.report_1.description)

    def test_number_of_reports_in_report_model(self):
        self.assertEqual(Report.objects.count(), 1)



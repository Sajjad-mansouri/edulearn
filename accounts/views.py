from django.views.generic import TemplateView


class LoginView(TemplateView):
    template_name = "accounts/login.html"


class RegisterStudentView(TemplateView):
    template_name = "accounts/register_student.html"

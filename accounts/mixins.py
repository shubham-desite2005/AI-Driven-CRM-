from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.urls import reverse


class RegularUserRequiredMixin(AccessMixin):
    login_url = 'accounts:login'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if request.user.is_staff or request.user.is_superuser:
            return redirect(reverse('admin:index'))

        return super().dispatch(request, *args, **kwargs)

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import ProductReview, Coupon


class RegisterForm(UserCreationForm):

    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User

        fields = (
            'first_name',
            'last_name',
            'username',
            'email',
            'password1',
            'password2'
        )

    def save(self, commit=True):
        user = super().save(commit=False)

        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

        return user


class ProfileForm(forms.ModelForm):

    class Meta:
        model = User

        fields = [
            'first_name',
            'last_name',
            'email',
            'username'
        ]


class ProductReviewForm(forms.ModelForm):

    class Meta:
        model = ProductReview

        fields = [
            'rating',
            'comment'
        ]

        widgets = {
            'rating': forms.NumberInput(attrs={
                'min': 1,
                'max': 5,
                'class': 'form-control'
            }),

            'comment': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control'
            }),
        }


class CouponApplyForm(forms.Form):
    code = forms.CharField(
        max_length=20,
        label='Coupon Code'
    )


class CheckoutForm(forms.Form):

    first_name = forms.CharField(max_length=50)

    last_name = forms.CharField(max_length=50)

    email = forms.EmailField()

    phone = forms.CharField(max_length=15)

    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4})
    )

    city = forms.CharField(max_length=100)

    postal_code = forms.CharField(max_length=20)

    country = forms.CharField(max_length=100)
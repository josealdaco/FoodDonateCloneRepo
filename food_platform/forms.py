from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.forms.utils import ValidationError
from datetimewidget.widgets import DateTimeWidget, TimeWidget
from datetime import date

from bootstrap_datepicker_plus import DatePickerInput,  TimePickerInput
from food_platform.models import (Answer, PickupTime, Foodriver, FoodriverAnswer,
                              Interested_area, CustomUser, ShelterInfo)
from PIL import Image


def validate_image(image):
    """ This will Cap the Image to 1500 KB"""
    file_size = image.size
    limit_kb = (200*200) * 3
    imagesTypes = ['JPEG', 'PNG']
    localImage = Image.open(image)
    if file_size > limit_kb:
        print("This image is not validated")
        raise ValidationError("Max size of Image is %s KB" % str(round(limit_kb/1014)))
    elif localImage.format not in imagesTypes:
        raise ValidationError("NOT VALID IMAGE TYPE, HAS TO BE JPEG OR PNG")
    return image


def validate_phone_number(number):
    if len(str(number)) > 14:
        raise ValidationError("Not a Valid number")
    else:
        PhoneNumber = None
        try:
            PhoneNumber = int(number)
        except Exception:
            raise ValidationError("Not valid input")
        return isinstance(PhoneNumber, int)


class FoodonatorSignUpForm(UserCreationForm):
    profile_Image = forms.ImageField(validators=[validate_image], required=True, widget=forms.ClearableFileInput(attrs={"id":"ImageInput"}))
    name = forms.CharField(label="Name", max_length=50, required=True)
    last_name = forms.CharField(label="Last Name", max_length=100, required=True)
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')
    phone_number = forms.CharField(required=True, validators=[validate_phone_number], help_text='Your contact #')
    # image = forms.ImageField(upload_to='images/')

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('profile_Image','name', 'last_name', 'email', 'phone_number', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_foodonator = True
        user.phone_number = self.cleaned_data.get("phone_number")
        if commit:
            user.save()
        return user


GENDER_CHOICES =(
    ('H', 'He'),
    ('S', 'She'),
    ('N', 'Non-Binary')
)


class FoodriverSignUpForm(UserCreationForm, forms.Form):
    # first_name = forms.CharField(max_length=30, required=True, help_text='Optional.')
    # last_name = forms.CharField(max_length=30, required=True, help_text='Optional.')
    # date_of_birth =
    # pronouns
    # phone_number = forms.IntegerField(help_text='Your contact #')
    profile_Image = forms.ImageField(validators=[validate_image], required=True, widget=forms.ClearableFileInput(attrs={"id":"ImageInput"}))
    name = forms.CharField(label="Name", max_length=50, required=True)
    last_name = forms.CharField(label="Last Name", max_length=100, required=True)
    date_of_birth = forms.DateField(
        widget=DatePickerInput(format='%m/%d/%Y'),
        required=True
    )

    pronouns = forms.ChoiceField(choices=GENDER_CHOICES)
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.', required=True)
    password1 = forms.CharField(label='Enter password', widget=forms.PasswordInput,  required=True)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput, required=True)

    area = forms.ModelMultipleChoiceField(
        queryset=Interested_area.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Don't worry, you can always change your preferred area"

    )

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)

    class Meta:
        model = CustomUser
        fields = ('profile_Image', 'pronouns', 'date_of_birth', 'email', 'password1', 'password2', 'area')

    @transaction.atomic
    def save(self):
        print("Attempting to save")
        user = super().save(commit=False)
        user.is_foodriver = True
        user.profile_Image = self.cleaned_data.get("profile_Image")
        user.date_of_birth = self.cleaned_data.get("date_of_birth")
        user.name = self.cleaned_data.get("name")
        user.last_name = self.cleaned_data.get("last_name")
        user.save()
        foodriver = Foodriver.objects.create(user=user)
        foodriver.area.add(*self.cleaned_data.get('area'))
        foodriver.save()

        print("Save successful")
        return user


class ShelterSignUpForm(UserCreationForm):
    profile_Image = forms.ImageField(label="Shelter Logo",validators=[validate_image], required=True, widget=forms.ClearableFileInput(attrs={"id":"ImageInput"}))
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')
    phone_number = forms.CharField(max_length=14, help_text='Your contact #')

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('profile_Image', 'email', 'phone_number', 'password1', 'password2')
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_shelter = True
        if commit:
            user.save()
        return user


class FoodriverAreaForm(forms.ModelForm):
    class Meta:
        model = Foodriver
        fields = ('area', )
        widgets = {
            'area': forms.CheckboxSelectMultiple
        }


class PickupTimeForm(forms.ModelForm):
    text = forms.TimeField()#widget=forms.extras.widgets.SelectTimeWidget(twelve_hr=True))

    class Meta:
        model = PickupTime
        fields = ('text', )


class BaseAnswerInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()

        has_one_correct_answer = False
        for form in self.forms:
            if not form.cleaned_data.get('DELETE', False):
                if form.cleaned_data.get('is_correct', False):
                    has_one_correct_answer = True
                    break
        if not has_one_correct_answer:
            raise ValidationError('Mark at least one answer as correct.', code='no_correct_answer')


class TakePickupForm(forms.ModelForm):
    answer = forms.ModelChoiceField(
        queryset=Answer.objects.none(),
        widget=forms.RadioSelect(),
        required=True,
        empty_label=None)

    class Meta:
        model = FoodriverAnswer
        fields = ('answer', )

    def __init__(self, *args, **kwargs):
        pickup_time = kwargs.pop('pickup_time')
        super().__init__(*args, **kwargs)
        self.fields['answer'].queryset = pickup_time.answers.order_by('text')


class ShelterInfoForm(forms.ModelForm):
    class Meta:
        model = ShelterInfo
        fields = ("title", "dropoff_time", "homeless_residents", "author")

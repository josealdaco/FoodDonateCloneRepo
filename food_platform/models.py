from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.html import escape, mark_safe
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone

from .managers import CustomUserManager
from django.contrib.auth.hashers import check_password

from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin

from django.contrib.auth import get_user_model
from PIL import Image
from io import BytesIO
from django.core.files import File
import os
import PIL


def get_image_path(instance, filename):
    print("Triggered, this is the destination:", str(instance.pk), filename)
    return os.path.join('static/userphotos', str(instance.email), filename)


def default_image_path():
    '''This will create a default image'''
    im = Image.open(r"static/img/default-image.png", mode='r')
    sizeb = os.path.getsize('static/img/default-image.png')
    print("Size in bytes", sizeb)
    thumb_io = BytesIO(sizeb.to_bytes(10, 'big')) # create a BytesIO object
    im = im.resize((400, 400), PIL.Image.ANTIALIAS)
    im.save(thumb_io, 'PNG', quality=90) # save image to BytesIO object
    thumbnail = File(thumb_io, name='default-image.png') # create a django friendly File object
    return thumbnail


# change for interested_area
class EmailAuth(object):
    def authenticate(self, email="", password=""):
    #    UserModel = get_user_model()
        try:
            user = CustomUser.objects.get(email=email)
            if check_password(password, user.password):
                return user
            else:
                return None
        except CustomUser.DoesNotExist:
            # No user was found, return None - triggers default login failed
            return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None


class Interested_area(models.Model):
    name = models.CharField(max_length=30)
    color = models.CharField(max_length=7, default='#007bff')

    def __str__(self):
        return self.name

    def get_html_badge(self):
        name = escape(self.name)
        color = escape(self.color)
        html = '<span class="badge badge-primary" style="background-color: %s">%s</span>' % (color, name)
        return mark_safe(html)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = None
    email = models.EmailField(('email address'), unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_foodriver = models.BooleanField(default=False)
    is_foodonator = models.BooleanField(default=False)
    is_shelter = models.BooleanField(default=False)
    name = models.CharField(max_length=50, null=True)
    last_name = models.CharField(max_length=100, null=True)
    phone_number = models.CharField(max_length=14, null=True, blank=True)
    profile_Image = models.ImageField(upload_to=get_image_path, blank=True) #default=os.path.join('img/default-image.png'))
    #areas = models.ForeignKey(Interested_area, on_delete=models.CASCADE, related_name='UserAreas', null=True)
    date_of_birth = models.DateField(null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class Pickup(models.Model):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='pickups')
    name = models.CharField(max_length=255)
    interested_area = models.ForeignKey(Interested_area, on_delete=models.CASCADE, related_name='pickups')

    def __str__(self):
        return self.name


class PickupTime(models.Model):
    pickup = models.ForeignKey(Pickup, on_delete=models.CASCADE, related_name='pickup_times')
    text = models.DateTimeField()

    def __str__(self):
        return self.text


class Answer(models.Model):
    pickup_time = models.ForeignKey(PickupTime, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField('Answer', max_length=255)
    is_correct = models.BooleanField('Correct answer', default=False)

    def __str__(self):
        return self.text


class Foodriver(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    pickups = models.ManyToManyField(Pickup, through='TakenPickup')
    area = models.ManyToManyField(Interested_area, related_name='interested_foodrivers')

    def get_unanswered_pickup_times(self, pickup):
        answered_pickup_times = self.pickup_answers \
            .filter(answer__pickup_time__pickup=pickup) \
            .values_list('answer__pickup_time__pk', flat=True)
        pickup_times = pickup.pickup_times.exclude(pk__in=answered_pickup_times).order_by('text')
        return pickup_times

    def __str__(self):
        return self.user.email


class TakenPickup(models.Model):
    foodriver = models.ForeignKey(Foodriver, on_delete=models.CASCADE, related_name='taken_pickups')
    pickup = models.ForeignKey(Pickup, on_delete=models.CASCADE, related_name='taken_pickups')
    score = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)


class FoodriverAnswer(models.Model):
    foodriver = models.ForeignKey(Foodriver, on_delete=models.CASCADE, related_name='pickup_answers')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='+')


class ShelterInfo(models.Model):
    title = models.CharField(max_length=30, blank=True, default="Shelter")
    dropoff_time = models.TimeField()
    author = models.ForeignKey(CustomUser, on_delete=models.PROTECT,
                               help_text="The user that posted this article.")
    slug = models.CharField(max_length=settings.PROJECT_CODE_TITLE_MAX_LENGTH, blank=True, editable=False,
                            help_text="Unique URL path to access this shelter info. Generated by the system.")
    homeless_residents = models.IntegerField(
        help_text="How many residents are you having this week?")
    created = models.DateTimeField(auto_now_add=True,
                                   help_text="The date and time this info was created. Automatically generated when the model saves.")
    modified = models.DateTimeField(auto_now=True,
                                    help_text="The date and time this info was updated. Automatically generated when the model updates.")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        path_components = {'slug': self.slug}
        return reverse('shelterinfo-details-project', kwargs=path_components)

    def save(self, *args, **kwargs):
        """ Creates a URL safe slug automatically when a new a shelter info is inputted. """
        if not self.pk:
            self.slug = slugify(self.title, allow_unicode=True)

        # Call save on the superclass.
        return super(ShelterInfo, self).save(*args, **kwargs)

from django.db import models
from django.db.models import Model
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .managers import CustomUserManager
from places.base.models import City, Country, PlaceType


class CustomUser(AbstractBaseUser, PermissionsMixin):
    # Password (hidden)
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    GENDER_CHOICES = (
        ('', 'Unset'),
        ('M', 'Male'),
        ('F', 'Female'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='')
    birth_date = models.DateField(verbose_name="Date of birth", blank=True, null=True)
    city = models.ForeignKey(City, verbose_name='City', blank=True, null=True, on_delete=models.SET_NULL)
    country = models.ForeignKey(Country, verbose_name='Country', blank=True, null=True, related_name='users',
                                on_delete=models.SET_NULL, limit_choices_to={'type': PlaceType.COUNTRY})
    phone = models.CharField(verbose_name='Phone number', max_length=15, blank=True, null=True, default=None)
    # permissions
    is_staff = models.BooleanField(_('staff status'),
                                   default=False,
                                   help_text=_('Designates whether the user can log into this admin site.'), )
    is_active = models.BooleanField(_('active'),
                                    default=False,
                                    help_text=_(
                                        'Designates whether this user should be treated as active. '
                                        'Unselect this instead of deleting accounts.'
                                    ), )
    # DATES
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    # Codes
    activation_code = models.IntegerField(verbose_name='Account Activation Code', blank=True, null=True)
    password_reset_code = models.IntegerField(verbose_name='Password Reset Code', blank=True, null=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return '{}'.format(self.email)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ('date_joined',)

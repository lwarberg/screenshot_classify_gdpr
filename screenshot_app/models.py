from django.db import models
from django.contrib.auth.models import User


class Screenshot(models.Model):
    wave_id = models.IntegerField(blank=True, null=True)
    view_id = models.IntegerField(blank=True, null=True)
    country = models.CharField(max_length=10, null=True)
    domain = models.CharField(max_length=255, null=True)
    channel_id = models.CharField(max_length=512, null=True)
    image_path = models.CharField(max_length=512, null=True)
    batch_num = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.domain + '_' + str(self.country) + '_' + str(self.wave_id)


class Task(models.Model):
    domain = models.CharField(max_length=255, null=True)
    country = models.CharField(max_length=10, null=True)
    screenshots = models.ManyToManyField(Screenshot, blank=True)

    def __str__(self):
        return self.domain + '_' + str(self.country)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    setting_collaborative_sort = models.BooleanField(default=False)
    assigned_tasks = models.ManyToManyField(Task, blank=True)

    def __str__(self):
        return self.user.username


class Response(models.Model):
    screenshot = models.ForeignKey(Screenshot, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=50, null=True)
    presentation = models.CharField(max_length=50, null=True)
    actions_accept = models.BooleanField(default=False)
    actions_decline = models.BooleanField(default=False)
    actions_more_information = models.BooleanField(default=False)
    actions_settings = models.BooleanField(default=False)
    actions_close = models.BooleanField(default=False)
    actions_privacy_policy = models.BooleanField(default=False)
    actions_preference_checkboxes = models.BooleanField(default=False)
    content_tracking_cookies = models.BooleanField(default=False)
    content_other_cookies = models.BooleanField(default=False)
    content_default_accept = models.BooleanField(default=False)
    content_implied_decline = models.BooleanField(default=False)
    content_explicit_decline = models.BooleanField(default=False)
    content_preselected_checkboxes = models.BooleanField(default=False)
    website_adblocker_present = models.BooleanField(default=False)
    website_subscription_option = models.BooleanField(default=False)
    website_paywall_present = models.BooleanField(default=False)
    website_not_active = models.BooleanField(default=False)
    further_review = models.BooleanField(default=False)
    further_review_language = models.BooleanField(default=False)
    further_review_language_select = models.CharField(max_length=50, null=True, blank=True)
    further_review_other = models.BooleanField(default=False)
    further_review_other_text = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user.username + '_' + self.screenshot.domain + '_' + str(self.screenshot.country) + '_' + str(
            self.screenshot.wave_id)

from django.db import models
from django.utils import timezone

class EmailTracking(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('opened', 'Opened'),
        ('unopened', 'Unopened'),
        ('clicked', 'CTA Clicked'),
        ('unseen', 'Cold Lead')
    ]

    # Company Information
    company_name = models.CharField(max_length=255)
    website = models.URLField()
    industry = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    followers = models.CharField(max_length=255)
    description = models.TextField()
    
    # Email Information
    email = models.EmailField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    sent_date = models.DateTimeField(default=timezone.now)
    opened_date = models.DateTimeField(null=True, blank=True)
    clicked_date = models.DateTimeField(null=True, blank=True)
    tracking_id = models.CharField(max_length=50, unique=True)
    last_updated = models.DateTimeField(auto_now=True)
    click_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.company_name} - {self.email} - {self.status}"

    class Meta:
        ordering = ['-sent_date'] 
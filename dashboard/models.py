from django.db import models

class MatomoSite(models.Model):
    site_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class AnalyticsResult(models.Model):
    url = models.URLField()
    site = models.ForeignKey(MatomoSite, on_delete=models.CASCADE)
    date_start = models.DateField()
    date_end = models.DateField()
    visits = models.IntegerField()
    pageviews = models.IntegerField()
    bounce_rate = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.url} ({self.date_start} - {self.date_end})"

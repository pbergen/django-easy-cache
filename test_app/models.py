from django.db import models


class TestModel(models.Model):
    """A simple test model for testing django-smart-cache."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class RelatedTestModel(models.Model):
    """A related model for testing cache invalidation."""

    test_model = models.ForeignKey(TestModel, on_delete=models.CASCADE, related_name="related_items")
    title = models.CharField(max_length=50)
    value = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.test_model.name})"

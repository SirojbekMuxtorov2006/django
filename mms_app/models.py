from django.db import models
from django.contrib.auth.models import User

class Material(models.Model):
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics & Sensors'),
        ('mechanical', 'Mechanical & Structure'),
        ('energy', 'Energy & Power Systems'),
        ('pneumatics', 'Pneumatics & Hydraulics'),
        ('consumables', 'Consumables & Tools'),
    ]

    name = models.CharField(max_length=150)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='electronics')
    quantity = models.FloatField(default=0.0)
    unit = models.CharField(max_length=20, default='pcs')
    min_required = models.FloatField(default=0.0)
    image = models.ImageField(upload_to='materials/', blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def status(self):
        if self.quantity <= 0:
            return 'Out of Stock'
        elif self.quantity <= self.min_required:
            return 'Low Stock'
        return 'Good'

    @property
    def status_class(self):
        if self.quantity <= 0:
            return 'danger'
        elif self.quantity <= self.min_required:
            return 'warning'
        return 'success'

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"

class MaintenanceTask(models.Model):
    STATUS_CHOICES = [
        ('backlog', 'Backlog'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='backlog')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def priority_class(self):
        if self.priority == 'high':
            return 'danger'
        elif self.priority == 'medium':
            return 'warning'
        return 'info'

    @property
    def status_class(self):
        if self.status == 'completed':
            return 'success'
        elif self.status == 'in_progress':
            return 'primary'
        return 'secondary'

    def __str__(self):
        return self.title

class SystemAlert(models.Model):
    ALERT_TYPES = [
        ('danger', 'Critical Danger'),
        ('warning', 'System Warning'),
        ('info', 'System Info'),
    ]

    message = models.CharField(max_length=255)
    alert_type = models.CharField(max_length=15, choices=ALERT_TYPES, default='info')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.alert_type.upper()}] {self.message[:50]}"

class AIConversation(models.Model):
    user_message = models.TextField()
    ai_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AI Message on {self.created_at.strftime('%Y-%m-%d %H:%M')}"

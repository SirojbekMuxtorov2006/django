import os
import django
import datetime

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_mms.settings')
django.setup()

from django.contrib.auth.models import User
from mms_app.models import Material, MaintenanceTask, SystemAlert

def seed():
    print("Starting database seeding...")
    
    # 1. Create Users
    print("- Seeding Users...")
    admin_user, created = User.objects.get_or_create(username='admin', email='admin@core.mms')
    if created:
        admin_user.set_password('admin123')
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.save()
        print("  * Superuser created: admin / admin123")
        
    u1, _ = User.objects.get_or_create(username='Sirojbek', email='sirojbek@core.mms')
    u1.set_password('pass123')
    u1.save()
    
    u2, _ = User.objects.get_or_create(username='Alisher', email='alisher@core.mms')
    u2.set_password('pass123')
    u2.save()
    
    u3, _ = User.objects.get_or_create(username='Madina', email='madina@core.mms')
    u3.set_password('pass123')
    u3.save()
    
    # 2. Seeding Materials
    print("- Seeding Materials...")
    Material.objects.all().delete()
    
    m1 = Material.objects.create(
        name="Core CPU Controller v4",
        category="electronics",
        quantity=15.0,
        unit="pcs",
        min_required=5.0
    )
    
    m2 = Material.objects.create(
        name="Hydro-Piston Actuator H2",
        category="mechanical",
        quantity=3.0,
        unit="pcs",
        min_required=8.0
    )
    
    m3 = Material.objects.create(
        name="Solar Battery Cell Pack 500W",
        category="energy",
        quantity=0.0,
        unit="packs",
        min_required=6.0
    )
    
    m4 = Material.objects.create(
        name="Pneumatic Valve 1/4 inch",
        category="pneumatics",
        quantity=32.0,
        unit="pcs",
        min_required=10.0
    )
    
    m5 = Material.objects.create(
        name="Thermal Conductive Paste",
        category="consumables",
        quantity=4.0,
        unit="tubes",
        min_required=12.0
    )
    print(f"  * Seeded {Material.objects.count()} materials.")
    
    # 3. Seeding Tasks
    print("- Seeding Tasks...")
    MaintenanceTask.objects.all().delete()
    
    t1 = MaintenanceTask.objects.create(
        title="Birlamchi generatorni tekshirish",
        description="Moy bosimi va kontakt simlarini harorat sensori orqali ko'rib chiqish.",
        status="in_progress",
        priority="high",
        assigned_to=u1,
        due_date=datetime.date.today() + datetime.timedelta(days=1)
    )
    
    t2 = MaintenanceTask.objects.create(
        title="1-blok klapanlarini almashtirish",
        description="Bosim yo'qolishi aniqlandi. Pnevmatik klapanlarni yangisiga almashtirish zarur.",
        status="backlog",
        priority="high",
        assigned_to=u2,
        due_date=datetime.date.today() + datetime.timedelta(days=3)
    )
    
    t3 = MaintenanceTask.objects.create(
        title="Server xonasini tozalash va sovitish tizimi",
        description="Konditsioner filtrlari yuvildi, changlar artildi.",
        status="completed",
        priority="low",
        assigned_to=u3,
        due_date=datetime.date.today() - datetime.timedelta(days=1)
    )
    
    t4 = MaintenanceTask.objects.create(
        title="Quyosh panellarini changdan tozalash",
        description="Keltiriladigan energiya 12% kamaydi. Panellar yuzasini yuvib chiqish talab etiladi.",
        status="backlog",
        priority="medium",
        assigned_to=None,
        due_date=datetime.date.today() + datetime.timedelta(days=5)
    )
    print(f"  * Seeded {MaintenanceTask.objects.count()} tasks.")
    
    # 4. Seeding Alerts
    print("- Seeding Alerts...")
    SystemAlert.objects.all().delete()
    
    SystemAlert.objects.create(
        message="Solar Battery Cell Pack 500W zaxirasi butkul tugagan! Tizim energiyasi xavf ostida.",
        alert_type="danger"
    )
    SystemAlert.objects.create(
        message="Hydro-Piston Actuator H2 zaxirasi minimal chegaradan kam qoldi (Qoldiq: 3).",
        alert_type="warning"
    )
    SystemAlert.objects.create(
        message="Yangi a'zo Madina tizimga muvaffaqiyatli qo'shildi va vazifalarga biriktirildi.",
        alert_type="info"
    )
    print(f"  * Seeded {SystemAlert.objects.count()} system alerts.")
    
    print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed()

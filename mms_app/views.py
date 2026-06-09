import json
import os
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db.models import F, Count
from .models import Material, MaintenanceTask, SystemAlert, AIConversation

# Main Dashboard View
def dashboard(request):
    materials = Material.objects.all()
    tasks = MaintenanceTask.objects.all()
    alerts = SystemAlert.objects.filter(is_active=True).order_by('-created_at')
    
    # Material Stats
    total_materials = materials.count()
    low_stock_materials = materials.filter(quantity__lte=F('min_required')).exclude(quantity=0).count()
    out_of_stock_materials = materials.filter(quantity=0).count()
    
    # Task Stats
    total_tasks = tasks.count()
    pending_tasks = tasks.filter(status__in=['backlog', 'in_progress']).count()
    completed_tasks = tasks.filter(status='completed').count()
    
    # Calculate System Health (100% max)
    # Penalty: Out of stock is -15%, Low stock is -5%, Active danger alert is -10%
    health = 100
    for m in materials:
        if m.quantity <= 0:
            health -= 15
        elif m.quantity <= m.min_required:
            health -= 5
            
    danger_alerts = alerts.filter(alert_type='danger').count()
    health -= (danger_alerts * 10)
    health = max(10, min(100, health)) # Clamp between 10% and 100%
    
    # Health color classification
    if health >= 80:
        health_color = 'success'
        health_status = 'Optimal'
    elif health >= 50:
        health_color = 'warning'
        health_status = 'Warning'
    else:
        health_color = 'danger'
        health_status = 'Critical'
        
    recent_tasks = tasks.filter(status__in=['backlog', 'in_progress']).order_by('due_date')[:5]
    recent_alerts = alerts[:5]

    # Category counts for charts
    cat_counts = {}
    for choice_val, choice_label in Material.CATEGORY_CHOICES:
        cat_counts[choice_label] = materials.filter(category=choice_val).count()

    context = {
        'total_materials': total_materials,
        'low_stock_materials': low_stock_materials,
        'out_of_stock_materials': out_of_stock_materials,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'system_health': health,
        'health_color': health_color,
        'health_status': health_status,
        'recent_tasks': recent_tasks,
        'recent_alerts': recent_alerts,
        'cat_counts_json': json.dumps(cat_counts),
        'page_title': 'E-Core MMS Dashboard'
    }
    return render(request, 'dashboard.html', context)


# Materials/Inventory View
def materials_list(request):
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    
    materials = Material.objects.all()
    
    if category_filter:
        materials = materials.filter(category=category_filter)
        
    # Python-side filtering for properties or annotate
    filtered_materials = []
    for m in materials:
        if status_filter == 'out' and m.quantity > 0:
            continue
        if status_filter == 'low' and (m.quantity <= 0 or m.quantity > m.min_required):
            continue
        if status_filter == 'good' and m.quantity <= m.min_required:
            continue
        filtered_materials.append(m)
        
    categories = Material.CATEGORY_CHOICES

    # Handle Add Material POST
    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category')
        quantity = float(request.POST.get('quantity', 0))
        unit = request.POST.get('unit', 'pcs')
        min_required = float(request.POST.get('min_required', 0))
        image = request.FILES.get('image')
        
        material = Material.objects.create(
            name=name, category=category, quantity=quantity, 
            unit=unit, min_required=min_required, image=image
        )
        
        # Auto-create alert if low stock
        if quantity <= min_required:
            alert_type = 'danger' if quantity == 0 else 'warning'
            SystemAlert.objects.create(
                message=f"Material inventory notification: '{material.name}' added with {status_filter or material.status.lower()} levels.",
                alert_type=alert_type
            )
            
        return redirect('materials')

    context = {
        'materials': filtered_materials,
        'categories': categories,
        'selected_category': category_filter,
        'selected_status': status_filter,
        'page_title': 'Inventory Registry'
    }
    return render(request, 'materials.html', context)


# Delete Material
def delete_material(request, pk):
    material = get_object_or_404(Material, pk=pk)
    material.delete()
    return redirect('materials')


# Maintenance Tasks View
def tasks_list(request):
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    
    tasks = MaintenanceTask.objects.all().order_by('due_date')
    
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
        
    users = User.objects.all()

    # Handle Add Task POST
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        priority = request.POST.get('priority', 'medium')
        assigned_id = request.POST.get('assigned_to')
        due_date_str = request.POST.get('due_date')
        
        assigned_to = None
        if assigned_id:
            assigned_to = User.objects.get(pk=assigned_id)
            
        due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d').date()
        
        task = MaintenanceTask.objects.create(
            title=title, description=description, priority=priority,
            assigned_to=assigned_to, due_date=due_date
        )
        
        # Auto alert
        SystemAlert.objects.create(
            message=f"New maintenance task scheduled: '{task.title}' assigned to {assigned_to.username if assigned_to else 'unassigned'}.",
            alert_type='info'
        )
        return redirect('tasks')

    context = {
        'tasks': tasks,
        'users': users,
        'selected_status': status_filter,
        'selected_priority': priority_filter,
        'page_title': 'Maintenance Schedule'
    }
    return render(request, 'tasks.html', context)


# Update Task Status
def update_task_status(request, pk):
    if request.method == 'POST':
        task = get_object_or_404(MaintenanceTask, pk=pk)
        new_status = request.POST.get('status')
        if new_status in ['backlog', 'in_progress', 'completed']:
            task.status = new_status
            task.save()
            
            # Auto-alert on complete
            if new_status == 'completed':
                SystemAlert.objects.create(
                    message=f"Maintenance Task resolved: '{task.title}' completed successfully.",
                    alert_type='info'
                )
            return JsonResponse({'status': 'success', 'new_status': new_status})
    return JsonResponse({'status': 'error'}, status=400)


# Team Directory View
def team_list(request):
    # Get users with active tasks count annotation
    users = User.objects.annotate(
        active_tasks=Count('tasks', filter=models.Q(tasks__status__in=['backlog', 'in_progress']))
    ).order_by('username')
    
    # Handle Invite/Create Team User
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if username and password:
            User.objects.create_user(username=username, email=email, password=password)
            return redirect('team')

    context = {
        'users': users,
        'page_title': 'Operations Team'
    }
    return render(request, 'team.html', context)


# AI Chat & Control Hub View
@csrf_exempt
def ai_chat(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
    except json.JSONDecodeError:
        user_message = request.POST.get('message', '').strip()
        
    if not user_message:
        return JsonResponse({'status': 'error', 'message': 'Empty message'}, status=400)

    # Gather System Context for AI context building
    materials = Material.objects.all()
    tasks = MaintenanceTask.objects.all()
    alerts = SystemAlert.objects.filter(is_active=True)
    
    context_str = "SYSTEM STATUS SUMMARY:\n"
    context_str += "- Materials:\n"
    for m in materials:
        context_str += f"  * {m.name} [Category: {m.get_category_display()}, Qty: {m.quantity} {m.unit}, Min Required: {m.min_required}, Status: {m.status}]\n"
        
    context_str += "- Maintenance Tasks:\n"
    for t in tasks:
        context_str += f"  * {t.title} [Status: {t.get_status_display()}, Priority: {t.priority}, Due: {t.due_date}, Assigned: {t.assigned_to.username if t.assigned_to else 'None'}]\n"
        
    context_str += "- Active System Alerts:\n"
    for a in alerts:
        context_str += f"  * [{a.get_alert_type_display()}] {a.message} (Created: {a.created_at.strftime('%Y-%m-%d')})\n"

    # Check for actual Gemini Key
    gemini_key = os.environ.get('GEMINI_API_KEY')
    ai_response = ""

    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            system_prompt = (
                "You are 'Core AI Commander', the intelligent core of E-Core MMS (Material & Maintenance Management System). "
                "You have absolute visibility over system materials, scheduling, and error logs. "
                "Respond helpfully to user prompts. Keep responses professional, sleek, and action-oriented. "
                "If the user asks in Uzbek, answer in Uzbek. If in English, answer in English.\n\n"
                f"Here is the real-time system database state:\n{context_str}\n\n"
                "You can guide them on what materials are low, recommend tasks, or suggest scheduling adjustments."
            )
            
            response = model.generate_content([system_prompt, user_message])
            ai_response = response.text
        except Exception as e:
            ai_response = f"[Live AI Connection Failed: {str(e)}]\n\n"
            
    # Fallback/Local AI engine (highly versatile)
    if not ai_response:
        msg_lower = user_message.lower()
        
        # System status / Health checks
        if any(w in msg_lower for w in ['status', 'holat', 'salomatlik', 'health', 'tizim', 'system']):
            out_items = [m.name for m in materials if m.quantity <= 0]
            low_items = [m.name for m in materials if 0 < m.quantity <= m.min_required]
            
            response_uz = "🤖 **E-Core Tizim Statusi:**\n"
            if out_items:
                response_uz += f"⚠️ **Tugagan omborlar:** {', '.join(out_items)} (Miqdori: 0)\n"
            if low_items:
                response_uz += f"⚠️ **Kam qolgan materiallar:** {', '.join(low_items)}\n"
            if not out_items and not low_items:
                response_uz += "✅ Barcha materiallar omborda etarli darajada mavjud.\n"
                
            active_tasks = tasks.filter(status__in=['backlog', 'in_progress'])
            response_uz += f"🔧 Hozirda **{active_tasks.count()}** ta faol texnik vazifalar bor.\n"
            
            ai_response = response_uz
            
        # Add new tasks via Chat!
        elif any(w in msg_lower for w in ['task', 'task yarat', 'vazifa', 'add task', 'schedule', 'qo\'shish', 'yarat']):
            # Try to extract title, default if not found
            # e.g. "vazifa yarat: Generatorni tozalash"
            parsed_title = ""
            for sep in [':', 'yarat', 'task', 'vazifa']:
                if sep in msg_lower:
                    parts = user_message.split(sep)
                    if len(parts) > 1 and len(parts[1].strip()) > 3:
                        parsed_title = parts[1].strip()
                        break
            
            if not parsed_title:
                parsed_title = "Scheduled maintenance by AI Commander"
                
            # Create a maintenance task for tomorrow
            tomorrow = datetime.date.today() + datetime.timedelta(days=1)
            new_task = MaintenanceTask.objects.create(
                title=parsed_title,
                description="Auto-scheduled via E-Core AI Command Center.",
                status='backlog',
                priority='medium',
                due_date=tomorrow
            )
            
            # System Alert
            SystemAlert.objects.create(
                message=f"AI initiated scheduling: task '{new_task.title}' created.",
                alert_type='info'
            )
            
            ai_response = (
                f"✅ **Bajarildi!** Men yangi texnik vazifa yaratdim:\n"
                f"- **Vazifa:** {new_task.title}\n"
                f"- **Muddati:** {new_task.due_date}\n"
                f"- **Status:** Boshlang'ich (Backlog)\n\n"
                f"Tizim jadvali yangilandi."
            )
            
        # Low Stock / Inventory query
        elif any(w in msg_lower for w in ['ombor', 'material', 'inventory', 'stock', 'kam', 'low']):
            low_items = [f"{m.name} ({m.quantity} {m.unit} qoldi, min: {m.min_required})" for m in materials if m.quantity <= m.min_required]
            if low_items:
                ai_response = (
                    "⚠️ **Kam qolgan yoki tugagan materiallar ro'yxati:**\n\n" +
                    "\n".join([f"- {item}" for item in low_items]) +
                    "\n\n*Tavsiya: Ushbu materiallarni sotib olish uchun buyurtma bering.*"
                )
            else:
                ai_response = "✅ Hozirda barcha materiallar etarli miqdorda mavjud. Xavotirga o'rin yo'q!"
                
        # Hello/General welcome
        elif any(w in msg_lower for w in ['salom', 'hello', 'hi', 'hey', 'assalomu alaykum']):
            ai_response = (
                "👋 **Salom! Men E-Core AI Commander ko'makchisiman.**\n"
                "Men sizga E-Core MMS tizimini boshqarishda yordam beraman. Mendan so'rashingiz mumkin:\n"
                "- Tizim salomatligi yoki materiallar holati (`tizim holati`)\n"
                "- Kam qolgan materiallar ro'yxati (`kam qolgan materiallar`)\n"
                "- Yangi texnik vazifa qo'shish (`vazifa yarat: Generator moyini almashtirish`)\n\n"
                "Qanday yordam bera olaman?"
            )
            
        else:
            # Smart default chatbot
            ai_response = (
                "🤖 **E-Core AI Commander:** Buyrug'ingiz tushunilmadi.\n\n"
                "Tizim holati, kam qolgan materiallarni so'rashingiz yoki yangi texnik vazifalar kiritishimni so'rashingiz mumkin. "
                "Masalan: `vazifa yarat: Server bloklarini changdan tozalash`."
            )
            
    # Save log
    AIConversation.objects.create(user_message=user_message, ai_response=ai_response)
    
    return JsonResponse({
        'status': 'success',
        'reply': ai_response
    })

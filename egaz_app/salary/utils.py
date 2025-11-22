from django.utils import timezone
from egaz_app.models import Salary, Attendance, RoleSalaryPolicy, User

def calculate_user_salary(user, month=None, year=None, auto_create=True):
    print(f"🔍 CALCULATING SALARY for: {user.name}, Role: {user.role}")  # ADD THIS LINE
    
    if user.role.lower() == "admin":
        print("❌ Skipping admin user")  # ADD THIS LINE
        return None

    now = timezone.now()
    month = month or now.month
    year = year or now.year

    try:
        policy = RoleSalaryPolicy.objects.get(role=user.role)
        print(f"✅ Policy found: {policy.role}, Base: {policy.base_salary}")  # ADD THIS LINE
    except RoleSalaryPolicy.DoesNotExist:
        print(f"❌ No policy for role: {user.role}")  # ADD THIS LINE
        return None

    base_salary = policy.base_salary
    bonuses = policy.bonuses

    # Calculate deductions based on attendance
    attendance_records = Attendance.objects.filter(user=user, date__month=month, date__year=year)
    print(f"📅 Attendance records found: {attendance_records.count()}")  # ADD THIS LINE

    deduction = 0
    sick_days = 0

    for att in attendance_records:
        if att.status == "absent":
            deduction += policy.deduction_per_absent
        elif att.status == "sick":
            sick_days += 1
            if sick_days > 2:  # after 2 sick days → deduct
                deduction += policy.deduction_per_sick_day
        elif att.status in ["off", "accident"]:
            # ✅ No deduction
            continue

    total_salary = base_salary + bonuses - deduction

    if auto_create:
        # Get existing salary to preserve status if it exists
        existing_salary = Salary.objects.filter(
            user=user, 
            month=month, 
            year=year
        ).first()
        
        current_status = "Unpaid"  # Default status for new records
        
        if existing_salary:
            # Preserve the existing status
            current_status = existing_salary.status
            print(f"💰 Existing salary found, preserving status: {current_status}")  # ADD THIS LINE
        
        # ✅ ALWAYS CREATE/UPDATE SALARY RECORD regardless of attendance
        salary, created = Salary.objects.update_or_create(
            user=user,
            month=month,
            year=year,
            defaults={
                "policy": policy,
                "base_salary": base_salary,
                "bonuses": bonuses,
                "deductions": deduction,
                "total_salary": total_salary,
                "status": current_status,
            }
        )
        
        print(f"✅ {'CREATED' if created else 'UPDATED'} salary for {user.name}: ID={salary.salary_id}")  # ADD THIS
        return salary
    else:
        return {
            "base_salary": base_salary,
            "bonuses": bonuses,
            "deductions": deduction,
            "total_salary": total_salary,
        }
        
        
        
def update_salary_for_all_users(month=None, year=None):
    """
    Update or generate salary records for all active non-admin users.
    Preserves existing Paid/Unpaid status.
    """
    now = timezone.now()
    month = month or now.month
    year = year or now.year

    users = User.objects.filter(is_active=True).exclude(role__iexact="admin")
    updated_count = 0
    created_count = 0

    for user in users:
        salary = calculate_user_salary(user, month, year, auto_create=True)
        if salary:
            # Check if this was a new creation by looking for the default "Unpaid" status
            if salary.status == "Unpaid" and not Salary.objects.filter(
                user=user, month=month, year=year
            ).exclude(pk=salary.pk).exists():
                created_count += 1
            else:
                updated_count += 1

    return {"created": created_count, "updated": updated_count}
from django.utils import timezone
from egaz_app.models import Salary, Attendance, RoleSalaryPolicy, User

def calculate_user_salary(user, month=None, year=None, auto_create=True):
    if user.role.lower() == "admin":
        return None

    now = timezone.now()
    month = month or now.month
    year = year or now.year

    try:
        policy = RoleSalaryPolicy.objects.get(role=user.role)
    except RoleSalaryPolicy.DoesNotExist:
        return None

    base_salary = policy.base_salary
    bonuses = policy.bonuses

    attendance_records = Attendance.objects.filter(user=user, date__month=month, date__year=year)

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
            }
        )

        # Only set status if new record
        if created:
            salary.status = "Unpaid"
            salary.save()

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

    for user in users:
        salary = calculate_user_salary(user, month, year, auto_create=True)
        if salary:
            updated_count += 1

    return updated_count

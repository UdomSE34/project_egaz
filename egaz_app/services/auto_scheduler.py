# services/auto_scheduler.py
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from ..models import Schedule, Hotel
import logging

logger = logging.getLogger(__name__)


class AutoScheduler:

    # =========================
    # DATE HELPERS
    # =========================

    @staticmethod
    def get_current_monday():
        """Return Monday of the current week"""
        today = timezone.now().date()
        return today - timedelta(days=today.weekday())

    @staticmethod
    def get_monday_for_week(weeks_ahead=0):
        """Return Monday for current or future week"""
        current_monday = AutoScheduler.get_current_monday()
        return current_monday + timedelta(days=weeks_ahead * 7)

    # =========================
    # CORE SCHEDULER
    # =========================

    @staticmethod
    def regenerate_week(week_start_date):
        """
        Generate or update FULL schedules for a week.
        This ensures no partial-week issues.
        Safe to run multiple times.
        """
        days = [
            "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"
        ]
        slots = ["06:00 – 12:00", "06:00 – 18:00"]

        hotels = Hotel.objects.all()
        created_count = 0

        try:
            with transaction.atomic():  # All creations in a single transaction
                for hotel in hotels:
                    for day in days:
                        for slot in slots:
                            _, created = Schedule.objects.update_or_create(
                                hotel=hotel,
                                day=day,
                                slot=slot,
                                week_start_date=week_start_date,
                                defaults={
                                    "status": "Pending",
                                    "is_visible": True,
                                    "completion_notes": ""
                                }
                            )
                            if created:
                                created_count += 1
        except Exception as e:
            logger.error(f"Failed to regenerate week {week_start_date}: {str(e)}")

        logger.info(
            f"AutoScheduler: Regenerated week {week_start_date} "
            f"(created {created_count} schedules)"
        )
        return created_count

    # =========================
    # AUTO MAINTENANCE
    # =========================

    @staticmethod
    def ensure_upcoming_weeks():
        """
        Ensure next 2 weeks ALWAYS have full schedules.
        """
        try:
            current_monday = AutoScheduler.get_current_monday()
            weeks_to_maintain = [1, 2]  # next week & week after

            results = []

            for weeks_ahead in weeks_to_maintain:
                week_start = current_monday + timedelta(days=weeks_ahead * 7)
                created = AutoScheduler.regenerate_week(week_start)

                results.append({
                    "week_start": week_start,
                    "action": "regenerated",
                    "created": created
                })

            return {
                "action": "maintained",
                "results": results,
                "timestamp": timezone.now().isoformat()
            }

        except Exception as e:
            logger.error(f"AutoScheduler error: {str(e)}")
            return {
                "action": "error",
                "error": str(e),
                "timestamp": timezone.now().isoformat()
            }

    # =========================
    # INITIALIZATION
    # =========================

    @staticmethod
    def auto_initialize():
        """
        Ensure CURRENT week exists on system startup.
        """
        try:
            if not Hotel.objects.exists():
                return {"action": "skipped", "reason": "No hotels found"}

            current_monday = AutoScheduler.get_current_monday()
            created = AutoScheduler.regenerate_week(current_monday)

            return {
                "action": "initialized",
                "week_start": current_monday,
                "created": created
            }

        except Exception as e:
            logger.error(f"Auto-initialize error: {str(e)}")
            return {"action": "error", "error": str(e)}

    # =========================
    # WEEK LABELS / REPORTING
    # =========================

    @staticmethod
    def get_week_label(weeks_ahead):
        if weeks_ahead == 0:
            return "This Week"
        elif weeks_ahead == 1:
            return "Next Week"
        elif weeks_ahead == 2:
            return "Week After Next"
        return f"{weeks_ahead} Weeks Ahead"

    @staticmethod
    def get_weekly_overview():
        """
        Return overview for current + next 2 weeks.
        Auto-fixes upcoming weeks before reporting.
        """
        maintenance = AutoScheduler.ensure_upcoming_weeks()
        current_monday = AutoScheduler.get_current_monday()

        weeks = {}

        for weeks_ahead in range(0, 3):
            week_start = current_monday + timedelta(days=weeks_ahead * 7)
            qs = Schedule.objects.filter(week_start_date=week_start)

            weeks[f"week_{weeks_ahead}"] = {
                "week_start": week_start,
                "week_label": AutoScheduler.get_week_label(weeks_ahead),
                "schedule_count": qs.count(),
                "has_schedules": qs.exists(),
                "week_type": "current" if weeks_ahead == 0 else "upcoming"
            }

        return {
            "maintenance": maintenance,
            "weeks": weeks,
            "current_monday": current_monday,
            "timestamp": timezone.now().isoformat()
        }

    # =========================
    # CLEANUP OLD SCHEDULES
    # =========================

    @staticmethod
    def cleanup_old_schedules(keep_weeks=4):
        """
        Delete schedules older than N weeks.
        """
        try:
            current_monday = AutoScheduler.get_current_monday()
            cutoff = current_monday - timedelta(days=keep_weeks * 7)

            deleted, _ = Schedule.objects.filter(
                week_start_date__lt=cutoff
            ).delete()

            if deleted:
                logger.info(f"AutoScheduler: Deleted {deleted} old schedules")

            return {
                "action": "cleaned",
                "deleted": deleted,
                "cutoff_date": cutoff
            }

        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")
            return {"action": "error", "error": str(e)}

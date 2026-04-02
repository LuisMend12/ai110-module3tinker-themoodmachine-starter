"""
Automated test suite for PawPal+ (pawpal_system.py).

Run with:  python -m pytest
"""

import pytest
from datetime import datetime, date, timedelta

from pawpal_system import Owner, Pet, Task, Schedule


# ---------------------------------------------------------------------------
# Fixtures — reusable test objects
# ---------------------------------------------------------------------------

@pytest.fixture
def dog():
    return Pet(name="Biscuit", species="Dog", breed="Labrador", age=3)


@pytest.fixture
def cat():
    return Pet(name="Whiskers", species="Cat", breed="Tabby", age=5)


@pytest.fixture
def owner(dog):
    o = Owner(name="Alex", email="alex@example.com")
    o.add_pet(dog)
    return o


@pytest.fixture
def schedule(dog):
    return Schedule(pets=[dog])


# ---------------------------------------------------------------------------
# Owner tests
# ---------------------------------------------------------------------------

class TestOwner:
    def test_add_pet(self, owner, cat):
        owner.add_pet(cat)
        assert cat in owner.get_pets()

    def test_get_pets_returns_all(self, owner, cat):
        owner.add_pet(cat)
        assert len(owner.get_pets()) == 2

    def test_remove_pet_by_name(self, owner, dog):
        owner.remove_pet("Biscuit")
        assert dog not in owner.get_pets()

    def test_remove_nonexistent_pet_is_safe(self, owner):
        before = len(owner.get_pets())
        owner.remove_pet("Ghost")
        assert len(owner.get_pets()) == before

    def test_owner_starts_with_no_pets(self):
        o = Owner("Sam", "sam@example.com")
        assert o.get_pets() == []


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------

class TestPet:
    def test_add_and_get_task(self, dog):
        task = Task("Walk Biscuit", "walk", datetime(2026, 4, 2, 9, 0))
        dog.add_task(task)
        assert task in dog.get_tasks()

    def test_pet_with_no_tasks(self, dog):
        assert dog.get_tasks() == []
        assert dog.get_tasks_for_date(date(2026, 4, 2)) == []

    def test_get_tasks_for_date_filters_correctly(self, dog):
        today = datetime(2026, 4, 2, 9, 0)
        tomorrow = datetime(2026, 4, 3, 9, 0)
        t1 = Task("Walk", "walk", today)
        t2 = Task("Feed", "feeding", tomorrow)
        dog.add_task(t1)
        dog.add_task(t2)
        result = dog.get_tasks_for_date(date(2026, 4, 2))
        assert t1 in result
        assert t2 not in result


# ---------------------------------------------------------------------------
# Sorting tests
# ---------------------------------------------------------------------------

class TestSorting:
    def test_get_tasks_sorted_returns_chronological_order(self, dog):
        t1 = Task("Morning walk", "walk", datetime(2026, 4, 2, 8, 0))
        t2 = Task("Afternoon walk", "walk", datetime(2026, 4, 2, 14, 0))
        t3 = Task("Evening walk", "walk", datetime(2026, 4, 2, 18, 0))
        # Add out of order
        dog.add_task(t3)
        dog.add_task(t1)
        dog.add_task(t2)
        sorted_tasks = dog.get_tasks_sorted()
        assert sorted_tasks == [t1, t2, t3]

    def test_get_tasks_for_date_sorted(self, dog):
        t_late  = Task("Late walk",  "walk", datetime(2026, 4, 2, 17, 0))
        t_early = Task("Early walk", "walk", datetime(2026, 4, 2, 7, 0))
        dog.add_task(t_late)
        dog.add_task(t_early)
        result = dog.get_tasks_for_date(date(2026, 4, 2))
        assert result[0] == t_early
        assert result[1] == t_late

    def test_sorted_with_single_task(self, dog):
        t = Task("Walk", "walk", datetime(2026, 4, 2, 9, 0))
        dog.add_task(t)
        assert dog.get_tasks_sorted() == [t]

    def test_sorted_with_no_tasks(self, dog):
        assert dog.get_tasks_sorted() == []


# ---------------------------------------------------------------------------
# Conflict detection tests
# ---------------------------------------------------------------------------

class TestConflictDetection:
    def test_no_conflict_when_times_differ(self, dog, schedule):
        t1 = datetime(2026, 4, 2, 9, 0)
        t2 = datetime(2026, 4, 2, 11, 0)
        schedule.schedule_walk(dog, t1)
        assert not schedule.has_conflict(dog, t2)

    def test_conflict_detected_at_same_time(self, dog, schedule):
        same_time = datetime(2026, 4, 2, 9, 0)
        schedule.schedule_walk(dog, same_time)
        assert schedule.has_conflict(dog, same_time)

    def test_schedule_walk_raises_on_conflict(self, dog, schedule):
        same_time = datetime(2026, 4, 2, 9, 0)
        schedule.schedule_walk(dog, same_time)
        with pytest.raises(ValueError, match="already has a task"):
            schedule.schedule_walk(dog, same_time)

    def test_conflict_is_per_pet(self, dog, cat, schedule):
        """Same time slot is fine for two different pets."""
        schedule.add_pet(cat)
        same_time = datetime(2026, 4, 2, 9, 0)
        schedule.schedule_walk(dog, same_time)
        # Should NOT raise — cat has no tasks yet
        task = schedule.schedule_walk(cat, same_time)
        assert task is not None


# ---------------------------------------------------------------------------
# Recurrence logic tests
# ---------------------------------------------------------------------------

class TestRecurrence:
    def test_complete_non_recurring_task_returns_none(self, dog, schedule):
        task = schedule.schedule_walk(dog, datetime(2026, 4, 2, 9, 0), recur_daily=False)
        next_task = schedule.complete_task(dog, task)
        assert next_task is None
        assert task.completed is True

    def test_complete_recurring_task_creates_next_day(self, dog, schedule):
        original_time = datetime(2026, 4, 2, 9, 0)
        task = schedule.schedule_walk(dog, original_time, recur_daily=True)
        next_task = schedule.complete_task(dog, task)
        assert next_task is not None
        assert next_task.scheduled_at == original_time + timedelta(days=1)

    def test_recurring_task_marked_complete(self, dog, schedule):
        task = schedule.schedule_walk(dog, datetime(2026, 4, 2, 9, 0), recur_daily=True)
        schedule.complete_task(dog, task)
        assert task.completed is True

    def test_next_occurrence_added_to_pet(self, dog, schedule):
        original_time = datetime(2026, 4, 2, 9, 0)
        task = schedule.schedule_walk(dog, original_time, recur_daily=True)
        next_task = schedule.complete_task(dog, task)
        assert next_task in dog.get_tasks()

    def test_next_occurrence_inherits_recur_flag(self, dog, schedule):
        task = schedule.schedule_walk(dog, datetime(2026, 4, 2, 9, 0), recur_daily=True)
        next_task = schedule.complete_task(dog, task)
        assert next_task.recur_daily is True

    def test_chaining_recurrence(self, dog, schedule):
        """Completing day-2 task spawns day-3."""
        task = schedule.schedule_walk(dog, datetime(2026, 4, 2, 9, 0), recur_daily=True)
        day2 = schedule.complete_task(dog, task)
        day3 = schedule.complete_task(dog, day2)
        assert day3.scheduled_at.date() == date(2026, 4, 4)


# ---------------------------------------------------------------------------
# Schedule integration tests
# ---------------------------------------------------------------------------

class TestSchedule:
    def test_get_todays_tasks_empty(self, schedule):
        assert schedule.get_todays_tasks() == []

    def test_get_tasks_for_pet_empty(self, dog, schedule):
        assert schedule.get_tasks_for_pet(dog) == []

    def test_schedule_walk_happy_path(self, dog, schedule):
        t = schedule.schedule_walk(dog, datetime(2026, 4, 2, 9, 0))
        assert t in dog.get_tasks()
        assert t.task_type == "walk"

"""
PawPal+ — Logic Layer
Contains the core classes for the pet care management system.
"""

from dataclasses import dataclass, field
from datetime import datetime, date


@dataclass
class Task:
    """A single care task (walk, feeding, vet visit, etc.) for a pet."""
    title: str
    task_type: str          # e.g. "walk", "feeding", "vet", "grooming"
    scheduled_at: datetime
    notes: str = ""
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True


class Pet:
    """Represents a single pet owned by a user."""

    def __init__(self, name: str, species: str, breed: str, age: int) -> None:
        self.name = name
        self.species = species
        self.breed = breed
        self.age = age
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        return self.tasks

    def get_tasks_for_date(self, target_date: date) -> list[Task]:
        """Return tasks scheduled on a specific date."""
        return [t for t in self.tasks if t.scheduled_at.date() == target_date]

    def __repr__(self) -> str:
        return f"Pet(name={self.name!r}, species={self.species!r}, breed={self.breed!r}, age={self.age})"


class Owner:
    """Represents the human user of the PawPal+ app."""

    def __init__(self, name: str, email: str) -> None:
        self.name = name
        self.email = email
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        return self.pets

    def __repr__(self) -> str:
        return f"Owner(name={self.name!r}, email={self.email!r}, pets={len(self.pets)})"


class Schedule:
    """Coordinator that manages tasks across all pets."""

    def __init__(self, pets: list[Pet] | None = None) -> None:
        self.pets: list[Pet] = pets if pets is not None else []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this schedule."""
        self.pets.append(pet)

    def schedule_walk(self, pet: Pet, scheduled_at: datetime, notes: str = "") -> Task:
        """Create a walk task for a pet and attach it."""
        task = Task(
            title=f"Walk {pet.name}",
            task_type="walk",
            scheduled_at=scheduled_at,
            notes=notes,
        )
        pet.add_task(task)
        return task

    def get_todays_tasks(self) -> list[Task]:
        """Return all tasks across all pets scheduled for today."""
        today = date.today()
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.get_tasks_for_date(today))
        return tasks

    def get_tasks_for_pet(self, pet: Pet) -> list[Task]:
        """Return all tasks for a specific pet."""
        return pet.get_tasks()

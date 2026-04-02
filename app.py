"""
PawPal+ — Streamlit UI
Run with: streamlit run app.py
"""

import streamlit as st
from datetime import datetime, date, time

# Step 1: Import classes from the logic layer
from pawpal_system import Owner, Pet, Task, Schedule


# ---------------------------------------------------------------------------
# Step 2: Application "memory" via st.session_state
# ---------------------------------------------------------------------------
# st.session_state works like a dictionary that survives page re-runs.
# We check if our objects already exist before creating them, so they are
# not reset to empty every time the user clicks a button.

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Demo User", email="user@pawpal.com")

if "schedule" not in st.session_state:
    st.session_state.schedule = Schedule(pets=st.session_state.owner.pets)

# Convenience references
owner: Owner = st.session_state.owner
schedule: Schedule = st.session_state.schedule


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

st.title("PawPal+")
st.caption(f"Welcome, {owner.name}!")

tab_pets, tab_walk, tab_today = st.tabs(["My Pets", "Schedule a Walk", "Today's Tasks"])


# ---------------------------------------------------------------------------
# Tab 1 — Add / view pets
# ---------------------------------------------------------------------------

with tab_pets:
    st.subheader("Add a New Pet")

    with st.form("add_pet_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        pet_name    = col1.text_input("Pet name")
        pet_species = col2.selectbox("Species", ["Dog", "Cat", "Bird", "Rabbit", "Other"])
        pet_breed   = col1.text_input("Breed")
        pet_age     = col2.number_input("Age (years)", min_value=0, max_value=30, step=1)
        submitted   = st.form_submit_button("Add Pet")

    # Step 3: Wire the form submission to Owner.add_pet()
    if submitted:
        if not pet_name.strip():
            st.warning("Please enter a pet name.")
        else:
            new_pet = Pet(
                name=pet_name.strip(),
                species=pet_species,
                breed=pet_breed.strip(),
                age=int(pet_age),
            )
            owner.add_pet(new_pet)          # <-- logic-layer call
            schedule.add_pet(new_pet)       # keep Schedule in sync
            st.success(f"{new_pet.name} added!")

    st.divider()
    st.subheader("Your Pets")

    pets = owner.get_pets()                 # <-- logic-layer call
    if not pets:
        st.info("No pets yet. Add one above!")
    else:
        for pet in pets:
            with st.expander(f"{pet.name} ({pet.species})"):
                st.write(f"**Breed:** {pet.breed or '—'}")
                st.write(f"**Age:** {pet.age} yr")
                tasks = pet.get_tasks()
                st.write(f"**Tasks on file:** {len(tasks)}")
                if st.button(f"Remove {pet.name}", key=f"remove_{pet.name}"):
                    owner.remove_pet(pet.name)      # <-- logic-layer call
                    schedule.pets = owner.get_pets()
                    st.rerun()


# ---------------------------------------------------------------------------
# Tab 2 — Schedule a walk
# ---------------------------------------------------------------------------

with tab_walk:
    st.subheader("Schedule a Walk")

    pets = owner.get_pets()
    if not pets:
        st.info("Add a pet first before scheduling a walk.")
    else:
        with st.form("schedule_walk_form", clear_on_submit=True):
            pet_choice   = st.selectbox("Select pet", [p.name for p in pets])
            walk_date    = st.date_input("Date", value=date.today())
            walk_time    = st.time_input("Time", value=time(9, 0))
            walk_notes   = st.text_input("Notes (optional)")
            walk_submit  = st.form_submit_button("Schedule Walk")

        # Step 3: Wire the form to Schedule.schedule_walk()
        if walk_submit:
            target_pet   = next(p for p in pets if p.name == pet_choice)
            scheduled_at = datetime.combine(walk_date, walk_time)
            task = schedule.schedule_walk(          # <-- logic-layer call
                pet=target_pet,
                scheduled_at=scheduled_at,
                notes=walk_notes.strip(),
            )
            st.success(f"Walk scheduled for {target_pet.name} on "
                       f"{scheduled_at.strftime('%b %d at %I:%M %p')}!")


# ---------------------------------------------------------------------------
# Tab 3 — Today's tasks
# ---------------------------------------------------------------------------

with tab_today:
    st.subheader("Today's Tasks")
    st.caption(f"Date: {date.today().strftime('%A, %B %d %Y')}")

    todays_tasks = schedule.get_todays_tasks()      # <-- logic-layer call

    if not todays_tasks:
        st.info("No tasks scheduled for today.")
    else:
        for task in todays_tasks:
            status_icon = "✅" if task.completed else "🔲"
            col_info, col_btn = st.columns([4, 1])
            col_info.markdown(
                f"{status_icon} **{task.title}** — "
                f"{task.scheduled_at.strftime('%I:%M %p')}"
                + (f"  \n_{task.notes}_" if task.notes else "")
            )
            if not task.completed:
                if col_btn.button("Done", key=f"done_{id(task)}"):
                    task.mark_complete()            # <-- logic-layer call
                    st.rerun()

# ubc-timetabler

Course scheduling is hard. This helps.

Enter desired courses and get generated schedules.

![Example](example.jpg?raw=true "Example")

## Setup

`pip install -r requirements.txt`

## Usage

See `example.py` for example usage.

### Setting Constants

Set the constants to your liking:

* `COMMUTE_HOURS`
    * How long it takes you to commute **one-way** to campus
* `SESSION`
    * The session you would like to create schedules for
* `TERMS`
    * Tuple of terms you want to generate schedules for
* `NO_CACHE`
* `ALLOW_SAME_SLOT_SECTIONS`

### Setting Required and Optional Courses in `get_schedules`

* Enter all mandatory courses for the year in `required`
* For optional courses/electives, enter the electives you would potentially
like to take in `opt`, and the in `num_required_from_opt`, specify how many
electives you want to take.
    * If you want more fine-grained control, feel free to define custom
    combinations of your own and modify the code accordingly.

### Adding Constraints for Schedules

You'll find this line in the code:

```python
# I don't want any classes that start before 9:00AM
s.add_constraint(lambda sched: earliest_start(sched.activities) >= 9)
```

You can modify this, or add more like to define further constraints for
scheduling.

### Adding Constraints for Courses

Further, you'll find this:

```python
        # Add GEOG122 constraints if we need to
        if "GEOG 122" in courses:
            # STTs are for Vantage College students
            s.courses["GEOG 122"].add_constraint(
                lambda acts: all(a.status not in [u"STT"] for a in acts)
            )
            # Default sections contained a Tutorial but that is for Vantage
            # students, so removing that and only setting Lecture and Discussion
            s.courses["GEOG 122"].num_section_constraints = [
                (Lecture, 1), (Discussion, 1)
            ]
```

Use this is a template for adding constraints for courses if necessary.

### Unregisterable Courses

```python
# Add statuses for courses that shouldn't be considered
        bad_statuses = (
            "Full",
            # "Blocked",
        )
```

Modify the above as required (but "Full" and "Blocked" are good defaults).

### Sorting Schedules

```python
    # Sort
    # Statements in order from top-to-bottom from least-to-most important
    # i.e., put the most important at the bottom
    scheds = sort.free_days(scheds)
    scheds = sort.least_time_at_school(scheds, commute_hrs=COMMUTE_HOURS)
    scheds = sort.sum_latest_daily_morning(scheds)
    scheds = sort.even_time_per_day(scheds, commute_hrs=COMMUTE_HOURS)
    scheds = sort.even_courses_per_term(scheds)
```

Modify the above to your liking.

### Looking at the Results

Use the REPL in `example.py` to browse, and create worklists for schedules
you like.

```
python example.py
> help
```

![Example](example2.jpg?raw=true "Example")

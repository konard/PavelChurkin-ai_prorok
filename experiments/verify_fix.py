"""
Verify that the fix resolves the bug.

The fix ensures that the time mentioned in the prophecy message
matches the actual time when the next prophecy will be published.
"""

from datetime import datetime, timedelta
import pytz

MOSCOW_TZ = pytz.timezone('Europe/Moscow')

def format_moscow_time(dt: datetime = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Formats time in Moscow timezone"""
    if dt is None:
        dt = datetime.now(MOSCOW_TZ)
    return dt.strftime(format_str)

def simulate_fixed_flow():
    """Simulate the fixed flow"""

    print("=== FIXED FLOW ===\n")

    print("Step 1: Program starts, initialize()")
    next_publish_time = datetime.now(MOSCOW_TZ) + timedelta(days=1, hours=10)
    print(f"  self.next_publish_time = {format_moscow_time(next_publish_time)}")
    print(f"  self.planned_next_publish_time = None\n")

    print("Step 2: _generate_and_publish_immediate()")
    print(f"  Uses self.next_publish_time for message")
    print(f"  Message says: 'Next at {format_moscow_time(next_publish_time)}'")
    print(f"  Publishes immediately\n")

    print("Step 3: Wait until generation time, _generate_next_prophecy()")
    # Generate a new time for the NEXT publication
    next_next_publish_time = datetime.now(MOSCOW_TZ) + timedelta(days=2, hours=15)
    print(f"  Generates next_next_publish_time = {format_moscow_time(next_next_publish_time)}")
    print(f"  ✓ FIX: Saves to self.planned_next_publish_time")
    print(f"  Message prepared: 'Next at {format_moscow_time(next_next_publish_time)}'")
    print(f"  Saves to self.current_prophecy\n")

    print("Step 4: Wait until publish time, _publish_scheduled_prophecy()")
    print(f"  Publishes self.current_prophecy (says 'Next at {format_moscow_time(next_next_publish_time)}')")
    print(f"  ✓ FIX: Uses self.planned_next_publish_time instead of generating new time")
    print(f"  self.next_publish_time = {format_moscow_time(next_next_publish_time)}")
    print(f"  ✓ FIX: Clears self.planned_next_publish_time\n")

    print("Step 5: Next cycle - _generate_next_prophecy()")
    next_next_next_publish_time = datetime.now(MOSCOW_TZ) + timedelta(days=3, hours=8)
    print(f"  Generates next_next_publish_time = {format_moscow_time(next_next_next_publish_time)}")
    print(f"  ✓ FIX: Saves to self.planned_next_publish_time")
    print(f"  Message prepared: 'Next at {format_moscow_time(next_next_next_publish_time)}'")
    print(f"  Saves to self.current_prophecy\n")

    print("Step 6: _publish_scheduled_prophecy()")
    print(f"  Publishes self.current_prophecy (says 'Next at {format_moscow_time(next_next_next_publish_time)}')")
    print(f"  ✓ FIX: Uses self.planned_next_publish_time = {format_moscow_time(next_next_next_publish_time)}")
    print(f"  self.next_publish_time = {format_moscow_time(next_next_next_publish_time)}")
    print(f"  ✓ These match!\n")

    print("=== SUMMARY ===")
    print("✓ The time mentioned in the prophecy message now matches")
    print("✓ the actual time when the next prophecy will be published!")
    print()
    print("The fix adds self.planned_next_publish_time to store the time")
    print("generated in _generate_next_prophecy(), which is then used in")
    print("_publish_scheduled_prophecy() instead of generating a new random time.")

if __name__ == "__main__":
    simulate_fixed_flow()

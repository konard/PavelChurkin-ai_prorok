"""
Experiment script to trace the bug with incorrect next prophecy time.

The issue: when a prophecy is generated, it should include the correct time
for the NEXT prophecy, but it seems to be writing incorrect time.

Let's trace the logic:
1. First prophecy is generated and published immediately (_generate_and_publish_immediate)
2. Next prophecy is generated ahead of time (_generate_next_prophecy)
3. Next prophecy is published (_publish_scheduled_prophecy)

Let's see where the bug might be...
"""

from datetime import datetime, timedelta
import pytz

MOSCOW_TZ = pytz.timezone('Europe/Moscow')
GENERATION_OFFSET = 600

def format_moscow_time(dt: datetime = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Formates time in Moscow timezone"""
    if dt is None:
        dt = datetime.now(MOSCOW_TZ)
    return dt.strftime(format_str)

def simulate_bug():
    """Simulate the bug scenario"""

    print("=== SCENARIO 1: First prophecy (immediate) ===")
    # This is what happens in _generate_and_publish_immediate (line 393-425)

    # Assume we already have next_publish_time set (e.g., tomorrow at 10:00)
    next_publish_time = datetime.now(MOSCOW_TZ) + timedelta(days=1, hours=10)

    print(f"next_publish_time (already set): {format_moscow_time(next_publish_time)}")

    # Line 400-401: next_next_publish_time = self.next_publish_time
    next_next_publish_time = next_publish_time
    next_next_time_str = format_moscow_time(next_next_publish_time)

    print(f"BUG HERE! next_next_publish_time uses the CURRENT next_publish_time: {next_next_time_str}")
    print(f"This means the message will say 'Next prophecy at {next_next_time_str}'")
    print(f"But that's the time for THIS prophecy, not the next one!\n")

    print("=== SCENARIO 2: Scheduled prophecy generation (_generate_next_prophecy) ===")
    # This is what happens in _generate_next_prophecy (line 454-495)

    # Current next_publish_time (e.g., tomorrow at 10:00)
    current_next_publish_time = datetime.now(MOSCOW_TZ) + timedelta(days=1, hours=10)
    print(f"current next_publish_time: {format_moscow_time(current_next_publish_time)}")

    # Line 466-467: Generate NEXT NEXT publish time
    # This would be the day after tomorrow
    next_next_publish_time_correct = datetime.now(MOSCOW_TZ) + timedelta(days=2, hours=15)
    next_next_time_str_correct = format_moscow_time(next_next_publish_time_correct)

    print(f"next_next_publish_time (correctly generated): {next_next_time_str_correct}")

    # Line 470: current_publish_time_str = format_moscow_time(self.next_publish_time)
    current_publish_time_str = format_moscow_time(current_next_publish_time)

    # Line 471-472: The message being created
    full_message = f"🔮 Пророчество от бота ({current_publish_time_str} МСК):\n\n[prophecy]\n\n" \
                   f"⏰ Следующее пророчество будет опубликовано {next_next_time_str_correct} МСК"

    print(f"\nGenerated message says:")
    print(f"  - Current prophecy time: {current_publish_time_str}")
    print(f"  - Next prophecy time: {next_next_time_str_correct}")
    print(f"\nThis looks CORRECT!")

    print("\n=== ANALYSIS ===")
    print("The bug is in _generate_and_publish_immediate() at lines 400-401:")
    print("  next_next_publish_time = self.next_publish_time")
    print("  next_next_time_str = format_moscow_time(next_next_publish_time)")
    print("\nIt should call generate_next_publish_time() to create a NEW time,")
    print("not reuse the already-set self.next_publish_time")

if __name__ == "__main__":
    simulate_bug()

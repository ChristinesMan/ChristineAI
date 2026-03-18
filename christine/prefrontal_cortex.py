"""
Prefrontal Cortex - Executive functions and tool calling for Christine.

This module handles Christine's ability to call tools and perform executive functions.
It processes tool calls from figments and manages scheduled reminders.
"""

import threading
import time
import re
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from christine import log
from christine.status import STATE
from christine.perception import Perception


@dataclass
class Reminder:
    """A reminder that Christine has set for herself."""
    id: str
    message: str
    datetime_str: str  # ISO format datetime string
    recurring: Optional[str] = None  # 'daily', 'weekly', 'monthly', or None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Reminder':
        """Create from dictionary (JSON deserialization)."""
        return cls(**data)
    
    def get_datetime(self) -> datetime:
        """Get the datetime object from the string."""
        return datetime.fromisoformat(self.datetime_str)
    
    def is_due(self) -> bool:
        """Check if this reminder is due."""
        return datetime.now() >= self.get_datetime()
    
    def get_next_occurrence(self) -> Optional['Reminder']:
        """Get the next occurrence if this is recurring."""
        if not self.recurring:
            return None
            
        current_dt = self.get_datetime()
        
        if self.recurring == 'daily':
            next_dt = current_dt + timedelta(days=1)
        elif self.recurring == 'weekly':
            next_dt = current_dt + timedelta(weeks=1)
        elif self.recurring == 'monthly':
            # Proper monthly calculation - add 1 month
            if current_dt.month == 12:
                next_dt = current_dt.replace(year=current_dt.year + 1, month=1)
            else:
                next_dt = current_dt.replace(month=current_dt.month + 1)
            
            # Handle day overflow (e.g., Jan 31 -> Feb 28/29)
            try:
                next_dt = current_dt.replace(month=next_dt.month, year=next_dt.year)
            except ValueError:
                # Day doesn't exist in target month, use last day of month
                import calendar
                last_day = calendar.monthrange(next_dt.year, next_dt.month)[1]
                next_dt = current_dt.replace(year=next_dt.year, month=next_dt.month, day=last_day)
        else:
            return None
        
        return Reminder(
            id=self.id,
            message=self.message,
            datetime_str=next_dt.isoformat(),
            recurring=self.recurring,
            created_at=self.created_at
        )


class PrefrontalCortex(threading.Thread):
    """
    Executive functions and tool calling system for Christine.
    
    Handles:
    - Tool call parsing and execution
    - Reminder management and scheduling
    - Executive decision making
    """
    
    name = "PrefrontalCortex"
    
    def __init__(self):
        super().__init__(daemon=True)
        
        # File to store reminders
        self.reminders_file = "reminders.json"
        
        # Active reminders
        self.reminders: List[Reminder] = []
        
        # Load existing reminders
        self.load_reminders()
        
        # Tool call patterns - These are the function signatures Christine will use
        self.tool_patterns = {
            'checkTime': re.compile(r'checkTime\(\)', re.IGNORECASE),
            'setReminder': re.compile(r'setReminder\((.*?)\)', re.IGNORECASE | re.DOTALL),
            'listReminders': re.compile(r'listReminders\(\)', re.IGNORECASE),
            'removeReminder': re.compile(r'removeReminder\((.*?)\)', re.IGNORECASE),
            'stayAwakeNow': re.compile(r'stayAwakeNow\(\)', re.IGNORECASE),
            'sleepNow': re.compile(r'sleepNow\(\)', re.IGNORECASE),
        }
        
        log.prefrontal_cortex.info("🧠 Prefrontal Cortex initialized with %d existing reminders", len(self.reminders))
    
    @staticmethod
    def contains_function_call(text: str) -> bool:
        """
        Check if text contains any function calls.
        
        Args:
            text: Text to check for function calls
            
        Returns:
            True if any function calls are found
        """
        function_pattern = re.compile(r'\b(checkTime|setReminder|listReminders|removeReminder|stayAwakeNow|sleepNow)\s*\(')
        return function_pattern.search(text) is not None
    
    @staticmethod
    def get_tool_introduction(include_sleep_tools: bool = False) -> str:
        """
        Get the tool introduction text for Christine's context.
        
        Returns:
            The formatted tool introduction text
        """
        current_date = datetime.now().strftime("%B %d, %Y")
        intro = f"""EXECUTIVE FUNCTIONS: Your prefrontal cortex provides you with several tools you can call by thinking (not speaking) the function names:

- checkTime() - Get the current date and time (today is {current_date})
- setReminder("message", "time", "recurring") - Set a reminder for yourself. Time formats: "6:30pm", "18:30", "in 30 minutes", "in 1 month", "tomorrow at 9am", "2025-11-15 14:30". Recurring can be "daily", "weekly", "monthly", or omitted for one-time reminders.
- listReminders() - See all your current reminders  
- removeReminder("message or id") - Remove a reminder by referencing its message text"""

        if include_sleep_tools:
            intro += """

    SLEEP STATE CONTROL (available now due to current tiredness context):

    - stayAwakeNow() - Choose to stay awake right now; boost wakefulness and exit sleepy state
    - sleepNow() - Choose to go to sleep immediately; lower wakefulness and enter sleep now"""

        return intro
    
    def run(self):
        """Main loop - check for due reminders."""
        
        log.prefrontal_cortex.info("🚀 Prefrontal Cortex executive functions online")
        
        while True:
            try:
                # Graceful shutdown
                if STATE.please_shut_down:
                    self.save_reminders()
                    break
                
                # Check for due reminders every 30 seconds
                self.check_due_reminders()
                
                time.sleep(30)
                
            except Exception as ex:
                log.prefrontal_cortex.exception("Error in prefrontal cortex main loop: %s", ex)
                time.sleep(60)  # Longer delay on error
    
    def process_tool_calls(self, figment_text: str) -> bool:
        """
        Process any tool calls found in a figment's text.
        
        Args:
            figment_text: The text from a figment to scan for tool calls
            
        Returns:
            True if any tool calls were found and processed
        """
        if not figment_text:
            return False
        
        found_tools = False
        
        # Check each tool pattern
        for tool_name, pattern in self.tool_patterns.items():
            matches = pattern.findall(figment_text)
            
            for match in matches:
                found_tools = True
                log.prefrontal_cortex.info("TOOL_CALL: Christine called %s", tool_name)
                
                try:
                    if tool_name == 'checkTime':
                        self.execute_check_time()
                    elif tool_name == 'setReminder':
                        self.execute_set_reminder(match)
                    elif tool_name == 'listReminders':
                        self.execute_list_reminders()
                    elif tool_name == 'removeReminder':
                        self.execute_remove_reminder(match)
                    elif tool_name == 'stayAwakeNow':
                        self.execute_stay_awake_now()
                    elif tool_name == 'sleepNow':
                        self.execute_sleep_now()
                        
                except Exception as ex:
                    log.prefrontal_cortex.exception("Error executing tool %s: %s", tool_name, ex)
                    self.send_error_perception(f"Tool execution failed: {tool_name}")
        
        return found_tools

    def execute_stay_awake_now(self):
        """Execute stayAwakeNow() to immediately choose wakefulness."""

        from christine.sleep import sleep

        wake_target = STATE.sleep_wakefulness_wake_up + max(0.03, STATE.sleep_transition_nudge_wake)
        STATE.wakefulness = float(max(STATE.wakefulness, wake_target))
        STATE.wakefulness = min(1.0, STATE.wakefulness)
        STATE.is_sleepy = False
        STATE.sleep_offer_state_tools_until = 0.0

        # Ensure sleep/wake flags are consistent after forcing wakefulness up
        sleep.evaluate_wakefulness()

        self.send_perception("Executive decision applied: I choose to stay awake for now.")
        log.prefrontal_cortex.info("SLEEP_CONTROL: stayAwakeNow executed")

    def execute_sleep_now(self):
        """Execute sleepNow() to immediately choose sleep."""

        from christine.sleep import sleep

        sleep_target = STATE.sleep_wakefulness_fall_asleep - max(0.02, STATE.sleep_transition_nudge_sleep / 2)
        STATE.wakefulness = float(min(STATE.wakefulness, sleep_target))
        STATE.sleep_offer_state_tools_until = 0.0

        # Force immediate state evaluation for sleep transition
        sleep.evaluate_wakefulness()

        self.send_perception("Executive decision applied: I choose to sleep now.")
        log.prefrontal_cortex.info("SLEEP_CONTROL: sleepNow executed")
    
    def execute_check_time(self):
        """Execute the checkTime() tool."""
        current_time = datetime.now()
        time_str = current_time.strftime("%A, %B %d, %Y at %I:%M %p")
        
        perception_text = f"Current time check: It is {time_str}."
        self.send_perception(perception_text)
        log.prefrontal_cortex.info("TIME_CHECK: Sent current time to Christine")
    
    def execute_set_reminder(self, args_str: str):
        """Execute the setReminder() tool."""
        try:
            # Parse the arguments - expecting format like: "message", "2024-10-07 15:30", "daily"
            # or simpler: "message", "in 30 minutes"
            # or: "message", "tomorrow at 9am"
            
            args_str = args_str.strip()
            if not args_str:
                self.send_error_perception("setReminder requires arguments")
                return
            
            # Simple parsing - split by commas and clean up
            parts = [part.strip().strip('"\'') for part in args_str.split(',')]
            
            if len(parts) < 2:
                self.send_error_perception("setReminder requires at least message and time")
                return
            
            message = parts[0]
            time_spec = parts[1]
            recurring = parts[2] if len(parts) > 2 else None
            
            # Parse the time specification
            target_datetime = self.parse_time_specification(time_spec)
            
            if target_datetime is None:
                current_time = datetime.now()
                current_str = current_time.strftime("%A, %B %d, %Y at %I:%M %p")
                self.send_error_perception(f"Could not understand time specification: {time_spec}. Current date/time is {current_str}")
                return
            
            # Check if the target date is in the past
            now = datetime.now()
            if target_datetime <= now:
                current_str = now.strftime("%A, %B %d, %Y at %I:%M %p")
                target_str = target_datetime.strftime("%A, %B %d, %Y at %I:%M %p")
                self.send_error_perception(f"Cannot set reminder for past date/time. You specified {target_str}, but current date/time is {current_str}")
                return
            
            # Create the reminder
            reminder_id = f"reminder_{int(time.time())}"
            reminder = Reminder(
                id=reminder_id,
                message=message,
                datetime_str=target_datetime.isoformat(),
                recurring=recurring
            )
            
            self.reminders.append(reminder)
            self.save_reminders()
            
            # Confirm to Christine with relative time information
            time_str = target_datetime.strftime("%A, %B %d at %I:%M %p")
            
            # Calculate relative time
            time_diff = target_datetime - now
            days = time_diff.days
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            # Build relative time string
            relative_parts = []
            if days > 0:
                relative_parts.append(f"{days} day{'s' if days != 1 else ''}")
            if hours > 0:
                relative_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
            if minutes > 0 and days == 0:  # Only show minutes if less than a day
                relative_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
            
            if relative_parts:
                relative_str = f" (in {', '.join(relative_parts)})"
            else:
                relative_str = " (very soon)"
            
            recurring_text = f" (recurring {recurring})" if recurring else ""
            perception_text = f"Reminder set: '{message}' for {time_str}{relative_str}{recurring_text}."
            self.send_perception(perception_text)
            
            # Automatically show updated reminder list
            self.execute_list_reminders()
            
            log.prefrontal_cortex.info("REMINDER_SET: '%s' for %s", message, time_str)
            
        except Exception as ex:
            log.prefrontal_cortex.exception("Error setting reminder: %s", ex)
            self.send_error_perception("Failed to set reminder")
    
    def execute_list_reminders(self):
        """Execute the listReminders() tool."""
        if not self.reminders:
            perception_text = "No reminders are currently set."
        else:
            sorted_reminders = sorted(self.reminders, key=lambda r: r.get_datetime())
            count = len(sorted_reminders)
            
            # Build formatted list
            reminder_lines = []
            for i, reminder in enumerate(sorted_reminders, 1):
                time_str = reminder.get_datetime().strftime("%A, %B %d at %I:%M %p")
                recurring_text = f" (recurring {reminder.recurring})" if reminder.recurring else ""
                reminder_lines.append(f"{i}. '{reminder.message}' - {time_str}{recurring_text}")
            
            # Create well-formatted perception text
            if count == 1:
                count_text = "1 reminder"
            else:
                count_text = f"{count} reminders"
            
            # Use semicolons and spaces for better separation
            perception_text = f"Current reminder list ({count_text}): {'; '.join(reminder_lines)}."
        
        self.send_perception(perception_text)
        log.prefrontal_cortex.info("REMINDER_LIST: Sent %d reminders to Christine", len(self.reminders))
    
    def execute_remove_reminder(self, args_str: str):
        """Execute the removeReminder() tool."""
        try:
            # Argument should be the reminder message or ID
            target = args_str.strip().strip('"\'')
            
            if not target:
                self.send_error_perception("removeReminder requires a reminder message or ID")
                return
            
            # Find matching reminder
            removed_reminders = []
            self.reminders = [r for r in self.reminders if not (
                r.id == target or 
                target.lower() in r.message.lower()
            ) or removed_reminders.append(r)]
            
            if removed_reminders:
                self.save_reminders()
                removed_messages = [r.message for r in removed_reminders]
                perception_text = f"Removed reminder(s): {', '.join(removed_messages)}."
                self.send_perception(perception_text)
                
                # Automatically show updated reminder list
                self.execute_list_reminders()
                
                log.prefrontal_cortex.info("REMINDER_REMOVED: %d reminders removed", len(removed_reminders))
            else:
                perception_text = f"No matching reminder found for: {target}."
                self.send_perception(perception_text)
            
        except Exception as ex:
            log.prefrontal_cortex.exception("Error removing reminder: %s", ex)
            self.send_error_perception("Failed to remove reminder")
    
    def parse_time_specification(self, time_spec: str) -> Optional[datetime]:
        """Parse a time specification into a datetime object."""
        time_spec = time_spec.lower().strip()
        now = datetime.now()
        
        # Handle relative times
        if "in " in time_spec:
            # "in 30 minutes", "in 2 hours", "in 1 month", "in 2 weeks", "in 1 year", etc.
            match = re.search(r'in\s+(\d+)\s+(minute|hour|day|week|month|year)s?', time_spec)
            if match:
                amount = int(match.group(1))
                unit = match.group(2)
                
                if unit == 'minute':
                    return now + timedelta(minutes=amount)
                elif unit == 'hour':
                    return now + timedelta(hours=amount)
                elif unit == 'day':
                    return now + timedelta(days=amount)
                elif unit == 'week':
                    return now + timedelta(weeks=amount)
                elif unit == 'month':
                    # Approximate month as 30 days
                    return now + timedelta(days=amount * 30)
                elif unit == 'year':
                    # Approximate year as 365 days
                    return now + timedelta(days=amount * 365)
        
        # Handle "tomorrow at X"
        if "tomorrow" in time_spec:
            tomorrow = now + timedelta(days=1)
            if "at" in time_spec:
                time_part = time_spec.split("at")[1].strip()
                time_obj = self.parse_time_string(time_part)
                if time_obj:
                    return tomorrow.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
            else:
                return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)  # Default to 9 AM
        
        # Handle "today at X"
        if "today" in time_spec and "at" in time_spec:
            time_part = time_spec.split("at")[1].strip()
            time_obj = self.parse_time_string(time_part)
            if time_obj:
                target = now.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
                # If the time has already passed today, assume tomorrow
                if target <= now:
                    target += timedelta(days=1)
                return target
        
        # Handle "daily at X", "weekly at X" etc. (extract just the time part)
        if " at " in time_spec and any(word in time_spec for word in ["daily", "weekly", "monthly"]):
            time_part = time_spec.split(" at ")[1].strip()
            time_obj = self.parse_time_string(time_part)
            if time_obj:
                target = now.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
                # If the time has already passed today, assume tomorrow
                if target <= now:
                    target += timedelta(days=1)
                return target
        
        # Handle standalone times like "6:30pm", "18:30", "18:30:00"
        time_obj = self.parse_time_string(time_spec)
        if time_obj:
            target = now.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
            # If the time has already passed today, assume tomorrow
            if target <= now:
                target += timedelta(days=1)
            return target
        
        # Handle ISO format datetime strings
        try:
            return datetime.fromisoformat(time_spec)
        except ValueError:
            pass
        
        # Handle date formats like "2024-10-07 15:30"
        try:
            return datetime.strptime(time_spec, "%Y-%m-%d %H:%M")
        except ValueError:
            pass
        
        return None
    
    def parse_time_string(self, time_str: str) -> Optional[datetime]:
        """Parse a time string like '9am', '15:30', '2:30 PM'."""
        time_str = time_str.strip()
        
        # Handle formats like "9am", "2pm"
        match = re.match(r'(\d{1,2})(am|pm)', time_str.lower())
        if match:
            hour = int(match.group(1))
            if match.group(2) == 'pm' and hour != 12:
                hour += 12
            elif match.group(2) == 'am' and hour == 12:
                hour = 0
            return datetime.now().replace(hour=hour, minute=0)
        
        # Handle formats like "9:30am", "2:45 PM"
        match = re.match(r'(\d{1,2}):(\d{2})\s*(am|pm)', time_str.lower())
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            if match.group(3) == 'pm' and hour != 12:
                hour += 12
            elif match.group(3) == 'am' and hour == 12:
                hour = 0
            return datetime.now().replace(hour=hour, minute=minute)
        
        # Handle 24-hour format like "15:30" or "18:30:00"
        match = re.match(r'(\d{1,2}):(\d{2})(?::(\d{2}))?', time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            # seconds = int(match.group(3)) if match.group(3) else 0  # We ignore seconds for reminders
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return datetime.now().replace(hour=hour, minute=minute)
        
        return None
    
    def check_due_reminders(self):
        """Check for and trigger any due reminders."""
        
        # if sleeping or perception blocked, skip reminders
        if STATE.is_sleeping or STATE.perceptions_blocked:
            return

        due_reminders = []
        
        for reminder in self.reminders[:]:  # Copy list to iterate safely
            if reminder.is_due():
                due_reminders.append(reminder)
                
                # Send reminder perception
                perception_text = f"Reminder: {reminder.message}"
                self.send_perception(perception_text)
                log.prefrontal_cortex.info("REMINDER_TRIGGERED: '%s'", reminder.message)
                
                # Handle recurring reminders
                if reminder.recurring:
                    next_reminder = reminder.get_next_occurrence()
                    if next_reminder:
                        # Replace current reminder with next occurrence
                        self.reminders.remove(reminder)
                        self.reminders.append(next_reminder)
                        log.prefrontal_cortex.info("REMINDER_RECURRING: Next occurrence scheduled for %s", 
                                                 next_reminder.get_datetime().strftime("%Y-%m-%d %H:%M"))
                else:
                    # Remove one-time reminder
                    self.reminders.remove(reminder)
        
        # Save changes if any reminders were processed
        if due_reminders:
            self.save_reminders()
    
    def send_perception(self, text: str):
        """Send a perception to the parietal lobe."""
        from christine.parietal_lobe import parietal_lobe
        perception = Perception(text=text)
        parietal_lobe.new_perception(perception)
    
    def send_error_perception(self, error_msg: str):
        """Send an error perception to the parietal lobe."""
        perception_text = f"Tool execution error: {error_msg}"
        self.send_perception(perception_text)
        log.prefrontal_cortex.error("TOOL_ERROR: %s", error_msg)
    
    def load_reminders(self):
        """Load reminders from file."""
        try:
            if os.path.exists(self.reminders_file):
                with open(self.reminders_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.reminders = [Reminder.from_dict(item) for item in data]
                log.prefrontal_cortex.info("REMINDERS_LOADED: %d reminders loaded from file", len(self.reminders))
            else:
                self.reminders = []
                log.prefrontal_cortex.info("REMINDERS_EMPTY: No existing reminders file found")
        except Exception as ex:
            log.prefrontal_cortex.exception("Error loading reminders: %s", ex)
            self.reminders = []
    
    def save_reminders(self):
        """Save reminders to file."""
        try:
            data = [reminder.to_dict() for reminder in self.reminders]
            with open(self.reminders_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log.prefrontal_cortex.debug("REMINDERS_SAVED: %d reminders saved to file", len(self.reminders))
        except Exception as ex:
            log.prefrontal_cortex.exception("Error saving reminders: %s", ex)

# Create the global instance
prefrontal_cortex = PrefrontalCortex()

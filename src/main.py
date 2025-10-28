import os
import sys
import csv
import json
import pygame
import arabic_reshaper
from pathlib import Path
from hijri_converter import convert
from bidi.algorithm import get_display
from datetime import datetime, date, timedelta
from typing import Dict, Any, Tuple, Optional

# --- Configuration & Utility Functions ---

def rgb(r: int, g: int, b: int) -> Tuple[int, int, int]:
    """Helper function for defining colors."""
    return (r, g, b)

# Colors
WHITE = rgb(255, 255, 255)
BLACK = rgb(0, 0, 0)
GRAY = rgb(128, 128, 128)

# Predefined color themes
COLOR_THEMES = [
    {"PRIMARY": rgb(0, 34, 68), "SECONDARY": rgb(68, 162, 255)},
    {"PRIMARY": rgb(30, 30, 60), "SECONDARY": rgb(120, 120, 180)},
    {"PRIMARY": rgb(50, 20, 20), "SECONDARY": rgb(200, 100, 100)},
    {"PRIMARY": rgb(20, 40, 60), "SECONDARY": rgb(100, 150, 200)},
    {"PRIMARY": rgb(40, 20, 60), "SECONDARY": rgb(160, 100, 200)},
    {"PRIMARY": rgb(20, 60, 40), "SECONDARY": rgb(100, 200, 150)},
    {"PRIMARY": rgb(60, 40, 20), "SECONDARY": rgb(200, 150, 100)},
    {"PRIMARY": rgb(20, 20, 50), "SECONDARY": rgb(100, 100, 200)},
    {"PRIMARY": rgb(30, 50, 30), "SECONDARY": rgb(120, 180, 120)},
    {"PRIMARY": rgb(50, 30, 50), "SECONDARY": rgb(180, 120, 180)},
    {"PRIMARY": rgb(20, 50, 50), "SECONDARY": rgb(100, 200, 200)},
    {"PRIMARY": rgb(50, 50, 20), "SECONDARY": rgb(200, 200, 100)},
    {"PRIMARY": rgb(20, 20, 80), "SECONDARY": rgb(100, 100, 240)},
    {"PRIMARY": rgb(60, 30, 20), "SECONDARY": rgb(200, 150, 100)},
    {"PRIMARY": rgb(10, 20, 30), "SECONDARY": rgb(80, 120, 160)},
    {"PRIMARY": rgb(70, 30, 30), "SECONDARY": rgb(220, 110, 110)},
    {"PRIMARY": rgb(30, 60, 90), "SECONDARY": rgb(140, 180, 220)},
    {"PRIMARY": rgb(50, 10, 70), "SECONDARY": rgb(180, 90, 200)},
    {"PRIMARY": rgb(10, 70, 50), "SECONDARY": rgb(90, 210, 170)},
    {"PRIMARY": rgb(80, 50, 20), "SECONDARY": rgb(220, 170, 110)},
    {"PRIMARY": rgb(30, 30, 70), "SECONDARY": rgb(120, 120, 220)},
    {"PRIMARY": rgb(40, 70, 40), "SECONDARY": rgb(140, 210, 140)},
    {"PRIMARY": rgb(70, 40, 70), "SECONDARY": rgb(210, 140, 210)},
    {"PRIMARY": rgb(30, 70, 70), "SECONDARY": rgb(120, 220, 220)},
    {"PRIMARY": rgb(70, 70, 30), "SECONDARY": rgb(220, 220, 120)},
    {"PRIMARY": rgb(10, 10, 90), "SECONDARY": rgb(80, 80, 240)},
    {"PRIMARY": rgb(90, 40, 20), "SECONDARY": rgb(240, 170, 110)},
]

# Hijri month names mapping
HIJRI_MONTH_NAMES = {
    1: "Muharram", 2: "Safar", 3: "Rabi Al-Awwal", 4: "Rabi Al-Thani",
    5: "Jamada Al-Awwal", 6: "Jamada Al-Thani", 7: "Rajab", 8: "Shaban",
    9: "Ramadan", 10: "Shawwal", 11: "Dhul-Qadah", 12: "Dhul-Hijjah"
}

# Arabic prayer names
ARABIC_PRAYER_NAMES = {
    "Fajr": "فجر", "Dhuhr": "ظهر", "Asr": "عصر", "Maghrib": "مغرب",
    "Isha": "عشاء", "Jummah": "جمعة", "Sunrise": "شروق"
}

# File paths (portable)
BASE_DIR = Path(__file__).resolve().parent  # src directory
ASSET_PATH = str(BASE_DIR / "assets") + os.sep
FONT_PATH = ASSET_PATH + "fonts" + os.sep
PRAYER_TIMES_FILE = ASSET_PATH + "prayer_times.csv"
SETTINGS_FILE = ASSET_PATH + "settings.json"
ADHAN_SOUND_FILE = ASSET_PATH + "adhan.wav"

def format_prayer_time(time_str: str) -> str:
    """Convert time string from 'HH:MM' to 'HH:MM AM/PM' format."""
    if not time_str:
        return ""
    try:
        time_obj = datetime.strptime(time_str, '%H:%M')
        return time_obj.strftime('%I:%M %p')
    except ValueError:
        return ""

def load_prayer_times(filename: str) -> Dict[str, Dict[str, str]]:
    """Load prayer times from a CSV file."""
    prayer_times = {}
    try:
        with open(filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Use a dictionary comprehension to apply the formatting
                prayer_times[row["Date"]] = {
                    key: format_prayer_time(row[key])
                    for key in row if key != "Date"
                }
    except FileNotFoundError:
        print(f"Error: Prayer times file not found at {filename}")
    return prayer_times

def get_today_prayer_times(prayer_times: Dict[str, Dict[str, str]]) -> Optional[Dict[str, str]]:
    """Get today's prayer times."""
    today = date.today().strftime("%Y-%m-%d")
    return prayer_times.get(today, None)

def load_settings(default_settings: Dict[str, Any]) -> Dict[str, Any]:
    """Load settings from JSON file, using defaults if file is missing or corrupt."""
    try:
        with open(SETTINGS_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return default_settings.copy()

def save_settings(settings: Dict[str, Any]):
    """Save settings to JSON file."""
    try:
        with open(SETTINGS_FILE, "w") as file:
            json.dump(settings, file, indent=4)
    except IOError:
        print("Error: Could not save settings file.")

# --- Main Application Class ---

class MasjidDisplay:
    """The main class for the Pygame mosque prayer time display application."""

    def __init__(self):
        """Initialize Pygame, display, assets, and data."""
        pygame.init()
        pygame.mouse.set_visible(False)

        # 1. Display Setup
        # self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.window = pygame.display.set_mode((1600, 960)) # For testing in windowed mode

        pygame.display.set_caption('Masjid Nurul Islam')
        self.screen_width, self.screen_height = self.window.get_size()

        # 2. Settings and Theme Management
        self.default_settings = self._get_default_settings()
        self.settings = load_settings(self.default_settings)
        self.current_theme_index = self.settings.get("current_theme_index", 0)
        self.PRIMARY, self.SECONDARY = self._get_current_theme()

        # 3. Font Setup
        self.fonts = {}
        self._setup_fonts()

        # 4. Data and State
        self.current_date = date.today()
        self.prayer_times = load_prayer_times(PRAYER_TIMES_FILE)
        self.today_prayers = get_today_prayer_times(self.prayer_times)
        
        self.islamic_date_offset = -1  # Manual adjustment
        self.hide_eid_message = True
        
        # 5. Audio Setup
        self.adhan_sound = pygame.mixer.Sound(ADHAN_SOUND_FILE)
        self.adhan_sound.set_volume(1.0)
        self.beep_played: Dict[str, bool] = {
            "Fajr": False, "Dhuhr": False, "Asr": False,
            "Maghrib": False, "Isha": False, "Jummah": False
        }

    def _get_default_settings(self) -> Dict[str, Any]:
        """Returns the default settings dictionary based on screen size."""
        return {
            "current_theme_index": 0,
            "date_font_size": int(self.screen_height * 0.047),
            "islamic_date_font_size": int(self.screen_height * 0.042),
            "eid_announcement_font_size": int(self.screen_height * 0.042),
        }

    def _get_current_theme(self) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
        """Returns the primary and secondary colors for the current theme."""
        theme = COLOR_THEMES[self.current_theme_index % len(COLOR_THEMES)]
        return theme["PRIMARY"], theme["SECONDARY"]

    def _setup_fonts(self):
        """Initializes all Pygame Font objects with dynamic sizing."""
        sh = self.screen_height
        
        sizes = {
            "current_time": int(sh * 0.11),
            "text": int(sh * 0.05),
            "sub_text": int(sh * 0.029),
            "prayer_times": int(sh * 0.06),
            "arabic": int(sh * 0.06),
            "countdown_text": int(sh * 0.06),
            "countdown_value": int(sh * 0.3),
            "countdown_unit": int(sh * 0.06),
            # Loaded from settings, used for dynamic updates
            "date": self.settings.get("date_font_size"),
            "islamic_date": self.settings.get("islamic_date_font_size"),
            "eid_announcement": self.settings.get("eid_announcement_font_size"),
        }

        # Regular font styles
        self.fonts["current_time"] = pygame.font.Font(FONT_PATH + "regular.ttf", sizes["current_time"])
        self.fonts["prayer_times_adhan"] = pygame.font.Font(FONT_PATH + "regular.ttf", sizes["prayer_times"])
        self.fonts["prayer_times_jamat"] = pygame.font.Font(FONT_PATH + "regular.ttf", sizes["prayer_times"])
        self.fonts["date"] = pygame.font.Font(FONT_PATH + "regular.ttf", sizes["date"])
        self.fonts["islamic_date"] = pygame.font.Font(FONT_PATH + "regular.ttf", sizes["islamic_date"])
        self.fonts["countdown_value"] = pygame.font.Font(FONT_PATH + "regular.ttf", sizes["countdown_value"])

        # Medium font styles
        self.fonts["sub_text"] = pygame.font.Font(FONT_PATH + "medium.ttf", sizes["sub_text"])
        self.fonts["prayer_times"] = pygame.font.Font(FONT_PATH + "medium.ttf", sizes["prayer_times"])
        self.fonts["sunrise_text"] = pygame.font.Font(FONT_PATH + "medium.ttf", sizes["countdown_unit"])

        # Bold font styles
        self.fonts["text"] = pygame.font.Font(FONT_PATH + "bold.ttf", sizes["text"])
        self.fonts["eid_announcement"] = pygame.font.Font(FONT_PATH + "bold.ttf", sizes["eid_announcement"])
        self.fonts["countdown_text"] = pygame.font.Font(FONT_PATH + "bold.ttf", sizes["countdown_text"])
        self.fonts["countdown_unit"] = pygame.font.Font(FONT_PATH + "bold.ttf", sizes["countdown_unit"])

        # Arabic font styles
        self.fonts["prayer_times_arabic"] = pygame.font.Font(FONT_PATH + "arabic.ttf", sizes["arabic"])
        self.fonts["sunrise_arabic"] = pygame.font.Font(FONT_PATH + "arabic.ttf", sizes["arabic"])

    def _handle_input(self):
        """Handles keyboard and system events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            elif event.type == pygame.KEYDOWN:
                # --- Application Controls ---
                if event.key == pygame.K_ESCAPE:
                    self.quit() # Exit the application
                elif event.key == pygame.K_TAB:
                    self.reload_data() # Reload prayer times from CSV
                
                # --- Display & Theme Controls ---
                elif event.key in [pygame.K_RIGHT, pygame.K_LEFT]:
                    self._cycle_theme(event.key) # Change color theme
                elif event.key == pygame.K_SPACE:
                    self.hide_eid_message = not self.hide_eid_message # Toggle Eid message

                # --- Font Size Adjustments ---
                elif event.key in [pygame.K_2, pygame.K_1]:
                    self._adjust_font_size("date", event.key) # Adjust Gregorian date font
                elif event.key in [pygame.K_4, pygame.K_3]:
                    self._adjust_font_size("islamic_date", event.key) # Adjust Islamic date font
                elif event.key in [pygame.K_6, pygame.K_5] and not self.hide_eid_message:
                    self._adjust_font_size("eid_announcement", event.key) # Adjust Eid message font

                # --- Settings Reset ---
                elif event.key == pygame.K_BACKSPACE:
                    self._reset_settings() # Reset all settings to default

    def _cycle_theme(self, key):
        """Cycles through color themes and updates display colors."""
        n_themes = len(COLOR_THEMES)
        if key == pygame.K_RIGHT:
            self.current_theme_index = (self.current_theme_index + 1) % n_themes
        elif key == pygame.K_LEFT:
            self.current_theme_index = (self.current_theme_index - 1) % n_themes
        self.PRIMARY, self.SECONDARY = self._get_current_theme()

    def _adjust_font_size(self, font_key, key):
        """Adjusts font size, updates settings, and reloads the font."""
        size_key = f"{font_key}_font_size"
        current_size = self.settings.get(size_key)

        if key in [pygame.K_2, pygame.K_4, pygame.K_6]:
            new_size = current_size + 1
        else: # pygame.K_1, pygame.K_3, pygame.K_5
            new_size = max(1, current_size - 1)

        self.settings[size_key] = new_size
        self.fonts[font_key] = pygame.font.Font(FONT_PATH + "regular.ttf" if font_key in ["date", "islamic_date"] else FONT_PATH + "bold.ttf", new_size)

    def _reset_settings(self):
        """Resets all adjustable settings to their default values and updates fonts."""
        self.settings = self._get_default_settings()
        self.current_theme_index = self.settings["current_theme_index"]
        self.PRIMARY, self.SECONDARY = self._get_current_theme()
        self._setup_fonts() # Re-initialize fonts with default sizes

    def reload_data(self):
        """Reloads prayer times from the CSV file."""
        self.prayer_times = load_prayer_times(PRAYER_TIMES_FILE)
        self.today_prayers = get_today_prayer_times(self.prayer_times)
        print("Prayer times reloaded.")

    def _get_islamic_date(self, current_time: datetime) -> Tuple[int, str, int]:
        """Calculates the Hijri date, adjusting at Maghrib and applying manual offset."""
        today_gregorian = current_time.date()
        date_to_convert = today_gregorian

        # 1. Maghrib check for date rollover
        maghrib_time_str = self.today_prayers.get("Maghrib", "") if self.today_prayers else ""
        if maghrib_time_str:
            try:
                maghrib_time = datetime.strptime(maghrib_time_str, '%I:%M %p').replace(
                    year=current_time.year, month=current_time.month, day=current_time.day
                )
                if current_time >= maghrib_time:
                    date_to_convert += timedelta(days=1)
            except ValueError:
                pass # Use current day if Maghrib time is invalid

        # 2. Apply manual offset
        date_to_convert += timedelta(days=self.islamic_date_offset)

        # 3. Conversion
        hijri_date = convert.Gregorian(
            date_to_convert.year, date_to_convert.month, date_to_convert.day
        ).to_hijri()

        return hijri_date.day, HIJRI_MONTH_NAMES[hijri_date.month], hijri_date.year

    def _get_time_until_next_event(self) -> Tuple[Optional[str], int, int, int, bool]:
        """Calculates time remaining until the next Adhan or Iqamah."""
        if not self.today_prayers:
            return None, 0, 0, 0, False

        current_time = datetime.now()
        is_friday = current_time.weekday() == 4
        next_event = None
        min_time_diff = None
        is_iqamah = False

        # Define the order of checks
        prayer_order = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
        if is_friday:
            prayer_order[1] = "Jummah" # Use Jummah instead of Dhuhr

        # Check for events today
        for prayer in prayer_order:
            if not is_friday and prayer == "Jummah":
                continue # Skip Jummah on non-Fridays

            adhan_time_str = self.today_prayers.get(prayer, "")
            iqamah_time_str = self.today_prayers.get(f"{prayer}_Iqamah", "")

            # Combine Adhan and Iqamah times for comparison
            times_to_check = []
            if adhan_time_str:
                times_to_check.append((adhan_time_str, False))
            if iqamah_time_str and adhan_time_str != iqamah_time_str:
                times_to_check.append((iqamah_time_str, True))

            for time_str, is_iqamah_event in times_to_check:
                try:
                    event_time = datetime.strptime(time_str, '%I:%M %p').replace(
                        year=current_time.year, month=current_time.month, day=current_time.day
                    )
                    if event_time > current_time:
                        time_diff = event_time - current_time
                        if min_time_diff is None or time_diff < min_time_diff:
                            min_time_diff = time_diff
                            next_event = prayer
                            is_iqamah = is_iqamah_event
                except ValueError:
                    continue # Skip if time string is invalid

        # If no more events today, check for next day's Fajr
        if next_event is None:
            next_day = current_time + timedelta(days=1)
            next_day_str = next_day.strftime("%Y-%m-%d")
            next_day_prayers = self.prayer_times.get(next_day_str, None)

            if next_day_prayers:
                fajr_time_str = next_day_prayers.get("Fajr", "")
                if fajr_time_str:
                    try:
                        fajr_time = datetime.strptime(fajr_time_str, '%I:%M %p').replace(
                            year=next_day.year, month=next_day.month, day=next_day.day
                        )
                        time_diff = fajr_time - current_time
                        min_time_diff = time_diff
                        next_event = "Fajr"
                        is_iqamah = False
                    except ValueError:
                        pass

        # Format the result
        if min_time_diff:
            # Add one second to the countdown logic as per original code
            total_seconds = int(min_time_diff.total_seconds()) + 1
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return next_event, hours, minutes, seconds, is_iqamah

        return None, 0, 0, 0, False

    def _check_and_play_adhan(self, current_time: datetime):
        """Checks if it's time for Adhan or Iqamah and plays the sound."""
        if not self.today_prayers:
            return

        for prayer in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha", "Jummah"]:
            # Skip Dhuhr on Friday and Jummah on non-Friday
            is_friday = current_time.weekday() == 4
            if (prayer == "Dhuhr" and is_friday) or (prayer == "Jummah" and not is_friday):
                continue

            adhan_time_str = self.today_prayers.get(prayer, "")
            iqamah_time_str = self.today_prayers.get(f"{prayer}_Iqamah", "")

            # Helper to check and play for a specific time
            def check_time(time_str: str, key: str):
                if not time_str:
                    return

                try:
                    event_time = datetime.strptime(time_str, '%I:%M %p').replace(
                        year=current_time.year, month=current_time.month, day=current_time.day
                    )
                except ValueError:
                    return

                # Check if the current time just passed the event time (within 1 second)
                if event_time <= current_time < event_time + timedelta(seconds=1):
                    if not self.beep_played.get(key, False):
                        self.adhan_sound.play()
                        self.beep_played[key] = True
                elif current_time > event_time + timedelta(seconds=1):
                    # Reset the flag after the event has passed
                    self.beep_played[key] = False

            # Check Adhan
            check_time(adhan_time_str, prayer)
            # Check Iqamah (only if it's different from Adhan to avoid double beep)
            if iqamah_time_str and iqamah_time_str != adhan_time_str:
                check_time(iqamah_time_str, f"{prayer}_Iqamah")


    # --- Drawing Methods ---

    def _draw_background_and_masthead(self):
        """Draws the main background and the header sections."""
        sw, sh = self.screen_width, self.screen_height

        # Main background
        self.window.fill(self.PRIMARY)

        # Right-hand side (Info Panel)
        rect_width = int(sw * 0.365)
        rect_height = int(sh * 0.14)
        rect_x = sw - rect_width
        rect_y = 0
        
        # White rectangle (Top Right - Masjid Info)
        pygame.draw.rect(self.window, WHITE, (rect_x, rect_y, rect_width, rect_height))
        
        # Secondary color rectangle (Bottom Right - Countdown/Sunrise)
        second_rect_y = rect_y + rect_height
        second_rect_height = sh - second_rect_y
        pygame.draw.rect(self.window, self.SECONDARY, (rect_x, second_rect_y, rect_width, second_rect_height))

        # Black rectangle (Top Left - Clock/Date)
        third_rect_width = sw - rect_width
        third_rect_height = int(sh * 0.14)
        third_rect_x = 0
        third_rect_y = 0
        pygame.draw.rect(self.window, BLACK, (third_rect_x, third_rect_y, third_rect_width, third_rect_height))

        # Logical border position for date/time elements
        self.border_x = rect_x - int(sw * 0.005)

        # Render Masjid name and address (Top Right)
        title_text = self.fonts["text"].render("Masjid Nurul Islam", True, BLACK)
        title_text_rect = title_text.get_rect(center=(int(sw * 0.82), int(sh * 0.05)))
        subtext = self.fonts["sub_text"].render("615 Rutger St, Utica, NY 13501", True, BLACK)
        subtext_rect = subtext.get_rect(center=(int(sw * 0.82), int(sh * 0.10)))
        self.window.blit(title_text, title_text_rect)
        self.window.blit(subtext, subtext_rect)

    def _draw_date_and_time(self, current_time: datetime):
        """Draws the current time and Gregorian/Hijri dates in the top-left area."""
        sw, sh = self.screen_width, self.screen_height

        # Current Time
        current_time_str = current_time.strftime('%I:%M:%S %p')
        current_time_surface = self.fonts["current_time"].render(current_time_str, True, WHITE)
        current_time_rect = current_time_surface.get_rect(topleft=(int(sw * 0.02), int(sh * 0.01)))
        self.window.blit(current_time_surface, current_time_rect)

        # Gregorian Date
        current_date_str = current_time.strftime('%d %B %Y')
        center_x = sw // 2 + int(sw * 0.108)
        date_surface = self.fonts["date"].render(current_date_str, True, WHITE)
        date_rect = date_surface.get_rect(midleft=(center_x - int(sw * 0.204), current_time_rect.centery + int(sh * 0.02)))
        
        # Check if Gregorian date fits
        max_date_width = self.border_x - date_rect.left - int(sw * 0.01)
        if date_rect.width <= max_date_width:
            self.window.blit(date_surface, date_rect)

        # Islamic Date
        h_day, h_month, h_year = self._get_islamic_date(current_time)
        islamic_date_str = f"{str(h_day).zfill(2)} {h_month} {h_year}"
        islamic_date_surface = self.fonts["islamic_date"].render(islamic_date_str, True, GRAY)
        islamic_date_rect = islamic_date_surface.get_rect(midleft=(date_rect.left, date_rect.top - int(sh * 0.025)))

        # Check if Islamic date fits
        max_islamic_date_width = self.border_x - islamic_date_rect.left - int(sw * 0.01)
        if islamic_date_rect.width <= max_islamic_date_width:
            self.window.blit(islamic_date_surface, islamic_date_rect)

    def _draw_prayer_times(self):
        """Draws the table of prayer names, Adhan times, and Iqamah times."""
        if not self.today_prayers:
            return

        sw, sh = self.screen_width, self.screen_height
        center_x = sw // 2 + int(sw * 0.108)
        adhan_center_x = center_x - int(sw * 0.03)

        # Column Labels
        y_label = int(sh * 0.25) - int(sh * 0.05)
        adhan_label = self.fonts["prayer_times"].render("Adhan", True, self.SECONDARY)
        iqamah_label = self.fonts["prayer_times"].render("Iqamah", True, self.SECONDARY)
        
        self.window.blit(adhan_label, adhan_label.get_rect(center=(adhan_center_x - int(sw * 0.21), y_label)))
        self.window.blit(iqamah_label, iqamah_label.get_rect(center=(center_x - int(sw * 0.065), y_label)))

        y_offset = int(sh * 0.25)
        
        # Determine prayers to display
        prayer_list = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha", "Jummah"]
        
        self.eid_message_y = 0
        prayer_name_width = 0

        for prayer in prayer_list:
            time = self.today_prayers.get(prayer, "")
            iqamah_time = self.today_prayers.get(f"{prayer}_Iqamah", "")

            if time:
                # 1. English Prayer Name
                prayer_name_surface = self.fonts["prayer_times"].render(prayer.strip(), True, self.SECONDARY)
                prayer_name_width = max(prayer_name_width, prayer_name_surface.get_width())
                prayer_name_x = int(sw * 0.02)
                self.window.blit(prayer_name_surface, (prayer_name_x, y_offset))

                # 2. Adhan Time
                time_surface = self.fonts["prayer_times_adhan"].render(time, True, WHITE)
                time_rect = time_surface.get_rect(center=(adhan_center_x - int(sw * 0.21), y_offset + int(sh * 0.035)))
                self.window.blit(time_surface, time_rect)

                # 3. Iqamah Time
                if iqamah_time:
                    iqamah_surface = self.fonts["prayer_times_jamat"].render(iqamah_time, True, WHITE)
                    iqamah_rect = iqamah_surface.get_rect(center=(center_x - int(sw * 0.065), y_offset + int(sh * 0.035)))
                    self.window.blit(iqamah_surface, iqamah_rect)

                # 4. Arabic Prayer Name
                arabic_prayer = ARABIC_PRAYER_NAMES.get(prayer.strip(), "")
                reshaped_text = arabic_reshaper.reshape(arabic_prayer)
                bidi_text = get_display(reshaped_text)
                arabic_surface = self.fonts["prayer_times_arabic"].render(bidi_text, True, WHITE)
                
                # Position Arabic text just to the right of the English name
                arabic_rect = arabic_surface.get_rect(
                    topleft=(prayer_name_x + prayer_name_surface.get_width() + int(sw * 0.01), y_offset - int(sh * 0.015))
                )
                self.window.blit(arabic_surface, arabic_rect)

                # Move to the next row
                if self.hide_eid_message:
                    y_offset += int(sh * 0.125)
                else:
                    y_offset += int(sh * 0.10)
        
        self.eid_message_y = y_offset

    def _draw_eid_announcement(self):
        """Draws the configurable Eid announcement message."""
        if self.hide_eid_message:
            return

        sw, sh = self.screen_width, self.screen_height
        
        # Static Eid message (as in original code)
        eid_message = "Eid Salah will be held on June 6, 2025 at 08:30 AM"
        
        eid_message_surface = self.fonts["eid_announcement"].render(eid_message, True, self.SECONDARY)
        
        # Calculate center position to align with the prayer time columns
        center_x = sw // 2 + int(sw * 0.108)
        adhan_center_x = center_x - int(sw * 0.03)

        name_x = int(sw * 0.02) 
        adhan_x = adhan_center_x - int(sw * 0.21)
        iqamah_x = center_x - int(sw * 0.065)
        
        # Average of the three main column positions
        target_center_x = (name_x + adhan_x + iqamah_x) // 3
        
        eid_message_rect = eid_message_surface.get_rect(
            center=(target_center_x, self.eid_message_y + int(sh * 0.05))
        )
        
        # Manual adjustment from original code
        eid_message_rect.centerx -= int(sw * 0.013) 

        self.window.blit(eid_message_surface, eid_message_rect)

        # Draw the (empty) additional line for the second part of the message
        additional_eid_message = "" # Empty in original code
        additional_eid_message_surface = self.fonts["eid_announcement"].render(additional_eid_message, True, WHITE)
        additional_eid_message_rect = additional_eid_message_surface.get_rect(
            center=(eid_message_rect.centerx, eid_message_rect.bottom + int(sh * 0.02))
        )
        self.window.blit(additional_eid_message_surface, additional_eid_message_rect)

    def _draw_countdown(self):
        """Draws the countdown to the next prayer event and the Sunrise time."""
        sw, sh = self.screen_width, self.screen_height
        next_event, hours, minutes, seconds, is_iqamah = self._get_time_until_next_event()
        
        # Countdown Timer (Right Side)
        if next_event:
            # 1. Countdown Text
            event_name = 'Iqamah' if is_iqamah else next_event
            countdown_text = f"Time until {event_name}"
            countdown_text_surface = self.fonts["countdown_text"].render(countdown_text, True, self.PRIMARY)
            countdown_text_rect = countdown_text_surface.get_rect(center=(int(sw * 0.82), int(sh * 0.30)))
            self.window.blit(countdown_text_surface, countdown_text_rect)

            # 2. Countdown Value and Unit
            if hours > 0:
                value_text = f"{hours}"
                unit_text = "hour" if hours == 1 else "hours"
            elif minutes > 0:
                value_text = f"{minutes}"
                unit_text = "minute" if minutes == 1 else "minutes"
            else:
                value_text = f"{seconds}"
                unit_text = "second" if seconds == 1 else "seconds"
                
            countdown_value_surface = self.fonts["countdown_value"].render(value_text, True, WHITE)
            countdown_unit_surface = self.fonts["countdown_unit"].render(unit_text, True, self.PRIMARY)

            countdown_value_rect = countdown_value_surface.get_rect(center=(int(sw * 0.82), int(sh * 0.50)))
            
            # Position the unit text below the value
            countdown_unit_rect = countdown_unit_surface.get_rect(
                midtop=(countdown_value_rect.centerx, countdown_value_rect.bottom + int(sh * 0.00050))
            )

            self.window.blit(countdown_value_surface, countdown_value_rect)
            self.window.blit(countdown_unit_surface, countdown_unit_rect)
            
            # 3. Sunrise Time Display (Below Countdown)
            self._draw_sunrise(countdown_unit_rect)

    def _draw_sunrise(self, reference_rect: pygame.Rect):
        """Draws the Sunrise time display."""
        if not self.today_prayers:
            return

        sw, sh = self.screen_width, self.screen_height
        sunrise_time = self.today_prayers.get("Sunrise", "")
        
        if sunrise_time:
            # Text 'Sunrise' (English)
            sunrise_text_surface = self.fonts["sunrise_text"].render("Sunrise", True, self.PRIMARY)
            sunrise_text_x = reference_rect.centerx - int(sw * 0.05)
            y_pos = reference_rect.bottom + int(sh * 0.09)
            sunrise_text_rect = sunrise_text_surface.get_rect(center=(sunrise_text_x, y_pos))
            self.window.blit(sunrise_text_surface, sunrise_text_rect)

            # Text 'شروق' (Arabic)
            arabic_sunrise = ARABIC_PRAYER_NAMES.get("Sunrise", "")
            reshaped_text = arabic_reshaper.reshape(arabic_sunrise)
            bidi_text = get_display(reshaped_text)
            arabic_surface = self.fonts["sunrise_arabic"].render(bidi_text, True, self.PRIMARY)
            arabic_x = reference_rect.centerx + int(sw * 0.057)
            arabic_rect = arabic_surface.get_rect(center=(arabic_x, y_pos - int(sh * 0.003)))
            self.window.blit(arabic_surface, arabic_rect)

            # Sunrise Time
            sunrise_time_surface = self.fonts["prayer_times_jamat"].render(sunrise_time, True, WHITE)
            sunrise_time_x = reference_rect.centerx - int(sw * 0.005)
            sunrise_time_y = reference_rect.bottom + int(sh * 0.164)
            sunrise_time_rect = sunrise_time_surface.get_rect(center=(sunrise_time_x, sunrise_time_y))
            self.window.blit(sunrise_time_surface, sunrise_time_rect)

    # --- Main Loop and Execution ---

    def run(self):
        """The main application loop."""
        clock = pygame.time.Clock()
        
        while True:
            # 1. Event Handling
            self._handle_input()
            
            # 2. State Updates
            current_time = datetime.now()
            
            # Check for date change and reload data if necessary
            new_date = date.today()
            if new_date != self.current_date:
                self.current_date = new_date
                self.today_prayers = get_today_prayer_times(self.prayer_times)

            # Check and play Adhan/Iqamah sound
            if self.today_prayers:
                self._check_and_play_adhan(current_time)
            
            # 3. Drawing
            self._draw_background_and_masthead()
            self._draw_date_and_time(current_time)
            self._draw_prayer_times()
            self._draw_eid_announcement()
            self._draw_countdown()

            # 4. Display Update
            pygame.display.flip()
            clock.tick(15) # Limit to 15 FPS

    def quit(self):
        """Saves settings and gracefully exits Pygame."""
        
        save_settings({
            "current_theme_index": self.current_theme_index,
            "date_font_size": self.settings["date_font_size"],
            "islamic_date_font_size": self.settings["islamic_date_font_size"],
            "eid_announcement_font_size": self.settings["eid_announcement_font_size"],
        })
        
        save_settings(self.settings)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = MasjidDisplay()
    try:
        app.run()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        app.quit()
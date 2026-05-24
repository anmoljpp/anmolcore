"""Minimize Home Assistant for low-storage devices like Orange Pi.

This script strips unused integrations, fixes Python 3.14 syntax for 3.12
compatibility, and sets up a premium dark theme.

Usage:
    python3 script/minimize.py
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPONENTS_DIR = ROOT / "homeassistant" / "components"
TESTS_COMPONENTS_DIR = ROOT / "tests" / "components"

# ============================================================================
# Integrations to KEEP
# ============================================================================

KEEP_INTEGRATIONS: set[str] = {
    # User-requested
    "tuya",
    "bluetooth",
    "xiaomi_tv",
    "androidtv",
    "cast",
    "automation",
    "frontend",
    # System dependencies (transitive)
    "homeassistant",
    "http",
    "websocket_api",
    "auth",
    "api",
    "config",
    "onboarding",
    "lovelace",
    "blueprint",
    "trace",
    "device_automation",
    "webhook",
    "diagnostics",
    "file_upload",
    "repairs",
    "search",
    "system_log",
    "usb",
    "ffmpeg",
    "network",
    "zeroconf",
    # Automation helpers
    "script",
    "scene",
    "input_boolean",
    "input_number",
    "input_text",
    "input_select",
    "input_datetime",
    "input_button",
    # Essential system integrations
    "persistent_notification",
    "logger",
    "recorder",
    "history",
    "logbook",
    "sun",
    "zone",
    "person",
    "group",
    "notify",
    "tag",
    "conversation",
    # Entity platforms needed by kept integrations
    "media_player",
    "light",
    "switch",
    "sensor",
    "binary_sensor",
    "climate",
    "cover",
    "fan",
    "number",
    "select",
    "button",
    "remote",
    "siren",
    "alarm_control_panel",
    "camera",
    "humidifier",
    "vacuum",
    "lock",
    "text",
    "image",
    "event",
    "update",
    "weather",
    "calendar",
    "todo",
    "date",
    "datetime",
    "time",
    "valve",
    # Default config & its remaining deps
    "default_config",
    # Additional system deps discovered from manifests
    "device_tracker",
    "intent",
    "energy",
    "backup",
    "assist_pipeline",
    "analytics",
    "hardware",
    "hassio",
    "panel_custom",
}


def delete_unused_integrations() -> tuple[int, int]:
    """Delete integration directories not in KEEP_INTEGRATIONS."""
    deleted = 0
    kept = 0

    if not COMPONENTS_DIR.is_dir():
        print(f"ERROR: Components directory not found: {COMPONENTS_DIR}")
        return 0, 0

    for entry in sorted(COMPONENTS_DIR.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith("__"):
            kept += 1
            continue
        if entry.name in KEEP_INTEGRATIONS:
            kept += 1
            continue

        shutil.rmtree(entry)
        deleted += 1

        # Also delete matching test directory
        test_dir = TESTS_COMPONENTS_DIR / entry.name
        if test_dir.is_dir():
            shutil.rmtree(test_dir)

    return deleted, kept


def fix_except_syntax(directory: Path) -> int:
    """Fix 'except TypeA, TypeB:' to 'except (TypeA, TypeB):' for Python 3.12.

    PEP 758 (Python 3.14) allows unparenthesized multi-except.
    On Python 3.12, 'except ValueError, TypeError:' is silently
    misinterpreted as old Python 2 syntax (catch ValueError, bind to TypeError).
    """
    # Match: except <Name>, <Name>:  but NOT except <Name> as <name>:
    # We need to be careful not to match "except SomeError as e:"
    pattern = re.compile(
        r"^(\s*)except\s+(\w+(?:\.\w+)*)\s*,\s*(\w+(?:\.\w+)*)\s*:",
        re.MULTILINE,
    )

    fixed_count = 0

    for py_file in directory.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        # Check if this file has the pattern
        matches = list(pattern.finditer(content))
        if not matches:
            continue

        # Verify these are actually multi-except, not "except E as name"
        new_content = content
        for match in reversed(matches):
            indent = match.group(1)
            exc1 = match.group(2)
            exc2 = match.group(3)

            # Skip if second part looks like a variable name (as binding)
            # Python 2 style: except TypeError, e: -> this shouldn't exist
            # PEP 758 style: except TypeError, ValueError: -> both are exception types
            # Heuristic: if exc2 starts with uppercase, it's likely an exception type
            if not exc2[0].isupper():
                continue

            old = match.group(0)
            new = f"{indent}except ({exc1}, {exc2}):"
            new_content = new_content[:match.start()] + new + new_content[match.end():]
            fixed_count += 1

        if new_content != content:
            py_file.write_text(new_content, encoding="utf-8")

    return fixed_count


def fix_type_statements(directory: Path) -> int:
    """Convert PEP 695 'type X = Y' to 'X: TypeAlias = Y' for Python 3.12.

    While 'type' statements technically work in 3.12, they have subtle
    differences in behavior. Using TypeAlias is more compatible.
    """
    pattern = re.compile(r"^(type\s+)(\w+)(\s*=\s*)", re.MULTILINE)
    fixed_count = 0

    for py_file in directory.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        matches = list(pattern.finditer(content))
        if not matches:
            continue

        # Check if any match is actually a type statement (not in string/comment)
        new_content = content
        needs_import = False

        for match in reversed(matches):
            line_start = content.rfind("\n", 0, match.start()) + 1
            line = content[line_start : match.end()]

            # Skip if inside a string or comment
            if "#" in content[line_start : match.start()]:
                continue

            name = match.group(2)
            rest = match.group(3)
            old = match.group(0)
            new = f"{name}: TypeAlias{rest}"
            new_content = new_content[:match.start()] + new + new_content[match.end():]
            needs_import = True
            fixed_count += 1

        if needs_import and new_content != content:
            # Add TypeAlias import if not already present
            if "TypeAlias" not in content:
                # Try to add to existing typing import
                typing_import = re.search(
                    r"^from typing import (.+)$", new_content, re.MULTILINE
                )
                if typing_import:
                    imports = typing_import.group(1)
                    if "TypeAlias" not in imports:
                        new_imports = imports.rstrip() + ", TypeAlias"
                        new_content = new_content.replace(
                            typing_import.group(0),
                            f"from typing import {new_imports}",
                            1,
                        )
                else:
                    # Add a new import line after the last import
                    new_content = (
                        "from typing import TypeAlias\n" + new_content
                    )

            py_file.write_text(new_content, encoding="utf-8")

    return fixed_count


def fix_typevar_defaults(directory: Path) -> int:
    """Fix TypeVar(..., default=...) for Python 3.12.

    PEP 696 TypeVar defaults are Python 3.13+.
    Change 'from typing import TypeVar' to 'from typing_extensions import TypeVar'
    in files that use the default parameter.
    """
    fixed_count = 0

    for py_file in directory.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        if "TypeVar(" not in content or "default=" not in content:
            continue

        # Check if TypeVar is actually used with default=
        if not re.search(r"TypeVar\([^)]*default=", content):
            continue

        # Replace typing import with typing_extensions
        new_content = content

        # Handle "from typing import TypeVar" -> "from typing_extensions import TypeVar"
        # But keep other typing imports
        typing_import_match = re.search(
            r"^from typing import (.+)$", content, re.MULTILINE
        )
        if typing_import_match:
            imports = [
                i.strip()
                for i in typing_import_match.group(1).split(",")
            ]
            if "TypeVar" in imports:
                remaining = [i for i in imports if i != "TypeVar"]
                new_lines = []
                if remaining:
                    new_lines.append(
                        f"from typing import {', '.join(remaining)}"
                    )
                new_lines.append("from typing_extensions import TypeVar")
                new_content = new_content.replace(
                    typing_import_match.group(0),
                    "\n".join(new_lines),
                    1,
                )
                fixed_count += 1

        if new_content != content:
            py_file.write_text(new_content, encoding="utf-8")

    return fixed_count


def add_future_annotations(directory: Path) -> int:
    """Add 'from __future__ import annotations' to all Python files.

    The codebase relies on PEP 649 (Python 3.14) for lazy annotation evaluation.
    For Python 3.12, we need __future__ annotations to handle forward references.
    """
    added_count = 0
    future_import = "from __future__ import annotations"

    for py_file in directory.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        # Skip empty files
        if not content.strip():
            continue

        # Skip if already has the import
        if future_import in content:
            continue

        # Find insertion point: after docstring and any encoding declarations
        lines = content.split("\n")
        insert_idx = 0

        # Skip shebang
        if lines and lines[0].startswith("#!"):
            insert_idx = 1

        # Skip encoding declaration
        if insert_idx < len(lines) and re.match(
            r"^#.*coding[=:]\s", lines[insert_idx]
        ):
            insert_idx += 1

        # Skip module docstring
        if insert_idx < len(lines):
            line = lines[insert_idx].strip()
            if line.startswith('"""') or line.startswith("'''"):
                quote = line[:3]
                if line.count(quote) >= 2 and len(line) > 6:
                    # Single-line docstring
                    insert_idx += 1
                else:
                    # Multi-line docstring - find the end
                    insert_idx += 1
                    while insert_idx < len(lines):
                        if quote in lines[insert_idx]:
                            insert_idx += 1
                            break
                        insert_idx += 1

        # Skip blank lines after docstring
        while insert_idx < len(lines) and lines[insert_idx].strip() == "":
            insert_idx += 1

        # Insert the import
        lines.insert(insert_idx, future_import)

        # Add blank line after if next line isn't blank
        if insert_idx + 1 < len(lines) and lines[insert_idx + 1].strip():
            lines.insert(insert_idx + 1, "")

        new_content = "\n".join(lines)
        py_file.write_text(new_content, encoding="utf-8")
        added_count += 1

    return added_count


def update_default_config() -> None:
    """Update default_config to only reference kept integrations."""
    manifest_path = COMPONENTS_DIR / "default_config" / "manifest.json"
    if not manifest_path.exists():
        print("WARNING: default_config/manifest.json not found")
        return

    manifest = json.loads(manifest_path.read_text())

    # Only keep dependencies that still exist
    if "dependencies" in manifest:
        manifest["dependencies"] = [
            dep
            for dep in manifest["dependencies"]
            if dep in KEEP_INTEGRATIONS
        ]

    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n"
    )
    print(f"  Updated default_config manifest: {manifest['dependencies']}")


def create_premium_theme(config_dir: Path) -> None:
    """Create a premium dark theme configuration."""
    theme_config = """# Premium Dark Theme for Home Assistant
# Add this to your configuration.yaml

frontend:
  themes:
    premium_dark:
      # Primary palette
      primary-color: "#7C4DFF"
      accent-color: "#FF4081"

      # Backgrounds
      primary-background-color: "#0A0E14"
      secondary-background-color: "#111822"
      card-background-color: "#151D2B"

      # Text
      primary-text-color: "#E4E8EE"
      secondary-text-color: "#7E8A9A"
      text-primary-color: "#E4E8EE"

      # Header
      app-header-background-color: "#0A0E14"
      app-header-text-color: "#E4E8EE"

      # Sidebar
      sidebar-background-color: "#0A0E14"
      sidebar-text-color: "#C8CDD4"
      sidebar-selected-background-color: "rgba(124, 77, 255, 0.12)"
      sidebar-selected-icon-color: "#7C4DFF"
      sidebar-icon-color: "#7E8A9A"

      # Cards
      ha-card-background: "#151D2B"
      ha-card-border-color: "rgba(255,255,255,0.06)"
      ha-card-border-width: "1px"
      ha-card-border-radius: "18px"
      ha-card-box-shadow: "0 2px 16px rgba(0,0,0,0.35), 0 0 1px rgba(255,255,255,0.05)"

      # Switches & Toggles
      switch-checked-color: "#7C4DFF"
      switch-unchecked-color: "#2A3444"
      switch-checked-track-color: "rgba(124, 77, 255, 0.35)"

      # Dividers
      divider-color: "rgba(255,255,255,0.06)"

      # State icons
      state-icon-active-color: "#7C4DFF"
      state-icon-color: "#7E8A9A"

      # Sliders
      paper-slider-active-color: "#7C4DFF"
      paper-slider-knob-color: "#7C4DFF"
      paper-slider-container-color: "#2A3444"

      # Inputs
      input-fill-color: "#111822"
      input-ink-color: "#E4E8EE"
      input-label-ink-color: "#7E8A9A"
      input-idle-line-color: "#2A3444"
      input-dropdown-icon-color: "#7E8A9A"

      # Labels/Badges
      label-badge-background-color: "#151D2B"
      label-badge-text-color: "#E4E8EE"
      label-badge-red: "#FF4081"
      label-badge-green: "#00E676"
      label-badge-blue: "#7C4DFF"
      label-badge-yellow: "#FFD740"

      # Tabs
      paper-tabs-selection-bar-color: "#7C4DFF"

      # Dialog
      ha-dialog-border-radius: "18px"

      # Scrollbar
      scrollbar-thumb-color: "#2A3444"

      # Buttons
      mdc-button-outline-color: "#7C4DFF"

      # Toggle
      paper-toggle-button-checked-bar-color: "#7C4DFF"
      paper-toggle-button-checked-button-color: "#7C4DFF"

      # Table
      table-row-background-color: "#151D2B"
      table-row-alternative-background-color: "#111822"
      data-table-background-color: "#151D2B"

      # Markdown
      markdown-code-background-color: "#111822"
      code-editor-background-color: "#0A0E14"

      # Misc
      disabled-text-color: "#4A5568"
      error-color: "#FF5252"
      warning-color: "#FFB300"
      success-color: "#00E676"
      info-color: "#448AFF"

      # Chip
      ha-chip-background-color: "#1A2332"

      # Energy
      energy-grid-consumption-color: "#7C4DFF"
      energy-solar-color: "#FFD740"
      energy-battery-in-color: "#00E676"
      energy-battery-out-color: "#FF4081"

      modes:
        dark:
          primary-background-color: "#0A0E14"
"""
    theme_file = config_dir / "premium_theme.yaml"
    theme_file.write_text(theme_config)
    print(f"  Created premium theme at: {theme_file}")

    # Create a sample configuration.yaml snippet
    config_sample = config_dir / "configuration_snippet.yaml"
    config_sample.write_text(
        """# Add these lines to your configuration.yaml on the Orange Pi:

homeassistant:
  name: Home
  unit_system: metric

# Include the premium theme
frontend:
  themes: !include premium_theme.yaml

# Enable automations
automation: !include automations.yaml

# Enable scripts
script: !include scripts.yaml

# Enable scenes
scene: !include scenes.yaml

# Recorder - use minimal history for low storage
recorder:
  purge_keep_days: 3
  commit_interval: 30

# Logger - reduce logging for performance
logger:
  default: warning
  logs:
    homeassistant.core: info
    homeassistant.components.tuya: info
    homeassistant.components.bluetooth: info
"""
    )
    print(f"  Created config snippet at: {config_sample}")


def main() -> None:
    """Run the minimization process."""
    print("=" * 60)
    print("Home Assistant Minimizer for Orange Pi")
    print("=" * 60)
    print()

    ha_dir = ROOT / "homeassistant"

    # Step 1: Delete unused integrations
    print("[1/5] Deleting unused integrations...")
    deleted, kept = delete_unused_integrations()
    print(f"  Deleted {deleted} integrations, kept {kept}")
    print()

    # Step 2: Fix except syntax
    print("[2/5] Fixing Python 3.14 except syntax...")
    except_fixes = fix_except_syntax(ha_dir)
    print(f"  Fixed {except_fixes} except statements")
    print()

    # Step 3: Fix type statements
    print("[3/5] Converting type statements to TypeAlias...")
    type_fixes = fix_type_statements(ha_dir)
    print(f"  Converted {type_fixes} type statements")
    print()

    # Step 4: Fix TypeVar defaults
    print("[4/5] Fixing TypeVar defaults for Python 3.12...")
    typevar_fixes = fix_typevar_defaults(ha_dir)
    print(f"  Fixed {typevar_fixes} TypeVar defaults")
    print()

    # Step 5: Add from __future__ import annotations
    print("[5/5] Adding 'from __future__ import annotations'...")
    future_adds = add_future_annotations(ha_dir)
    print(f"  Added to {future_adds} files")
    print()

    # Update default_config
    print("Updating default_config...")
    update_default_config()
    print()

    # Create premium theme
    print("Creating premium dark theme...")
    config_dir = ROOT / "config"
    config_dir.mkdir(exist_ok=True)
    create_premium_theme(config_dir)
    print()

    # Summary
    print("=" * 60)
    print("MINIMIZATION COMPLETE")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Regenerate requirements:")
    print("     python3 -m script.gen_requirements_all")
    print()
    print("  2. Install in your Orange Pi venv:")
    print("     pip install -e .")
    print("     pip install -r requirements.txt")
    print()
    print("  3. Copy config files to your HA config directory:")
    print("     cp config/premium_theme.yaml ~/.homeassistant/")
    print("     # Add the snippet from config/configuration_snippet.yaml")
    print("     # to your ~/.homeassistant/configuration.yaml")
    print()
    print("  4. Start Home Assistant:")
    print("     python3 -m homeassistant -c ~/.homeassistant")
    print()
    print("  5. Set the theme in the UI:")
    print("     Profile -> Theme -> premium_dark")
    print()


if __name__ == "__main__":
    main()

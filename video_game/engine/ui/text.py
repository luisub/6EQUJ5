"""
MODULE: video_game/engine/ui/text.py
PURPOSE: Text editing buffer, monospace/pixel text wrapping, and scrollable transcript management.
CALLED BY: CRTTerminalScene in video_game/engine/scenes/terminal.py.
HOW TO MODIFY:
  - To adjust cursor blink rate or scrolling steps -> configure component defaults.
  - To change line wrapping rules -> edit wrap_text_chars() or wrap_text_pixels().
"""

from typing import List, Optional, Tuple
import pygame
from .. import config


def ellipsize_pixels(text: str, font, max_width_px: int) -> str:
    """Fit a preview label while indicating when its full text is elsewhere."""
    if font.size(text)[0] <= max_width_px:
        return text
    while text and font.size(text + '...')[0] > max_width_px:
        text = text[:-1]
    return text + '...' if text else ''


def wrap_text_chars(text: str, max_chars: int = 38) -> List[str]:
    """
    Wrap text into lines of at most max_chars length, preserving word boundaries.

    Handles explicit newlines and preserves indentation when appropriate.
    """
    if not text:
        return [""]

    lines: List[str] = []
    paragraphs = text.split("\n")

    for paragraph in paragraphs:
        if not paragraph:
            lines.append("")
            continue

        words = paragraph.split(" ")
        current_line: List[str] = []
        current_len = 0

        for word in words:
            word_len = len(word)
            # If a single word is longer than max_chars, chunk it
            if word_len > max_chars:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = []
                    current_len = 0
                for i in range(0, word_len, max_chars):
                    lines.append(word[i : i + max_chars])
                continue

            # Check if word fits on current line (including space)
            added_len = word_len + (1 if current_line else 0)
            if current_len + added_len <= max_chars:
                current_line.append(word)
                current_len += added_len
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_len = word_len

        if current_line:
            lines.append(" ".join(current_line))

    return lines


def wrap_text_pixels(text: str, font: pygame.font.Font, max_width_px: int) -> List[str]:
    """Wrap text so that every rendered line stays within max_width_px."""
    if max_width_px <= 0:
        raise ValueError('max_width_px must be positive')
    if not text:
        return [""]

    lines: List[str] = []
    paragraphs = text.split("\n")

    for paragraph in paragraphs:
        if not paragraph:
            lines.append("")
            continue

        words = paragraph.split(" ")
        current_line: List[str] = []

        for word in words:
            candidate = " ".join(current_line + [word]) if current_line else word
            width, _ = font.size(candidate)
            if width <= max_width_px:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = []
                # A long word must be split even after an existing line.
                chunk = ""
                for ch in word:
                    if chunk and font.size(chunk + ch)[0] > max_width_px:
                        lines.append(chunk)
                        chunk = ch
                    else:
                        chunk += ch
                if chunk:
                    current_line = [chunk]

        if current_line:
            lines.append(" ".join(current_line))

    return lines


class TextInputBuffer:
    """Maintains an interactive single-line text input buffer with cursor support."""

    def __init__(self, max_length: int = 128):
        self.text: str = ""
        self.cursor_pos: int = 0
        self.max_length: int = max_length
        self.is_active: bool = True

    def insert(self, chars: str) -> bool:
        """Insert printable characters at current cursor position."""
        if not chars:
            return False
        clean = "".join(ch for ch in chars if ch.isprintable())
        if not clean:
            return False

        remaining_cap = max(0, self.max_length - len(self.text))
        to_add = clean[:remaining_cap]
        if not to_add:
            return False

        self.text = self.text[:self.cursor_pos] + to_add + self.text[self.cursor_pos:]
        self.cursor_pos += len(to_add)
        return True

    def backspace(self) -> bool:
        """Delete character before cursor."""
        if self.cursor_pos > 0:
            self.text = self.text[:self.cursor_pos - 1] + self.text[self.cursor_pos:]
            self.cursor_pos -= 1
            return True
        return False

    def delete(self) -> bool:
        """Delete character at cursor."""
        if self.cursor_pos < len(self.text):
            self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos + 1:]
            return True
        return False

    def set_text(self, text: str):
        """Replace buffer text and reposition cursor at end."""
        clean = "".join(ch for ch in text if ch.isprintable())
        self.text = clean[:self.max_length]
        self.cursor_pos = len(self.text)

    def clear(self) -> str:
        """Reset text and cursor; return previous text."""
        old = self.text
        self.text = ""
        self.cursor_pos = 0
        return old

    def move_left(self):
        self.cursor_pos = max(0, self.cursor_pos - 1)

    def move_right(self):
        self.cursor_pos = min(len(self.text), self.cursor_pos + 1)

    def move_home(self):
        self.cursor_pos = 0

    def move_end(self):
        self.cursor_pos = len(self.text)

    def get_visible_slice(self, max_chars: int) -> Tuple[str, int]:
        """
        Return a window of (visible_string, cursor_index_in_slice) that keeps
        the cursor visible within max_chars width.
        """
        if len(self.text) <= max_chars:
            return self.text, self.cursor_pos

        # Center or shift window around cursor
        start = max(0, self.cursor_pos - max_chars + 4)
        if start + max_chars > len(self.text):
            start = max(0, len(self.text) - max_chars)
        slice_text = self.text[start : start + max_chars]
        slice_cursor = self.cursor_pos - start
        return slice_text, slice_cursor

    def get_visible_slice_pixels(self, font, max_width: int) -> Tuple[str, int]:
        """Keep the insertion point visible using the same measured font as drawing."""
        start = self.cursor_pos
        while start > 0 and font.size(self.text[start - 1:self.cursor_pos])[0] <= max_width:
            start -= 1
        end = self.cursor_pos
        while end < len(self.text) and font.size(self.text[start:end + 1])[0] <= max_width:
            end += 1
        return self.text[start:end], self.cursor_pos - start


class TranscriptScroller:
    """Manages scrollable, styled text lines for terminal conversation history."""

    def __init__(self, visible_lines: int = 12):
        self.lines: List[Tuple[str, Tuple[int, int, int]]] = []
        self.scroll_offset: int = 0
        self.visible_lines: int = visible_lines
        self.auto_scroll: bool = True

    def clear(self):
        self.lines.clear()
        self.scroll_offset = 0
        self.auto_scroll = True

    def add_line(self, text: str, color: Tuple[int, int, int] = config.COLOR_CRT_GREEN):
        self.lines.append((text, color))
        if self.auto_scroll:
            self.scroll_to_bottom()

    def add_wrapped(self, text: str, max_chars: int = 38, color: Tuple[int, int, int] = config.COLOR_CRT_GREEN):
        wrapped = wrap_text_chars(text, max_chars=max_chars)
        for line in wrapped:
            self.lines.append((line, color))
        if self.auto_scroll:
            self.scroll_to_bottom()

    def scroll_up(self, count: int = 1):
        max_offset = max(0, len(self.lines) - self.visible_lines)
        if max_offset > 0:
            self.scroll_offset = max(0, self.scroll_offset - count)
            if self.scroll_offset < max_offset:
                self.auto_scroll = False

    def scroll_down(self, count: int = 1):
        max_offset = max(0, len(self.lines) - self.visible_lines)
        if max_offset > 0:
            self.scroll_offset = min(max_offset, self.scroll_offset + count)
            if self.scroll_offset >= max_offset:
                self.auto_scroll = True

    def scroll_to_bottom(self):
        max_offset = max(0, len(self.lines) - self.visible_lines)
        self.scroll_offset = max_offset
        self.auto_scroll = True

    def get_visible_lines(self) -> List[Tuple[str, Tuple[int, int, int]]]:
        end = self.scroll_offset + self.visible_lines
        return self.lines[self.scroll_offset : end]

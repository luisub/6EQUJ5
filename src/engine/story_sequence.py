"""PURPOSE: Select and display authored story pages from earned campaign facts.
CALLED BY: video_game.engine.scenes.boss and focused story tests.
HOW TO MODIFY: Keep selection state-derived, fail closed on malformed content,
and preserve timed progression and input-neutral rendering.
"""
import json
from pathlib import Path

from .ui.dialogue import paginate, render_dialogue

STORY_PATH = Path(__file__).resolve().parent.parent / 'data' / 'act_01_story.json'
_ALLOWED = {'greenkeeper_defeated', 'dish_defense_completed', 'fasr_001_received', 'fasr_001_validated'}


def earned_story_pages(campaign, path=STORY_PATH):
    """Select only pages supported by the actual campaign snapshot.

    Invalid or missing authored data yields no pages, rather than an invented reward.
    """
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        pages = data['pages']
        if data.get('schema_version') != 1 or not isinstance(pages, list):
            return []
        if any(not isinstance(p, dict) or p.get('when') not in _ALLOWED or
               not isinstance(p.get('title'), str) or not p['title'] or
               not isinstance(p.get('text'), str) or not p['text'] for p in pages):
            return []
    except (OSError, ValueError, KeyError, TypeError):
        return []
    state = campaign.state
    flags = state.room_flags
    conditions = {
        'greenkeeper_defeated': flags.get('greenkeeper_defeated', False),
        'dish_defense_completed': flags.get('dish_defense_completed', False),
        'fasr_001_received': 'FASR-001' in state.extracted_fragments,
        'fasr_001_validated': any(r.get('id') == 'FASR-001' for r in state.validation_records),
    }
    # A story sequence is a reward for actual victory, even on malformed saves.
    if not conditions['greenkeeper_defeated']:
        return []
    return [dict(p) for p in pages if conditions[p['when']]]


class StorySequence:
    """Pages advance on a reading timer or an explicit next action."""
    def __init__(self, pages, seconds_per_page=6.0, *, font=None, auto_advance=True,
                 next_label='Continue', detail=''):
        self.pages = paginate(pages, font) if font is not None else list(pages)
        self.index = 0
        self.seconds_per_page = seconds_per_page
        self.remaining = seconds_per_page
        self.auto_advance = auto_advance
        self.next_label = next_label
        self.detail = detail

    @property
    def done(self):
        return self.index >= len(self.pages)

    def advance(self):
        if not self.done:
            self.index += 1
            self.remaining = self.seconds_per_page

    def update(self, dt):
        if self.auto_advance and not self.done:
            self.remaining -= max(0.0, dt)
            if self.remaining <= 0:
                self.advance()

    def render(self, crt, *, save_pending=False):
        if not self.pages or (self.done and not save_pending):
            return
        index = min(self.index, len(self.pages) - 1)
        render_dialogue(crt, self.pages[index], eyebrow='MISSION UPDATE',
                        progress=f'{index + 1} / {len(self.pages)}',
                        next_label=self.next_label if index == len(self.pages) - 1 else 'Next',
                        detail=self.detail, save_pending=save_pending)

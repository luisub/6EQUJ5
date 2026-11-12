# Controls documentation draft — pending final verification

This is a review draft, not the live controls document or an acceptance result. Final wording must reflect the actual integrated behavior and verification before updating `video_game/CONTROLS.md`.

## Suggested player-facing additions

**Combat profile:** Open pause/settings with F2 or controller Start, then choose `COMBAT`. Assisted is the default for fresh settings and makes the starter maser easier to use; Classic retains its earlier single-shot combat balance. Existing schema 1/2 settings load as Classic; the selection persists when changed. Movement speed, collision, boss vulnerability and weapon unlock rules remain unchanged.

**Mouse and keyboard:** Move with A/D or arrows; jump with Space, W or Up. Move the pointer to aim in field and boss scenes. With the starter maser, hold left mouse to repeat normal fire; hold and release right mouse to charge and fire a charged shot. Other unlocked weapons retain their own press/hold/release behavior. X/J/Left Ctrl retain the keyboard fire/charge action. Q cycles unlocked weapons. The pause panel also accepts a left click on a setting. Settings/profile changes are available without leaving the current game.

**Mapped controller:** Left stick or D-pad moves; right stick aims; With the starter maser, RT repeats normal fire and LT charges and releases; other unlocked weapons retain their own firing behavior. A jumps, B dashes, X interacts, Y grapples, LB cycles weapons, RB activates the selected ability, and Start pauses. Back opens the bunker dossier; D-pad/A/B navigate the available title/bunker/pause controls where supported. A real connected controller has not yet been independently checked. This increment does not establish full controller-only campaign, remapping or R02 acceptance: use the keyboard for free-text receiver interaction and advanced panels that do not expose controller navigation.

Losing focus, disconnecting a controller, opening a modal or changing input modes must not leave movement or fire held; interrupted charging cancels rather than firing. Exact supported modal/device behavior and any limits must be verified with the final tests and actual implementation before publishing this wording.

## Handoff note to complete after checks

Record fresh Assisted versus legacy Classic settings migration, input/aim and volley behavior, explicit dummy-SDL/fake-controller limits, first and final verified checks, any rendering/visual caveats and pending real-window/physical-hardware/human play. Do not promote R01, R02 or G2/G3 from this bounded increment. Preserve the existing controls and issue history using SHA-verified backups before changing shared files.

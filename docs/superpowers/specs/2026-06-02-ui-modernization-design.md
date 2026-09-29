# Violence Detection UI Modernization Design

Date: 2026-06-02

## Goal

Modernize the existing `main/violence_detection` Tkinter UI without replacing its core workflow. The application should remain recognizable: live camera first, system information visible, status and confidence prominent, and the same operational actions available. The new design should feel cleaner, more stable, more responsive, and easier to work with during real monitoring.

The report generation crash is part of this design scope. The report flow must become safe under common failure states instead of crashing the UI.

## Selected Direction

Use the `Responsive Operator Console` direction, adapted so it does not drift too far from the current UI.

Key decisions:

- Keep the live video as the main visual focus.
- Keep the title, start/stop/test/expand/report actions, system information, status bar, and confidence concept.
- Move from the current heavy dark-blue theme to a lighter modern operator panel.
- Use neutral surfaces, clear borders, readable metric cards, and restrained status colors.
- Preserve strong red/green alert semantics for violence detected / no violence.
- Keep scrollbar support, but make the layout compact enough that the primary information appears without awkward scrolling on normal desktop sizes.

## Layout

The main window is organized into five areas.

### Header

The header contains:

- Application title: `Şiddet Algılama Sistemi`
- Short context line: camera source, stream type, and model readiness
- Connection/model status badges

The header should be visually quieter than the video area. It should not consume excessive vertical space.

### Live View

The live video remains the primary content area.

The video area includes overlays for:

- Timestamp
- FPS and latency
- Current classification result
- Confidence score

The overlays should be readable but not cover important parts of the video. They should use compact pill or panel styling rather than large text blocks.

### Action Bar

The action bar contains:

- Start
- Stop
- Test Mode
- Expand/Shrink
- Generate Report

Start and Stop are primary operational actions. Test, expand, and report are secondary actions. Buttons should wrap cleanly on narrower windows and must not overlap or push text outside their bounds.

### Metrics Panel

The metrics panel shows the currently important values as scan-friendly cards:

- Result
- Confidence
- FPS
- Latency

On wide windows, this panel appears to the right of the live view. On narrow windows, it moves below the video.

### Status And Recent Events

The status panel shows:

- `Şiddet Yok` in a calm green state
- `Şiddet Algılandı` in a clear red alert state

The recent events panel shows whether violence events exist and, when possible, the latest event rows. Its purpose is to make report readiness visible before the user clicks the report button.

## Responsive Behavior

The UI must adapt inside Tkinter rather than assuming a fixed large screen.

Rules:

- Wide layout: video left, information/status panel right.
- Narrow layout: information/status panel moves below the video.
- Metric cards flow from 4 columns to 2 columns to 1 column as needed.
- Action buttons wrap to additional rows instead of shrinking into unreadable text.
- The existing scrollbar support remains as a fallback.
- No text, button, canvas, or metric element may overlap another UI element.
- Text must stay readable inside its container.

## Report Generation Safety

The `Rapor Oluştur` flow must not crash the application.

Expected behavior:

- If there are no violence events, show a user-facing message: `Rapor için kayıtlı şiddet olayı yok.`
- While a report is being generated, disable the report button or show a loading state so repeated clicks do not start multiple report jobs.
- If a screenshot path is missing, still generate the report and include a `görüntü bulunamadı` note for that event.
- If the database has missing columns or unexpected values, handle the error and show a short user-facing message.
- If font, image, or PDF creation fails, catch the error, keep the UI alive, and print detailed diagnostic output to the terminal.
- On success, show the generated report path and event count.

The recent events panel should help the user understand whether report generation is currently meaningful.

## Component Boundaries

The implementation should stay close to the current package structure.

### `DetectionGUI`

Responsible for layout, visual state, button states, and user messages.

It should own:

- Responsive layout decisions
- Start/stop button state
- Test mode button state
- Report button loading/disabled state
- Rendering the latest frame
- Rendering metrics and status
- Rendering recent event summary

### `ReportGenerator`

Responsible for reading events and building the PDF.

It should return enough structured information for the GUI to display a useful success or failure message. It should not rely on the GUI to understand internal PDF generation details.

### `AlarmManager`

Responsible for logging violence events and saving screenshots.

It should continue to guard screenshot writes and database writes so detection does not crash during alert moments.

## Error Handling

User-facing errors should be short and actionable. Terminal logs may include more detail.

Examples:

- No report data: `Rapor için kayıtlı şiddet olayı yok.`
- PDF error: `Rapor oluşturulamadı. Ayrıntılar terminalde.`
- Missing screenshot: the report continues and notes the missing image.

Errors should not leave buttons stuck in disabled/loading states.

## Acceptance Criteria

- The UI remains recognizable as the current violence detection application.
- The new visual style is modern, readable, and work-focused.
- The live camera, result, confidence, FPS, and latency are visible during normal operation.
- Small windows do not cause incoherent overlap or clipped button text.
- Action buttons wrap cleanly when the window is narrow.
- Start/stop cycles do not multiply UI update loops.
- Violence alert state is obvious but does not freeze or block the UI.
- `Rapor Oluştur` does not crash when there are no events.
- `Rapor Oluştur` does not crash when screenshots are missing.
- `Rapor Oluştur` does not crash on recoverable PDF, font, image, or database errors.
- Successful report generation shows the output path and event count.

## Out Of Scope

- Replacing Tkinter with a web app or another GUI framework.
- Retraining or changing the ML model.
- Changing detection semantics beyond UI/report safety needs.
- Adding authentication, remote dashboards, or multi-camera management.
- Redesigning generated PDF visuals beyond the crash-safe behavior needed here.

## Implementation Notes

The UI can be implemented incrementally:

1. Make report generation crash-safe.
2. Restructure the GUI into header, live view, action bar, metrics, status, and recent events areas.
3. Add responsive layout behavior and verify narrow/wide windows.
4. Polish theme, spacing, button states, and alert states.

This keeps the highest-risk bug fix first while allowing the visual modernization to land in controlled steps.

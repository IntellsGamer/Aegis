# RTL Dashboard Repair Validation

## Persian desktop inset

A fresh Waitress-served Persian dashboard at desktop width reported `dir="rtl"` and computed inline padding of `51.2px` on both edges of `.dashboard-hero`. Its content surface measured from x=32 to x=992 in the validation viewport, confirming the reading inset is active rather than the title being attached to the sidebar-facing edge.

The next check verifies the dark selected-navigation contrast against the same local browser build.

## Dark selected-navigation contrast

With dark mode active, the selected sidebar item resolved to a neutral graphite `rgb(52, 52, 49)` background, a light `rgb(247, 247, 242)` foreground, and a soft neutral border. The computed dashboard hero padding remained `51.2px` at both RTL inline edges. This eliminates the former dark-blue-on-cyan selected state while preserving a clear, thin cyan state marker.

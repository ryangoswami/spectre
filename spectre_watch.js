/**
 * SPECTRE — spectre_watch.js
 * KWin script that fires on every window focus change.
 * Outputs: SPECTRE|window title|app class
 * Read by daemon.py via journalctl -f
 */

workspace.windowActivated.connect(function(window) {
    if (window) {
        print("SPECTRE|" + window.caption + "|" + window.resourceClass);
    }
});

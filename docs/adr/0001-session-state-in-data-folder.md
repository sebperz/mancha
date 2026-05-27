# Session state stored alongside image data

Mancha persists Cell Type definitions, Calibration, per-mask Classifications, and window layout in a `.mancha` JSON file inside the user's image folder, rather than in the user's home config directory.

A project folder is fully portable — copying it also copies all classification work. A scientist can move the project between machines or share it with a collaborator without losing state.

**Considered alternative:** Store state in `~/.config/mancha/` per standard desktop conventions. Rejected because it decouples state from data, making sharing and backup fragile. A scientist who backs up their image folder would unknowingly lose all their classifications.

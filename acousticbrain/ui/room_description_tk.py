from pathlib import Path

from .room_description_adapter import (
    ListeningPositionFormRow,
    RoomDescriptionEditorAdapter,
    RoomDescriptionFormState,
    RoomOpeningFormRow,
    SpeakerPositionFormRow,
)


class RoomDescriptionTkApp:
    """Prototype Tkinter mince au-dessus de RoomDescriptionEditorAdapter."""

    def __init__(self, root=None, adapter=None):
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.adapter = adapter or RoomDescriptionEditorAdapter()
        self.root = root or tk.Tk()
        self.root.title("AcousticBrain — Description de salle")
        self.speakers = []
        self.listening_positions = []
        self.openings = []
        self.variables = {
            name: tk.StringVar()
            for name in ("name", "length_m", "width_m", "height_m")
        }
        self.status = tk.StringVar(value="")
        self._build()
        for variable in self.variables.values():
            variable.trace_add("write", lambda *_: self.validate())

    def run(self):
        self.root.mainloop()

    def _build(self):
        from tkinter import filedialog

        self.filedialog = filedialog
        frame = self.ttk.Frame(self.root, padding=12)
        frame.grid(sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        dimensions = self.ttk.LabelFrame(frame, text="Salle", padding=8)
        dimensions.grid(row=0, column=0, sticky="ew")
        for column, (field, label) in enumerate(
            (
                ("name", "Nom"),
                ("length_m", "Longueur (m)"),
                ("width_m", "Largeur (m)"),
                ("height_m", "Hauteur (m)"),
            )
        ):
            self.ttk.Label(dimensions, text=label).grid(row=0, column=column)
            self.ttk.Entry(
                dimensions, textvariable=self.variables[field], width=18
            ).grid(row=1, column=column, padx=3)

        self.speaker_tree = self._section(
            frame,
            row=1,
            title="Enceintes",
            columns=("speaker_id", "x_m", "y_m", "z_m"),
            add=self._add_speaker,
            remove=lambda: self._remove_selected(
                self.speaker_tree, self.speakers
            ),
        )
        self.listening_tree = self._section(
            frame,
            row=2,
            title="Positions d'écoute",
            columns=("position_id", "x_m", "y_m", "z_m"),
            add=self._add_listening_position,
            remove=lambda: self._remove_selected(
                self.listening_tree, self.listening_positions
            ),
        )
        self.opening_tree = self._section(
            frame,
            row=3,
            title="Ouvertures",
            columns=(
                "opening_id",
                "surface",
                "horizontal_offset_m",
                "vertical_offset_m",
                "width_m",
                "height_m",
            ),
            add=self._add_opening,
            remove=lambda: self._remove_selected(
                self.opening_tree, self.openings
            ),
        )

        actions = self.ttk.Frame(frame)
        actions.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        self.ttk.Button(actions, text="Charger", command=self.load).pack(
            side="left"
        )
        self.ttk.Button(actions, text="Enregistrer", command=self.save).pack(
            side="left", padx=6
        )
        self.ttk.Label(
            frame,
            textvariable=self.status,
            foreground="#9b1c1c",
            wraplength=900,
        ).grid(row=5, column=0, sticky="w", pady=(8, 0))

    def _section(self, parent, *, row, title, columns, add, remove):
        section = self.ttk.LabelFrame(parent, text=title, padding=8)
        section.grid(row=row, column=0, sticky="nsew", pady=(8, 0))
        tree = self.ttk.Treeview(
            section, columns=columns, show="headings", height=3
        )
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=125, stretch=True)
        tree.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.ttk.Button(section, text="Ajouter", command=add).grid(
            row=1, column=0, sticky="w", pady=(4, 0)
        )
        self.ttk.Button(section, text="Supprimer", command=remove).grid(
            row=1, column=1, sticky="e", pady=(4, 0)
        )
        section.columnconfigure(0, weight=1)
        return tree

    def _ask_values(self, title, fields):
        from tkinter import simpledialog

        values = []
        for field in fields:
            value = simpledialog.askstring(title, field, parent=self.root)
            if value is None:
                return None
            values.append(value)
        return values

    def _add_speaker(self):
        values = self._ask_values("Enceinte", ("Identifiant", "x", "y", "z"))
        if values is not None:
            self.speakers.append(SpeakerPositionFormRow(*values))
            self._refresh()

    def _add_listening_position(self):
        values = self._ask_values(
            "Position d'écoute", ("Identifiant", "x", "y", "z")
        )
        if values is not None:
            self.listening_positions.append(ListeningPositionFormRow(*values))
            self._refresh()

    def _add_opening(self):
        values = self._ask_values(
            "Ouverture",
            (
                "Identifiant",
                "Surface (FRONT_WALL/REAR_WALL/LEFT_WALL/RIGHT_WALL)",
                "Décalage horizontal",
                "Décalage vertical",
                "Largeur",
                "Hauteur",
            ),
        )
        if values is not None:
            self.openings.append(RoomOpeningFormRow(*values))
            self._refresh()

    def _remove_selected(self, tree, collection):
        selected = tree.selection()
        if selected:
            collection.pop(tree.index(selected[0]))
            self._refresh()

    def _refresh(self):
        for tree, rows in (
            (self.speaker_tree, self.speakers),
            (self.listening_tree, self.listening_positions),
            (self.opening_tree, self.openings),
        ):
            tree.delete(*tree.get_children())
            for row in rows:
                tree.insert("", "end", values=tuple(row.__dict__.values()))
        self.validate()

    def state(self):
        return RoomDescriptionFormState(
            name=self.variables["name"].get(),
            length_m=self.variables["length_m"].get(),
            width_m=self.variables["width_m"].get(),
            height_m=self.variables["height_m"].get(),
            speakers=tuple(self.speakers),
            listening_positions=tuple(self.listening_positions),
            openings=tuple(self.openings),
        )

    def set_state(self, state):
        for field in ("name", "length_m", "width_m", "height_m"):
            self.variables[field].set(getattr(state, field))
        self.speakers = list(state.speakers)
        self.listening_positions = list(state.listening_positions)
        self.openings = list(state.openings)
        self._refresh()

    def validate(self):
        result = self.adapter.validate(self.state())
        self._show_errors(result.errors)
        return result

    def load(self):
        path = self.filedialog.askopenfilename(filetypes=(("JSON", "*.json"),))
        if not path:
            return
        result = self.adapter.load(Path(path).read_text(encoding="utf-8"))
        if result.is_success:
            self.set_state(result.state)
        else:
            self._show_errors(result.errors)

    def save(self):
        result = self.adapter.serialize(self.state())
        if not result.is_success:
            self._show_errors(result.errors)
            return
        path = self.filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=(("JSON", "*.json"),),
        )
        if path:
            Path(path).write_text(result.payload, encoding="utf-8")
            self.status.set("")

    def _show_errors(self, errors):
        self.status.set(
            "\n".join(
                f"{error.code.value} — {'/'.join(map(str, error.path))}"
                for error in errors
            )
        )


def main():
    RoomDescriptionTkApp().run()


if __name__ == "__main__":
    main()

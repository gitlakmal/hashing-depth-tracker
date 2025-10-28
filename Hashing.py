import tkinter as tk
from tkinter import ttk
import threading
import time

BUCKET_SIZE = 3  # Max values per bucket


class Bucket:
    def __init__(self, depth):
        self.local_depth = depth
        self.values = []

    def is_full(self):
        return len(self.values) >= BUCKET_SIZE

    def insert(self, val):
        if val not in self.values:
            self.values.append(val)

    def delete(self, val):
        if val in self.values:
            self.values.remove(val)


class ExtendibleHashing:
    def __init__(self):
        self.global_depth = 2
        self.directory = {}
        for i in range(2 ** self.global_depth):
            key = format(i, f'0{self.global_depth}b')
            self.directory[key] = Bucket(depth=1)

    def hash(self, val):
        return format(val % (2 ** self.global_depth), f'0{self.global_depth}b')

    def insert(self, val):
        key = self.hash(val)
        bucket = self.directory[key]
        if not bucket.is_full():
            bucket.insert(val)
        else:
            if bucket.local_depth == self.global_depth:
                self.double_directory()
            self.split_bucket(key)
            self.insert(val)

    def delete(self, val):
        key = self.hash(val)
        bucket = self.directory[key]
        bucket.delete(val)

    def double_directory(self):
        self.global_depth += 1
        new_directory = {}
        for key, bucket in self.directory.items():
            new_directory['0' + key] = bucket
            new_directory['1' + key] = bucket
        self.directory = new_directory

    def split_bucket(self, key):
        old_bucket = self.directory[key]
        old_values = old_bucket.values.copy()
        old_bucket.values.clear()
        old_bucket.local_depth += 1

        new_bucket1 = Bucket(depth=old_bucket.local_depth)
        new_bucket2 = Bucket(depth=old_bucket.local_depth)

        for k in self.directory:
            if self.directory[k] == old_bucket:
                if k[-old_bucket.local_depth] == '0':
                    self.directory[k] = new_bucket1
                else:
                    self.directory[k] = new_bucket2

        for val in old_values:
            self.insert(val)


class HashingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌈 Extendible Hashing Simulator")
        self.root.geometry("780x520")
        self.root.configure(bg="#f4f7fb")

        style = ttk.Style()
        style.configure("TButton", font=("Arial", 11, "bold"), padding=6)
        style.configure("TEntry", padding=5)

        self.eh = ExtendibleHashing()

        # Frame for controls
        control_frame = ttk.Frame(root)
        control_frame.pack(pady=10)

        ttk.Label(control_frame, text="Enter Value:", font=("Arial", 11)).grid(row=0, column=0, padx=5)
        self.entry = ttk.Entry(control_frame, width=10)
        self.entry.grid(row=0, column=1, padx=5)

        ttk.Button(control_frame, text="➕ Insert", command=self.insert_value).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="🗑 Delete", command=self.delete_value).grid(row=0, column=3, padx=5)
        ttk.Button(control_frame, text="🔄 Reset", command=self.reset).grid(row=0, column=4, padx=5)

        # Binary info label
        self.info_label = tk.Label(
            root, text="⚙️ Binary value of inserted number will appear here.",
            font=("Consolas", 11), bg="#f4f7fb", fg="#333"
        )
        self.info_label.pack(pady=5)

        # Canvas for visualization
        self.canvas = tk.Canvas(root, width=740, height=380, bg="white", highlightthickness=1, highlightbackground="#ccc")
        self.canvas.pack(pady=10)

        self.draw()

    def show_temporary_popup(self, text, duration=3):
        """Show a fading popup for a few seconds."""
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.configure(bg="#333333")
        popup.attributes("-alpha", 0.9)

        label = tk.Label(popup, text=text, font=("Arial", 12, "bold"), fg="white", bg="#333333", padx=20, pady=10)
        label.pack()

        # Center popup
        self.root.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() // 2 - popup.winfo_reqwidth() // 2
        y = self.root.winfo_y() + 80
        popup.geometry(f"+{x}+{y}")

        def fade_out():
            time.sleep(duration)
            for i in range(10):
                popup.attributes("-alpha", 0.9 - i * 0.09)
                time.sleep(0.05)
            popup.destroy()

        threading.Thread(target=fade_out, daemon=True).start()

    def insert_value(self):
        try:
            val = int(self.entry.get())
            hashed = self.eh.hash(val)
            binary_full = format(val, "b")  # Full binary representation
            self.eh.insert(val)

            # Update label to show binary form
            self.info_label.config(
                text=f"✅ Inserted {val}\nFull Binary: {binary_full}\nHash ({self.eh.global_depth}-bit): {hashed}",
                fg="#00695c",
                font=("Consolas", 11, "bold")
            )

            # Show temporary popup
            self.show_temporary_popup(f"Inserted {val} → {hashed}")

            self.draw()
            self.entry.delete(0, tk.END)
        except ValueError:
            self.show_temporary_popup("⚠️ Please enter a valid integer!", duration=2)

    def delete_value(self):
        try:
            val = int(self.entry.get())
            self.eh.delete(val)
            self.info_label.config(
                text=f"🗑 Deleted {val}",
                fg="#b71c1c",
                font=("Consolas", 11, "bold")
            )
            self.show_temporary_popup(f"Deleted {val}", duration=2)
            self.draw()
            self.entry.delete(0, tk.END)
        except ValueError:
            self.show_temporary_popup("⚠️ Please enter a valid integer!", duration=2)

    def reset(self):
        self.eh = ExtendibleHashing()
        self.info_label.config(
            text="🔄 Table reset. Insert a new value to see its binary and hash.",
            fg="#333",
            font=("Consolas", 11)
        )
        self.show_temporary_popup("Reset Complete!", duration=2)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        x, y = 20, 20
        self.canvas.create_text(x, y, anchor="nw", text=f"🌍 Global Depth: {self.eh.global_depth}", font=("Arial", 13, "bold"), fill="#333")
        y += 30

        buckets_drawn = {}
        for key in sorted(self.eh.directory.keys()):
            bucket = self.eh.directory[key]
            if bucket not in buckets_drawn:
                buckets_drawn[bucket] = f"B{len(buckets_drawn)}"

            label = buckets_drawn[bucket]
            values = ', '.join(str(v) for v in bucket.values)
            color = "#e0f7fa" if int(key, 2) % 2 == 0 else "#ffe0b2"

            self.canvas.create_rectangle(x, y, x + 700, y + 25, fill=color, outline="#aaa")
            self.canvas.create_text(x + 10, y + 5, anchor="nw",
                                    text=f"{key} → {label} (LD: {bucket.local_depth}) [{values}]",
                                    font=("Consolas", 10))
            y += 30


if __name__ == "__main__":
    root = tk.Tk()
    app = HashingApp(root)
    root.mainloop()

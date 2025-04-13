import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from database import connect_db, execute_query, fetch_mobs, fetch_all_loot, fetch_mob_loot_config, get_loot_for_mob
import psycopg2
import os
from PIL import Image, ImageTk

class AddMobDialog(tk.Toplevel):
    def __init__(self, parent, refresh_callback):
        super().__init__(parent)
        self.title("Добавить моба")
        self.parent = parent
        self.refresh_callback = refresh_callback
        self.avatar_dir = "avatars"
        self.avatar_files = [""] + [f for f in os.listdir(self.avatar_dir) if os.path.isfile(os.path.join(self.avatar_dir, f))]
        self.avatar_var = tk.StringVar(self)
        self.avatar_var.set(self.avatar_files[0])
        self.current_image = None

        self.init_ui()

    def init_ui(self):
        # --- Имя моба ---
        name_label = ttk.Label(self, text="Имя моба:")
        name_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = ttk.Entry(self)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # --- Выбор аватарки ---
        avatar_label = ttk.Label(self, text="Аватарка:")
        avatar_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.avatar_combobox = ttk.Combobox(self, textvariable=self.avatar_var, values=self.avatar_files, state="readonly")
        self.avatar_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.avatar_combobox.bind("<<ComboboxSelected>>", self.update_avatar_preview)

        # --- Предпросмотр аватарки ---
        self.avatar_preview_label = ttk.Label(self)
        self.avatar_preview_label.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        self.update_avatar_preview(None)

        # --- Кнопки ---
        add_button = ttk.Button(self, text="Добавить", command=self.add_mob)
        add_button.grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        self.grid_columnconfigure(1, weight=1)

    def update_avatar_preview(self, event):
        selected_file = self.avatar_var.get()
        if selected_file:
            file_path = os.path.join(self.avatar_dir, selected_file)
            try:
                img = Image.open(file_path)
                img.thumbnail((100, 100))
                self.current_image = ImageTk.PhotoImage(img)
                self.avatar_preview_label.config(image=self.current_image)
            except Exception as e:
                print(f"Ошибка при загрузке изображения для предпросмотра: {e}")
                self.avatar_preview_label.config(image=None, text="Ошибка загрузки")
        else:
            self.avatar_preview_label.config(image=None, text="Нет аватара")

    def add_mob(self):
        name = self.name_entry.get()
        avatar_filename = self.avatar_var.get()
        avatar_path = os.path.join(self.avatar_dir, avatar_filename) if avatar_filename else None

        if not name:
            messagebox.showerror("Ошибка", "Имя моба не может быть пустым.")
            return

        conn = connect_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("INSERT INTO mobs (name, avatar_path) VALUES (%s, %s)", (name, avatar_path))
                conn.commit()
                messagebox.showinfo("Успех", f"Моб '{name}' успешно добавлен.")
                self.refresh_callback()
                self.destroy()
            except psycopg2.Error as e:
                messagebox.showerror("Ошибка базы данных", f"Ошибка при добавлении моба: {e}")
            finally:
                conn.close()

class EditMobDialog(tk.Toplevel):
    def __init__(self, parent, refresh_callback, mob_id=None, initial_name="", initial_avatar_path=None):
        super().__init__(parent)
        self.title("Редактировать моба")
        self.parent = parent
        self.refresh_callback = refresh_callback
        self.selected_mob_id_for_edit = mob_id
        self.initial_name = initial_name
        self.initial_avatar_path = initial_avatar_path
        self.avatar_dir = "avatars"
        self.avatar_files = [""] + [f for f in os.listdir(self.avatar_dir) if os.path.isfile(os.path.join(self.avatar_dir, f))]
        self.avatar_var = tk.StringVar(self)
        self.current_image = None
        self.selected_avatar_path = initial_avatar_path
        if initial_avatar_path:
            initial_avatar_filename = os.path.basename(initial_avatar_path)
            if initial_avatar_filename in self.avatar_files:
                self.avatar_var.set(initial_avatar_filename)
            else:
                self.avatar_var.set("")
        else:
            self.avatar_var.set("")

        self.init_ui()

    def init_ui(self):
        # --- Имя моба ---
        name_label = ttk.Label(self, text="Новое имя моба:")
        name_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.edit_mob_name_entry = ttk.Entry(self)
        self.edit_mob_name_entry.insert(0, self.initial_name)
        self.edit_mob_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # --- Выбор аватарки ---
        avatar_label = ttk.Label(self, text="Аватарка:")
        avatar_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.avatar_combobox = ttk.Combobox(self, textvariable=self.avatar_var, values=self.avatar_files, state="readonly")
        self.avatar_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.avatar_combobox.bind("<<ComboboxSelected>>", self.update_avatar_preview)

        # --- Предпросмотр аватарки ---
        self.avatar_preview_label = ttk.Label(self)
        self.avatar_preview_label.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        self.load_initial_avatar()

        # --- Кнопки ---
        save_button = ttk.Button(self, text="Сохранить изменения", command=self.save_edited_mob)
        save_button.grid(row=3, column=0, columnspan=2, pady=10)

        self.grid_columnconfigure(1, weight=1)

    def load_initial_avatar(self):
        if self.initial_avatar_path and os.path.exists(self.initial_avatar_path):
            try:
                img = Image.open(self.initial_avatar_path)
                img.thumbnail((100, 100))
                self.current_image = ImageTk.PhotoImage(img)
                self.avatar_preview_label.config(image=self.current_image)
            except Exception as e:
                print(f"Ошибка при загрузке начального изображения: {e}")
                self.avatar_preview_label.config(image=None, text="Ошибка загрузки")
        else:
            self.avatar_preview_label.config(image=None, text="Нет аватара")

    def update_avatar_preview(self, event):
        selected_file = self.avatar_var.get()
        if selected_file:
            self.selected_avatar_path = os.path.join(self.avatar_dir, selected_file)
            try:
                img = Image.open(self.selected_avatar_path)
                img.thumbnail((100, 100))
                self.current_image = ImageTk.PhotoImage(img)
                self.avatar_preview_label.config(image=self.current_image)
            except Exception as e:
                print(f"Ошибка при загрузке изображения для предпросмотра: {e}")
                self.avatar_preview_label.config(image=None, text="Ошибка загрузки")
        else:
            self.selected_avatar_path = None
            self.avatar_preview_label.config(image=None, text="Нет аватара")

    def save_edited_mob(self):
        new_mob_name = self.edit_mob_name_entry.get()

        if not new_mob_name:
            messagebox.showerror("Ошибка", "Имя моба не может быть пустым.")
            return

        if self.selected_mob_id_for_edit is None:
            messagebox.showerror("Ошибка", "Не выбран моб для редактирования.")
            return

        if self.selected_avatar_path is None and self.initial_avatar_path is not None and self.avatar_var.get() == "":
            if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить аватарку у этого моба?"):
                return

        conn = connect_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("UPDATE mobs SET name = %s, avatar_path = %s WHERE id = %s",
                            (new_mob_name, self.selected_avatar_path, self.selected_mob_id_for_edit))
                conn.commit()
                messagebox.showinfo("Успех", f"Моб успешно отредактирован.")
                self.refresh_callback()
                self.destroy()
            except psycopg2.Error as e:
                messagebox.showerror("Ошибка базы данных", f"Ошибка при редактировании моба: {e}")
            finally:
                conn.close()

class DeleteMobDialog(tk.Toplevel):
    def __init__(self, parent, refresh_callback):
        super().__init__(parent)
        self.title("Удалить моба")
        self.parent = parent
        self.refresh_callback = refresh_callback
        self.mobs = fetch_mobs(connect_db())
        self.selected_mob_id_for_delete = None

        ttk.Label(self, text="Выберите моба для удаления:").pack(padx=10, pady=5)

        self.delete_mob_var = tk.StringVar(self)
        self.delete_mob_var.set("Выберите моба")

        mob_names = [mob[1] for mob in self.mobs]
        self.delete_mob_dropdown = ttk.Combobox(self, textvariable=self.delete_mob_var, values=mob_names, state="readonly")
        self.delete_mob_dropdown.pack(padx=10, pady=5)

        delete_button = ttk.Button(self, text="Удалить моба", command=self.delete_selected_mob)
        delete_button.pack(pady=10)

    def delete_selected_mob(self):
        selected_mob_name = self.delete_mob_var.get()
        for mob in self.mobs:
            if mob[1] == selected_mob_name:
                self.selected_mob_id_for_delete = mob[0]
                break

        if self.selected_mob_id_for_delete is None:
            messagebox.showerror("Ошибка", "Не выбран моб для удаления.")
            return

        if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить моба '{selected_mob_name}'?"):
            conn = connect_db()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM mob_loot WHERE mob_id = %s", (self.selected_mob_id_for_delete,))
                    cur.execute("DELETE FROM mobs WHERE id = %s", (self.selected_mob_id_for_delete,))
                    conn.commit()
                    messagebox.showinfo("Успех", f"Моб '{selected_mob_name}' успешно удален.")
                    self.refresh_callback()
                    self.destroy()
                except psycopg2.Error as e:
                    messagebox.showerror("Ошибка базы данных", f"Ошибка при удалении моба: {e}")
                finally:
                    conn.close()

class AddLootDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Добавить лут")

        ttk.Label(self, text="Название лута:").pack(padx=10, pady=5)
        self.new_loot_name_entry = ttk.Entry(self)
        self.new_loot_name_entry.pack(padx=10, pady=5)

        add_button = ttk.Button(self, text="Сохранить", command=self.add_new_loot)
        add_button.pack(pady=10)

    def add_new_loot(self):
        new_loot_name = self.new_loot_name_entry.get()
        if not new_loot_name:
            messagebox.showerror("Ошибка", "Название лута не может быть пустым.")
            return

        conn = connect_db()
        if conn:
            query = "INSERT INTO loot (name) VALUES (%s)"
            params = (new_loot_name,)
            if execute_query(conn, query, params):
                messagebox.showinfo("Успех", f"Лут '{new_loot_name}' успешно добавлен.")
                self.destroy()
            conn.close()

class EditLootDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Редактировать лут")
        self.all_loot_items = {item[1]: item[0] for item in fetch_all_loot(connect_db())}
        self.selected_loot_id_for_edit = None

        ttk.Label(self, text="Выберите лут для редактирования:").pack(padx=10, pady=5)

        self.edit_loot_var = tk.StringVar(self)
        self.edit_loot_var.set("Выберите лут")

        loot_names = list(self.all_loot_items.keys())
        self.edit_loot_dropdown = ttk.Combobox(self, textvariable=self.edit_loot_var, values=loot_names, state="readonly")
        self.edit_loot_dropdown.pack(padx=10, pady=5)
        self.edit_loot_dropdown.bind("<<ComboboxSelected>>", self.populate_edit_form)

        ttk.Label(self, text="Новое название лута:").pack(padx=10, pady=5)
        self.edit_loot_name_entry = ttk.Entry(self)
        self.edit_loot_name_entry.pack(padx=10, pady=5)

        save_button = ttk.Button(self, text="Сохранить изменения", command=self.save_edited_loot)
        save_button.pack(pady=10)

    def populate_edit_form(self, event):
        selected_loot_name = self.edit_loot_var.get()
        if selected_loot_name in self.all_loot_items:
            loot_id = self.all_loot_items[selected_loot_name]
            conn = connect_db()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT name FROM loot WHERE id = %s", (loot_id,))
                    result = cur.fetchone()
                    if result:
                        self.edit_loot_name_entry.delete(0, tk.END)
                        self.edit_loot_name_entry.insert(0, result[0])
                        self.selected_loot_id_for_edit = loot_id
                except psycopg2.Error as e:
                    messagebox.showerror("Ошибка базы данных", f"Ошибка при получении информации о луте: {e}")
                finally:
                    conn.close()
        else:
            self.selected_loot_id_for_edit = None

    def save_edited_loot(self):
        new_loot_name = self.edit_loot_name_entry.get()
        if not new_loot_name:
            messagebox.showerror("Ошибка", "Название лута не может быть пустым.")
            return

        if self.selected_loot_id_for_edit is None:
            messagebox.showerror("Ошибка", "Не выбран лут для редактирования.")
            return

        conn = connect_db()
        if conn:
            query = "UPDATE loot SET name = %s WHERE id = %s"
            params = (new_loot_name, self.selected_loot_id_for_edit)
            if execute_query(conn, query, params):
                messagebox.showinfo("Успех", f"Лут успешно отредактирован.")
                self.destroy()
            conn.close()

class DeleteLootDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Удалить лут")
        self.all_loot_items_delete = {item[1]: item[0] for item in fetch_all_loot(connect_db())}
        self.selected_loot_id_for_delete = None

        ttk.Label(self, text="Выберите лут для удаления:").pack(padx=10, pady=5)

        self.delete_loot_var = tk.StringVar(self)
        self.delete_loot_var.set("Выберите лут")

        loot_names = list(self.all_loot_items_delete.keys())
        self.delete_loot_dropdown = ttk.Combobox(self, textvariable=self.delete_loot_var, values=loot_names, state="readonly")
        self.delete_loot_dropdown.pack(padx=10, pady=5)

        delete_button = ttk.Button(self, text="Удалить лут", command=self.delete_selected_loot)
        delete_button.pack(pady=10)

    def delete_selected_loot(self):
        selected_loot_name = self.delete_loot_var.get()
        if selected_loot_name in self.all_loot_items_delete:
            self.selected_loot_id_for_delete = self.all_loot_items_delete[selected_loot_name]
        else:
            self.selected_loot_id_for_delete = None
            messagebox.showerror("Ошибка", "Не выбран лут для удаления.")
            return

        conn = connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM mob_loot WHERE loot_id = %s", (self.selected_loot_id_for_delete,))
                linked_mobs_count = cursor.fetchone()[0]
                if linked_mobs_count > 0:
                    messagebox.showerror("Ошибка", f"Лут '{selected_loot_name}' связан с {linked_mobs_count} мобами. Пожалуйста, сначала удалите связь с этими мобами в разделе 'Редактировать лут моба'.")
                    return

                cur = conn.cursor()
                cur.execute("DELETE FROM loot WHERE id = %s", (self.selected_loot_id_for_delete,))
                conn.commit()
                messagebox.showinfo("Успех", f"Лут '{selected_loot_name}' успешно удален.")
                self.destroy()
            except psycopg2.Error as e:
                messagebox.showerror("Ошибка базы данных", f"Ошибка при удалении лута: {e}")
            finally:
                conn.close()

class EditMobLootDialog(tk.Toplevel):
    def __init__(self, parent, mobs, refresh_overview_callback, refresh_mob_list_callback, initial_mob_id=None, initial_mob_name=""):
        super().__init__(parent)
        self.title("Редактировать лут моба")
        self.parent = parent
        self.mobs = mobs
        self.refresh_overview_callback = refresh_overview_callback
        self.refresh_mob_list_callback = refresh_mob_list_callback
        self.loot_widgets = {}
        self.selected_mob_id = initial_mob_id
        self.selected_mob_name = initial_mob_name

        ttk.Label(self, text=f"Редактирование лута для моба: {self.selected_mob_name}").pack(padx=10, pady=5)
        ttk.Label(self, text="Введите шанс выпадения в процентах (%):").pack(padx=10, pady=5)

        self.loot_frame = ttk.Frame(self)
        self.loot_frame.pack(padx=10, pady=5)

        ttk.Button(self, text="Сохранить", command=self.save_mob_loot_config).pack(pady=10)

        if self.selected_mob_id is not None:
            self.load_mob_loot_config()

    def load_mob_loot_config(self):
        if self.selected_mob_id is None:
            return

        for widget in self.loot_frame.winfo_children():
            widget.destroy()

        conn = connect_db()
        if conn:
            try:
                all_loot = fetch_all_loot(conn)
                current_mob_loot = fetch_mob_loot_config(conn, self.selected_mob_id)

                for loot_item in all_loot:
                    loot_id = loot_item[0]
                    loot_name = loot_item[1]

                    loot_label = ttk.Label(self.loot_frame, text=f"{loot_name}:")
                    loot_label.grid(row=all_loot.index(loot_item), column=0, padx=5, pady=2, sticky="w")

                    drop_chance_var = tk.StringVar(self.loot_frame, value=current_mob_loot.get(loot_id, 0.0) * 100)
                    drop_chance_entry = ttk.Entry(self.loot_frame, width=5, textvariable=drop_chance_var)
                    drop_chance_entry.grid(row=all_loot.index(loot_item), column=1, padx=5, pady=2)

                    percent_label = ttk.Label(self.loot_frame, text="%")
                    percent_label.grid(row=all_loot.index(loot_item), column=2, padx=5, pady=2, sticky="w")

                    self.loot_widgets[loot_id] = drop_chance_var

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при загрузке конфигурации лута: {e}")
            finally:
                conn.close()

    def save_mob_loot_config(self):
        if self.selected_mob_id is None:
            messagebox.showerror("Ошибка", "Не выбран моб для сохранения конфигурации лута.")
            return

        conn = connect_db()
        if conn:
            try:
                execute_query(conn, "DELETE FROM mob_loot WHERE mob_id = %s", (self.selected_mob_id,))

                for loot_id, drop_chance_var in self.loot_widgets.items():
                    try:
                        drop_chance = float(drop_chance_var.get()) / 100.0
                        if 0.0 <= drop_chance <= 1.0:
                            execute_query(conn, "INSERT INTO mob_loot (mob_id, loot_id, drop_chance) VALUES (%s, %s, %s)",
                                          (self.selected_mob_id, loot_id, drop_chance))
                        elif drop_chance != 0.0:
                            messagebox.showwarning("Предупреждение", f"Шанс выпадения для лута с ID {loot_id} должен быть от 0 до 100. Значение {drop_chance_var.get()}% будет проигнорировано.")
                    except ValueError:
                        messagebox.showerror("Ошибка ввода", f"Некорректный формат шанса выпадения для лута с ID {loot_id}. Используйте числовое значение в процентах.")

                messagebox.showinfo("Успех", f"Конфигурация лута для '{self.selected_mob_name}' успешно сохранена.")
                self.refresh_overview_callback()
                self.refresh_mob_list_callback()
                self.destroy()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при сохранении конфигурации лута: {e}")
            finally:
                conn.close()


class CalculateKillsDialog(tk.Toplevel):
    def __init__(self, parent, mobs):
        super().__init__(parent)
        self.title("Рассчитать необходимое количество убийств")
        self.parent = parent
        self.mobs = mobs

        self.selected_mob_id = tk.StringVar(self)
        self.selected_mob_name = tk.StringVar(self)
        self.selected_loot_name = tk.StringVar(self)
        self.expected_kills = tk.StringVar(self, value="0")

        self.init_ui()

    def init_ui(self):
        ttk.Label(self, text="Выберите моба:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        mob_names = [mob[1] for mob in self.mobs]
        self.mob_combo = ttk.Combobox(self, textvariable=self.selected_mob_name, values=mob_names, state="readonly")
        self.mob_combo.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.mob_combo.bind("<<ComboboxSelected>>", self.populate_loot_options)

        ttk.Label(self, text="Выберите предмет лута (необязательно):").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.loot_combo = ttk.Combobox(self, textvariable=self.selected_loot_name, values=[], state="readonly")
        self.loot_combo.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        calculate_button = ttk.Button(self, text="Рассчитать", command=self.calculate_expected_kills)
        calculate_button.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Label(self, text="Ожидаемое количество убийств:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        ttk.Label(self, textvariable=self.expected_kills).grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        self.grid_columnconfigure(1, weight=1)

    def populate_loot_options(self, event):
        selected_mob = next((mob for mob in self.mobs if mob[1] == self.selected_mob_name.get()), None)
        if selected_mob:
            conn = connect_db()
            if conn:
                try:
                    loot_data = get_loot_for_mob(conn, selected_mob[0])
                    loot_names = [item[0] for item in loot_data]
                    self.loot_combo.config(values=loot_names)
                    self.selected_loot_name.set("")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Ошибка при получении списка лута: {e}")
                finally:
                    conn.close()

    def calculate_expected_kills(self):
        selected_mob = next((mob for mob in self.mobs if mob[1] == self.selected_mob_name.get()), None)
        selected_loot = self.selected_loot_name.get()

        if not selected_mob:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите моба.")
            return

        if selected_loot:
            conn = connect_db()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT ml.drop_chance
                        FROM mob_loot ml
                        JOIN mobs m ON ml.mob_id = m.id
                        JOIN loot l ON ml.loot_id = l.id
                        WHERE m.id = %s AND l.name = %s;
                    """, (selected_mob[0], selected_loot))
                    result = cursor.fetchone()
                    if result and result[0] > 0:
                        drop_chance = result[0]
                        expected_kills = 1 / drop_chance
                        self.expected_kills.set(f"{expected_kills:.2f}")
                    else:
                        self.expected_kills.set("Предмет не найден у этого моба или шанс равен 0.")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Ошибка при получении шанса выпадения: {e}")
                finally:
                    conn.close()
        else:
            messagebox.showinfo("Информация", "Пожалуйста, выберите конкретный предмет лута для расчета.")
            self.expected_kills.set("Выберите предмет лута.")
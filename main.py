import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from ttkthemes import ThemedTk
import random
from database import connect_db, fetch_mobs, get_loot_for_mob
from dialogs import AddMobDialog, CalculateKillsDialog, EditMobDialog, DeleteMobDialog, AddLootDialog, EditLootDialog, DeleteLootDialog, EditMobLootDialog
from PIL import Image, ImageTk
import os

class LootGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор Лута")

        self.root.geometry("2000x1000")
        self.root.minsize(800, 600)

        self.root.set_theme('equilux')

        self.conn = connect_db()
        if not self.conn:
            return

        self.mobs = fetch_mobs(self.conn)
        self.mob_images = []
        self.selected_mob_index = None
        self.avatar_image_tk = None
        self.placeholder_avatar_tk = None  # Инициализируем placeholder_avatar_tk

                # --- Секция выбора моба ---
        mob_frame = ttk.LabelFrame(root, text="Выбор моба", padding=10)
        mob_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        mob_frame.grid_rowconfigure(1, weight=1)
        mob_frame.grid_columnconfigure(0, weight=0) # Ширина колонки со списком будет определяться виджетом
        mob_frame.grid_columnconfigure(1, weight=1) # Колонка с аватаркой будет занимать оставшееся пространство

        self.mob_label = ttk.Label(mob_frame, text="Выберите моба:")
        self.mob_label.grid(row=0, column=0, columnspan=2, pady=(0, 5), sticky="w")

        self.mob_listbox = tk.Listbox(mob_frame, height=10, width=20) # Установите желаемую статичную ширину (например, 20 символов)
        self.mob_listbox.grid(row=1, column=0, padx=(0, 5), pady=5, sticky="nsew")
        self.mob_listbox.bind('<<ListboxSelect>>', self.select_mob_from_listbox)

        self.mob_avatar_display_label = ttk.Label(mob_frame, anchor="center", borderwidth=1, relief="solid")
        if self.placeholder_avatar_tk:
            self.mob_avatar_display_label.config(image=self.placeholder_avatar_tk)
            self.mob_avatar_display_label.image = self.placeholder_avatar_tk
        else:
            self.mob_avatar_display_label.config(text="Аватар")
        self.mob_avatar_display_label.grid(row=1, column=1, padx=(5, 0), pady=5, sticky="nsew")

        buttons_subframe = ttk.Frame(mob_frame)
        buttons_subframe.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky="ew")

        # --- Секция отображения аватарки моба ---
        self.avatar_frame = ttk.LabelFrame(root, text="Аватар", padding=10)
        self.avatar_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ns") # Растягиваем по вертикали

        self.avatar_label = ttk.Label(self.avatar_frame, text="Нет аватара")
        self.avatar_label.pack(padx=10, pady=10, fill="both", expand=True)

        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=0)

        # --- Секция управления мобами ---
        mobs_control_frame = ttk.LabelFrame(root, text="Управление мобами", padding=10)
        mobs_control_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        add_mob_button = ttk.Button(mobs_control_frame, text="Добавить", command=self.open_add_mob_dialog)
        add_mob_button.pack(side=tk.LEFT, padx=5, pady=5, fill="x", expand=True)
        edit_mob_button = ttk.Button(mobs_control_frame, text="Редактировать", command=self.edit_selected_mob)
        edit_mob_button.pack(side=tk.LEFT, padx=5, pady=5, fill="x", expand=True)
        delete_mob_button = ttk.Button(mobs_control_frame, text="Удалить", command=self.delete_selected_mob)
        delete_mob_button.pack(side=tk.LEFT, padx=5, pady=5, fill="x", expand=True)


        # --- Секция выпавшего лута ---
        loot_result_frame = ttk.LabelFrame(root, text="Выпавший лут", padding=10)
        loot_result_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.loot_label = ttk.Label(loot_result_frame, text="Здесь отобразится выпавший лут:")
        self.loot_label.pack(pady=5)

        self.loot_text = tk.Text(loot_result_frame, height=10, width=50)
        self.loot_text.pack(padx=10, pady=5, fill="both", expand=True)
        self.loot_text.config(state=tk.DISABLED)

        # --- Секция инвентаря ---
        self.inventory_frame = ttk.LabelFrame(root, text="Инвентарь", padding=10)
        self.inventory_frame.grid(row=0, column=2, rowspan=2, padx=10, pady=10, sticky="nsew")

        self.inventory_label = ttk.Label(self.inventory_frame, text="Содержимое инвентаря:")
        self.inventory_label.pack(pady=5)

        self.inventory_tree = ttk.Treeview(self.inventory_frame, columns=("item", "quantity"), show="headings")
        self.inventory_tree.heading("item", text="Предмет")
        self.inventory_tree.heading("quantity", text="Количество")
        self.inventory_tree.column("item", width=150)
        self.inventory_tree.column("quantity", width=100)
        self.inventory_tree.pack(padx=10, pady=5, fill="both", expand=True)

        self.inventory = {}

        self.clear_inventory_button = ttk.Button(self.inventory_frame, text="Очистить инвентарь", command=self.clear_inventory)
        self.clear_inventory_button.pack(pady=5)

        root.grid_columnconfigure(2, weight=1)

        # --- Секция управления лутом ---
        loot_control_frame = ttk.LabelFrame(root, text="Управление лутом", padding=10)
        loot_control_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        add_loot_button = ttk.Button(loot_control_frame, text="Добавить лут", command=self.open_add_loot_dialog)
        add_loot_button.pack(side=tk.LEFT, padx=5, pady=5, fill="x", expand=True)
        edit_loot_button = ttk.Button(loot_control_frame, text="Редактировать лут", command=self.open_edit_loot_dialog)
        edit_loot_button.pack(side=tk.LEFT, padx=5, pady=5, fill="x", expand=True)
        delete_loot_button = ttk.Button(loot_control_frame, text="Удалить лут", command=self.open_delete_loot_dialog)
        delete_loot_button.pack(side=tk.LEFT, padx=5, pady=5, fill="x", expand=True)
        edit_mob_loot_button = ttk.Button(loot_control_frame, text="Редактировать лут моба", command=self.edit_selected_mob_loot)
        edit_mob_loot_button.pack(side=tk.LEFT, padx=5, pady=5, fill="x", expand=True)

        # --- Секция обзора лута мобов ---
        overview_frame = ttk.LabelFrame(root, text="Обзор лута мобов", padding=10)
        overview_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.loot_overview_label = ttk.Label(overview_frame, text="Конфигурация выпадения лута для каждого моба:")
        self.loot_overview_label.pack(pady=5)

        self.loot_overview_tree = ttk.Treeview(overview_frame, columns=("mob", "loot", "drop_chance"), show="headings")
        self.loot_overview_tree.heading("mob", text="Моб")
        self.loot_overview_tree.heading("loot", text="Лут")
        self.loot_overview_tree.heading("drop_chance", text="Шанс выпадения (%)")
        self.loot_overview_tree.column("mob", width=200)
        self.loot_overview_tree.column("loot", width=200)
        self.loot_overview_tree.column("drop_chance", width=150)
        self.loot_overview_tree.pack(padx=10, pady=5, fill="both", expand=True)

        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=1)
        root.grid_rowconfigure(2, weight=1)

        self.populate_loot_overview()
        self.refresh_mob_list()

    def generate_loot(self):
        if self.selected_mob_index is None:
            messagebox.showinfo("Внимание", "Пожалуйста, выберите моба из списка.")
            return

        selected_mob_index = self.selected_mob_index
        mob_id = self.mobs[selected_mob_index][0]
        mob_name = self.mobs[selected_mob_index][1]

        loot_data = get_loot_for_mob(self.conn, mob_id)
        dropped_items = []
        for item_name, drop_chance in loot_data:
            if random.random() < drop_chance:
                dropped_items.append(item_name)

        self.loot_text.config(state=tk.NORMAL)
        self.loot_text.delete("1.0", tk.END)

        if dropped_items:
            self.loot_text.insert(tk.END, f"Выпало из '{mob_name}':\n")
            for item in dropped_items:
                self.loot_text.insert(tk.END, f"- {item}\n")
                if item in self.inventory:
                    self.inventory[item] += 1
                else:
                    self.inventory[item] = 1
        else:
            self.loot_text.insert(tk.END, f"Из '{mob_name}' ничего не выпало.\n")

        self.loot_text.config(state=tk.DISABLED)
        self.update_inventory_display()

    def hit_random_mob(self):
        if not self.mobs:
            messagebox.showinfo("Внимание", "Список мобов пуст.")
            return

        random_index = random.randint(0, len(self.mobs) - 1)
        self.mob_list_select(random_index)
        self.generate_loot()

    def open_add_mob_dialog(self):
        dialog = AddMobDialog(self.root, self.refresh_mob_list)
        dialog.grab_set()
        self.root.wait_window(dialog)

    def edit_selected_mob(self):
        if self.selected_mob_index is None:
            messagebox.showinfo("Внимание", "Пожалуйста, выберите моба для редактирования.")
            return

        selected_mob_index = self.selected_mob_index
        mob_id = self.mobs[selected_mob_index][0]
        mob_name = self.mobs[selected_mob_index][1]
        avatar_path = self.mobs[selected_mob_index][2] if len(self.mobs[selected_mob_index]) > 2 else None

        dialog = EditMobDialog(self.root, self.refresh_mob_list, mob_id=mob_id, initial_name=mob_name, initial_avatar_path=avatar_path)
        dialog.grab_set()
        self.root.wait_window(dialog)

    def delete_selected_mob(self):
        if self.selected_mob_index is None:
            messagebox.showinfo("Внимание", "Пожалуйста, выберите моба для удаления.")
            return

        selected_mob_index = self.selected_mob_index
        mob_id = self.mobs[selected_mob_index][0]
        mob_name = self.mobs[selected_mob_index][1]

        if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить моба '{mob_name}'?"):
            conn = connect_db()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM mob_loot WHERE mob_id = %s", (mob_id,))
                    cur.execute("DELETE FROM mobs WHERE id = %s", (mob_id,))
                    conn.commit()
                    messagebox.showinfo("Успех", f"Моб '{mob_name}' успешно удален.")
                    self.refresh_mob_list()
                    self.populate_loot_overview()
                    self.selected_mob_index = None
                except psycopg2.Error as e:
                    messagebox.showerror("Ошибка базы данных", f"Ошибка при удалении моба: {e}")
                finally:
                    conn.close()

    def open_add_loot_dialog(self):
        dialog = AddLootDialog(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)

    def _on_mousewheel(self, event):

        if event.delta > 0:
            self.mob_canvas.yview_scroll(-1, "units")
        else:
            self.mob_canvas.yview_scroll(1, "units")

    def edit_selected_mob_loot(self):
        if self.selected_mob_index is None:
            messagebox.showinfo("Внимание", "Пожалуйста, выберите моба для редактирования его лута.")
            return

        selected_mob_index = self.selected_mob_index
        mob_id = self.mobs[selected_mob_index][0]
        mob_name = self.mobs[selected_mob_index][1]

        dialog = EditMobLootDialog(self.root, self.mobs, self.populate_loot_overview, self.refresh_mob_list, initial_mob_id=mob_id, initial_mob_name=mob_name)
        dialog.grab_set()
        self.root.wait_window(dialog)

    def open_edit_loot_dialog(self):
        dialog = EditLootDialog(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)

    def open_delete_loot_dialog(self):
        dialog = DeleteLootDialog(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)

    def refresh_mob_list(self):
        self.mobs = fetch_mobs(self.conn)
        self.mob_listbox.delete(0, tk.END)
        for i, mob in enumerate(self.mobs):
            mob_name = mob[1]
            self.mob_listbox.insert(tk.END, mob_name)
        self.mob_images = []
        self.selected_mob_index = None
    def select_mob_from_listbox(self, event):
        selected_indices = self.mob_listbox.curselection()
        if selected_indices:
            self.selected_mob_index = selected_indices[0]
            mob_id = self.mobs[self.selected_mob_index][0]

            selected_mob = next((mob for mob in self.mobs if mob[0] == mob_id), None)
            if selected_mob and len(selected_mob) > 2 and selected_mob[2]:
                avatar_path = selected_mob[2]
                print(f"Путь к аватарке выбранного моба: {avatar_path}") # Добавили для отладки
                try:
                    img = Image.open(avatar_path)
                    img.thumbnail((100, 100)) # Создаем миниатюру размером не более 100x100
                    self.avatar_image_tk = ImageTk.PhotoImage(img)

                    self.mob_avatar_display_label.config(image=self.avatar_image_tk, text="") # Отображаем изображение и убираем текст
                except FileNotFoundError:
                    self.mob_avatar_display_label.config(image=None, text="Файл не найден")
                except Exception as e:
                    print(f"Ошибка при загрузке аватара: {e}")
                    self.mob_avatar_display_label.config(image=None, text="Ошибка загрузки")
            else:
                self.mob_avatar_display_label.config(image=None, text="Нет аватара")
    def update_inventory_display(self):
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        for item, quantity in self.inventory.items():
            self.inventory_tree.insert("", tk.END, values=(item, quantity))

    def open_calculate_kills_dialog(self):
        dialog = CalculateKillsDialog(self.root, self.mobs)
        dialog.grab_set()
        self.root.wait_window(dialog)

    def clear_inventory(self):
        self.inventory.clear()
        self.update_inventory_display()

    def populate_loot_overview(self):
        for item in self.loot_overview_tree.get_children():
            self.loot_overview_tree.delete(item)

        conn = connect_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT m.name AS mob_name, l.name AS loot_name, ml.drop_chance
                    FROM mob_loot ml
                    JOIN mobs m ON ml.mob_id = m.id
                    JOIN loot l ON ml.loot_id = l.id
                    WHERE ml.drop_chance > 0
                """)
                loot_data = cur.fetchall()
                for mob_name, loot_name, drop_chance in loot_data:
                    self.loot_overview_tree.insert("", tk.END, values=(mob_name, loot_name, f"{drop_chance * 100:.2f}"))
            except psycopg2.Error as e:
                messagebox.showerror("Ошибка базы данных", f"Ошибка при получении обзора лута: {e}")
            finally:
                conn.close()


    def mob_list_select(self, index):
        self.selected_mob_index = index
        for i in range(len(self.mobs)):
            border_tag = f"mob_border_{i}"
            if i == index:
                self.mob_canvas.itemconfig(border_tag, outline="blue", width=2)
            else:
                self.mob_canvas.itemconfig(border_tag, outline="lightgray", width=1)

if __name__ == "__main__":
    root = ThemedTk()
    app = LootGeneratorApp(root)
    root.mainloop()
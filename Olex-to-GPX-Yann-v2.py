import tkinter as tk
from tkinter import filedialog, messagebox
import gzip
import os
import webbrowser
import xml.etree.ElementTree as ET
from datetime import datetime
import folium
#add "pkg_resources.extern"
# --- Fonctions de conversion et de génération du GPX ---

def convert_minutes_to_decimal(minutes):
    return float(minutes) / 60

def parse_olex_route_file(route_file_content):
    waypoints = []
    for line in route_file_content:
        parts = line.strip().split()
        if len(parts) != 4:
            continue
        lat_str, lon_str, timestamp, name = parts
        try:
            lat_sign = -1 if lat_str.startswith('-') else 1
            lon_sign = -1 if lon_str.startswith('-') else 1
            lat = convert_minutes_to_decimal(lat_str.lstrip('-')) * lat_sign
            lon = convert_minutes_to_decimal(lon_str.lstrip('-')) * lon_sign
            timestamp = int(timestamp)
            dt = datetime.utcfromtimestamp(timestamp)
            waypoints.append({
                "lat": lat,
                "lon": lon,
                "time": dt.isoformat() + "Z",
                "name": name
            })
        except ValueError as e:
            print(f"Erreur de conversion dans la ligne: {line}. Erreur: {e}")
            continue
    return waypoints

def create_gpx_file(waypoints, is_route):
    # Création de l'élément racine GPX
    gpx = ET.Element("gpx", version="1.1", creator="OlexConverter",
                     xmlns="http://www.topografix.com/GPX/1/1")
    if is_route:
        rte = ET.SubElement(gpx, "rte")
        for wp in waypoints:
            rtept = ET.SubElement(rte, "rtept", lat=str(wp["lat"]), lon=str(wp["lon"]))
            ET.SubElement(rtept, "time").text = wp["time"]
            ET.SubElement(rtept, "name").text = wp["name"]
    else:
        for wp in waypoints:
            wpt = ET.SubElement(gpx, "wpt", lat=str(wp["lat"]), lon=str(wp["lon"]))
            ET.SubElement(wpt, "time").text = wp["time"]
            ET.SubElement(wpt, "name").text = wp["name"]
    return ET.ElementTree(gpx)

def generate_map(waypoints, map_file):
    if not waypoints:
        return
    m = folium.Map(location=[waypoints[0]['lat'], waypoints[0]['lon']], zoom_start=10)
    for wp in waypoints:
        folium.Marker([wp['lat'], wp['lon']], popup=wp['name']).add_to(m)
    m.save(map_file)

def open_map(map_file):
    webbrowser.open(map_file)

# --- Fonction principale de sélection et conversion ---

def select_and_convert():
    # Sélection du fichier .gz
    file_path = filedialog.askopenfilename(title="Sélectionner le fichier Olex (.gz)",
                                           filetypes=[("Olex GZ files", "*.gz")])
    if not file_path:
        return

    try:
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            content = f.readlines()
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de la lecture du fichier : {e}")
        return

    waypoints = parse_olex_route_file(content)
    if not waypoints:
        messagebox.showerror("Erreur", "Aucun waypoint valide trouvé.")
        return

    # Choix de l'emplacement d'enregistrement du fichier GPX
    save_path = filedialog.asksaveasfilename(defaultextension=".gpx",
                                             filetypes=[("GPX Files", "*.gpx")],
                                             title="Enregistrer le fichier GPX")
    if not save_path:
        return

    # Création du GPX en fonction du choix (route ou liste de waypoints)
    gpx_tree = create_gpx_file(waypoints, is_route=(route_var.get() == "route"))
    try:
        ET.indent(gpx_tree, space="    ")
    except Exception:
        pass  # Pour les versions de Python ne supportant pas indent()
    gpx_tree.write(save_path, encoding="utf-8", xml_declaration=True)

    # Génération de la carte (map.html dans le même dossier que le GPX)
    map_file = os.path.join(os.path.dirname(save_path), "map.html")
    generate_map(waypoints, map_file)

    text_output.delete('1.0', tk.END)
    text_output.insert(tk.END, f"{len(waypoints)} waypoints extraits.\n"
                               f"Fichier GPX enregistré en : {save_path}\n"
                               f"Carte générée en : {map_file}")
    open_map(map_file)

# --- Interface Graphique (belle interface) ---

root = tk.Tk()
root.title("Olex to GPX Converter")
root.geometry("800x493")
try:
    root.iconbitmap("o.ico")
except Exception as e:
    print("Erreur lors du chargement de l'icône :", e)

# Création d'un Canvas pour l'arrière-plan
canvas = tk.Canvas(root, width=800, height=493)
canvas.pack(fill="both", expand=True)

try:
    background_image = tk.PhotoImage(file="image.png")
    canvas.create_image(0, 0, image=background_image, anchor="nw")
except Exception as e:
    print("Erreur lors du chargement de l'image de fond :", e)

# Cadre central avec fond clair
frame = tk.Frame(root, bg="#f0f0f0")
frame.place(relx=0.5, rely=0.5, anchor="center")

lbl_title = tk.Label(frame, text="Sélectionnez un fichier Olex (.gz)", font=("Arial", 14))
lbl_title.pack(pady=10)

btn_select = tk.Button(frame, text="Sélectionner un fichier .gz",
                       command=select_and_convert, bg="#4CAF50", fg="white",
                       font=("Arial", 12), relief="flat", width=25)
btn_select.pack(pady=10)

# Switch pour choisir entre "Liste de waypoints" et "Route"
route_var = tk.StringVar(value="waypoints")
radio_wpt = tk.Radiobutton(frame, text="Liste de waypoints", variable=route_var,
                           value="waypoints", bg="#f0f0f0", font=("Arial", 12))
radio_rte = tk.Radiobutton(frame, text="Route", variable=route_var,
                           value="route", bg="#f0f0f0", font=("Arial", 12))
radio_wpt.pack()
radio_rte.pack()

# Zone de texte pour afficher les messages
text_output = tk.Text(frame, height=8, width=70, wrap="word", font=("Arial", 10))
text_output.pack(pady=10)

scroll = tk.Scrollbar(frame, command=text_output.yview)
text_output.config(yscrollcommand=scroll.set)
scroll.pack(side="right", fill="y")

root.mainloop()

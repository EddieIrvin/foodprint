import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import webbrowser
import time

# --- Configuration ---
DATA_FILE = "data.json"

# --- Helper: Generate Map Picker HTML (Updated with Search Function) ---
def create_map_picker_html():
    """Creates a temporary HTML file for picking coordinates using Leaflet + Amap Tiles, now with search."""
    
    # !!! 警告: 请将 '您自己的高德地图Key' 替换为您在高德开放平台申请的 Web 端 (JS API) Key !!!
    AMAP_KEY = "0c7874d496d9ba218153b11119ab1068" 
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>地图选点及搜索 - FoodPrint</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.3/dist/leaflet.css" />
    <style>
        body {{ margin: 0; padding: 0; display: flex; flex-direction: column; height: 100vh; }}
        #map-wrapper {{ position: relative; flex: 1; }}
        #info {{ padding: 10px; background: #ea945a; color: white; text-align: center; font-family: sans-serif; font-weight: bold; display: flex; align-items: center; justify-content: center; }}
        #map {{ width: 100%; height: 100%; }}
        .copy-btn {{ margin-left: 15px; padding: 5px 10px; cursor: pointer; background: white; border: none; border-radius: 4px; color: #ea945a; font-weight: bold; }}
        #coords {{ margin-right: 15px; }}
        
        /* 搜索框样式 */
        #search-container {{ position: absolute; z-index: 10000; top: 10px; left: 10px; }}
        #tipinput {{ width: 250px; padding: 10px; border: 2px solid #ddd; box-shadow: 0 2px 6px rgba(0,0,0,0.2); border-radius: 4px; font-size: 14px; outline: none; }}
        #tipinput:focus {{ border-color: #ea945a; box-shadow: 0 2px 8px rgba(234, 148, 90, 0.4); }}
        .leaflet-container {{ background: #f0f0f0; }}
        .amap-suggest-list {{ z-index: 10001 !important; }}
    </style>
    <script src="https://unpkg.com/leaflet@1.9.3/dist/leaflet.js"></script>
    <script type="text/javascript" src="https://webapi.amap.com/maps?v=1.4.15&key={AMAP_KEY}&plugin=AMap.PlaceSearch,AMap.AutoComplete"></script>
</head>
<body>
    <div id="info">
        <span id="coords">尚未选择</span>
        <button class="copy-btn" onclick="copyCoords()">复制并关闭</button>
    </div>
    <div id="map-wrapper">
        <div id="search-container">
            <input type="text" id="tipinput" placeholder="输入地址或地名搜索..." />
        </div>
        <div id="map"></div>
    </div>
    
    <script>
        const map = L.map('map').setView([39.9042, 116.4074], 11); // Default Beijing
        L.tileLayer('https://webst0{{s}}.is.autonavi.com/appmaptile?style=7&x={{x}}&y={{y}}&z={{z}}', {{
            subdomains: ['1', '2', '3', '4'],
            maxZoom: 18
        }}).addTo(map);

        let currentMarker = null;
        const coordsSpan = document.getElementById('coords');
        
        // --- Core Functions ---
        function setMarker(latlng, name = "所选位置") {{
            if (currentMarker) map.removeLayer(currentMarker);
            currentMarker = L.marker(latlng).addTo(map).bindPopup(name).openPopup();
            const lat = latlng.lat.toFixed(6);
            const lng = latlng.lng.toFixed(6);
            coordsSpan.innerText = `${{lat}}, ${{lng}}`;
            
            // Auto copy to clipboard logic
            navigator.clipboard.writeText(`${{lat}}, ${{lng}}`).catch(err => {{
                console.error("Clipboard error", err);
            }});
        }}

        map.on('click', function(e) {{
            setMarker(e.latlng, "地图点击位置");
        }});

        function copyCoords() {{
            const text = coordsSpan.innerText;
            if(text === "尚未选择") {{
                alert("请先点击地图选择一个位置或搜索！");
                return;
            }}
            // Fallback copy
            const textArea = document.createElement("textarea");
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand("Copy");
            textArea.remove();
            
            alert("坐标 " + text + " 已复制！请回到Python程序粘贴。");
            window.close(); // Attempt to close
        }}
        
        // --- Amap Search Integration ---
        console.log("Page loaded, waiting for Amap...");
        window.addEventListener('load', function() {{
            console.log("Window loaded, initializing search...");
            if (window.AMap) {{
                AMap.plugin(['AMap.PlaceSearch', 'AMap.AutoComplete'], function(){{
                    console.log("Amap plugins loaded successfully");
                    const tipInput = document.getElementById('tipinput');
                    
                    // Auto Complete
                    const auto = new AMap.AutoComplete({{
                        input: "tipinput" 
                    }});

                    // Place Search
                    const placeSearch = new AMap.PlaceSearch({{
                        map: null, // Don't bind to AMap map instance
                        pageSize: 5,
                        pageIndex: 1,
                    }});
                    
                    console.log("AutoComplete initialized");
                    
                    // Function to handle search
                    function performSearch(keyword) {{
                        if (!keyword || keyword.trim() === '') {{
                            console.log("Empty search keyword");
                            return;
                        }}
                        console.log("Performing search for:", keyword);
                        placeSearch.search(keyword, function(status, result) {{
                            console.log("PlaceSearch status:", status, "result:", result);
                            if (status === 'complete' && result && result.poiList && result.poiList.pois && result.poiList.pois.length > 0) {{
                                const poi = result.poiList.pois[0];
                                console.log("Found POI:", poi);
                                const latlng = L.latLng(poi.location.lat, poi.location.lng);
                                map.setView(latlng, 15);
                                setMarker(latlng, poi.name);
                            }} else {{
                                console.log("PlaceSearch returned no results");
                                alert("未找到该地点，请重试");
                            }}
                        }});
                    }}
                    
                    // Listen to Enter key
                    tipInput.addEventListener('keypress', function(e) {{
                        console.log("Key pressed:", e.key);
                        if (e.key === 'Enter') {{
                            e.preventDefault();
                            performSearch(this.value);
                        }}
                    }});
                    
                    // Listen to selection event from AutoComplete (clicking on suggestion)
                    AMap.Event.addListener(auto, "select", function(e){{
                        console.log("Search result selected from autocomplete:", e);
                        if (e.poi && e.poi.location) {{
                            console.log("Using POI location");
                            const latlng = L.latLng(e.poi.location.lat, e.poi.location.lng);
                            map.setView(latlng, 15);
                            setMarker(latlng, e.poi.name);
                        }} else if (e.item && e.item.location) {{
                            console.log("Using item location");
                            // Fallback for non-POI search result
                            const latlng = L.latLng(e.item.location.lat, e.item.location.lng);
                            map.setView(latlng, 15);
                            setMarker(latlng, e.item.name || e.item.value);
                        }} else if (e.item) {{
                            // If no location in autocomplete, use PlaceSearch to query the suggestion
                            const searchText = e.item.name || e.item.value;
                            console.log("Using PlaceSearch for:", searchText);
                            performSearch(searchText);
                        }}
                    }});
                }});
            }} else {{
                console.error("AMap is not loaded!");
            }}
        }});
    </script>
</body>
</html>
    """
    try:
        with open("map_picker_temp.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        return os.path.abspath("map_picker_temp.html")
    except Exception as e:
        messagebox.showerror("Error", f"无法创建地图选点文件: {e}")
        return None

# --- Main Application Class ---
class FoodManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FoodPrint 数据管理系统")
        self.root.geometry("800x600")
        
        # Data storage
        self.data = []
        
        # 1. 先初始化 GUI (创建 self.tree)
        self.setup_ui()
        
        # 2. 再加载数据 (内部会调用 refresh_list，此时 self.tree 已存在)
        self.load_data()

    def setup_ui(self):
        # 1. Top Toolbar
        toolbar = tk.Frame(self.root, pady=10)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=10)

        tk.Button(toolbar, text="刷新数据", command=self.load_data).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="添加店铺", bg="#ea945a", fg="white", command=self.add_item).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="修改选中", command=self.edit_item).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="删除选中", fg="red", command=self.delete_item).pack(side=tk.LEFT, padx=5)
        
        # 2. Treeview (List)
        columns = ("ID", "Name", "Cuisine", "Lat", "Lng", "Address")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")
        
        self.tree.heading("ID", text="ID")
        self.tree.column("ID", width=30)
        self.tree.heading("Name", text="名称")
        self.tree.column("Name", width=150)
        self.tree.heading("Cuisine", text="菜系")
        self.tree.column("Cuisine", width=80)
        self.tree.heading("Lat", text="纬度")
        self.tree.column("Lat", width=80)
        self.tree.heading("Lng", text="经度")
        self.tree.column("Lng", width=80)
        self.tree.heading("Address", text="地址")
        self.tree.column("Address", width=200)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.tree, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            # Create default if not exists
            default_data = [{"id": "1", "name": "示例", "latitude": 39.9, "longitude": 116.4, "cuisine": "测试", "reason": "", "address": ""}]
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=4)
            self.data = default_data
        else:
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"无法读取数据文件: {e}")
                self.data = []
        self.refresh_list()

    def save_data(self):
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"保存失败: {e}")

    def refresh_list(self):
        # Clear current list
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Add data
        for item in self.data:
            self.tree.insert("", tk.END, values=(
                item.get("id", ""),
                item.get("name", ""),
                item.get("cuisine", ""),
                item.get("latitude", ""),
                item.get("longitude", ""),
                item.get("address", "")
            ))

    def open_editor(self, item=None):
        """Opens a dialog to add or edit an item."""
        is_edit = item is not None
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑店铺" if is_edit else "添加店铺")
        dialog.geometry("400x500")

        # Variables
        v_name = tk.StringVar(value=item['name'] if is_edit else "")
        v_cuisine = tk.StringVar(value=item['cuisine'] if is_edit else "")
        v_lat = tk.DoubleVar(value=item['latitude'] if is_edit else 0.0)
        v_lng = tk.DoubleVar(value=item['longitude'] if is_edit else 0.0)
        v_reason = tk.StringVar(value=item.get('reason', "") if is_edit else "")
        v_address = tk.StringVar(value=item.get('address', "") if is_edit else "")

        # Layout
        tk.Label(dialog, text="店铺名称:").pack(pady=5)
        tk.Entry(dialog, textvariable=v_name).pack(fill=tk.X, padx=20)

        tk.Label(dialog, text="菜系:").pack(pady=5)
        tk.Entry(dialog, textvariable=v_cuisine).pack(fill=tk.X, padx=20)

        # Coordinate Picker Frame
        coord_frame = tk.LabelFrame(dialog, text="位置坐标 (必填)", padx=10, pady=10)
        coord_frame.pack(fill=tk.X, padx=20, pady=10)

        def pick_on_map():
            path = create_map_picker_html()
            if path:
                webbrowser.open('file://' + path)
                messagebox.showinfo("提示", "地图已在浏览器打开。\n\n1. 点击地图选点 或 使用搜索框定位\n2. 点击'复制并关闭'\n3. 回到此处将坐标粘贴填入纬度和经度框中。")

        tk.Button(coord_frame, text="🗺️ 在地图上选择/搜索 (浏览器)", command=pick_on_map, bg="#eee").pack(pady=5)

        tk.Label(coord_frame, text="纬度 (Latitude):").pack()
        tk.Entry(coord_frame, textvariable=v_lat).pack(fill=tk.X)
        
        tk.Label(coord_frame, text="经度 (Longitude):").pack()
        tk.Entry(coord_frame, textvariable=v_lng).pack(fill=tk.X)

        tk.Label(dialog, text="地址:").pack(pady=5)
        tk.Entry(dialog, textvariable=v_address).pack(fill=tk.X, padx=20)

        tk.Label(dialog, text="推荐理由:").pack(pady=5)
        tk.Entry(dialog, textvariable=v_reason).pack(fill=tk.X, padx=20)

        def save():
            try:
                new_item = {
                    "id": item['id'] if is_edit else str(int(time.time())), # Simple timestamp ID
                    "name": v_name.get(),
                    "latitude": float(v_lat.get()),
                    "longitude": float(v_lng.get()),
                    "cuisine": v_cuisine.get(),
                    "reason": v_reason.get(),
                    "address": v_address.get()
                }
                
                if is_edit:
                    # Update existing
                    for i, d in enumerate(self.data):
                        if d['id'] == item['id']:
                            self.data[i] = new_item
                            break
                else:
                    self.data.append(new_item)
                
                self.save_data()
                self.refresh_list()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "坐标必须是数字！")

        tk.Button(dialog, text="保存", bg="#ea945a", fg="white", command=save).pack(pady=20, fill=tk.X, padx=20)

    def add_item(self):
        self.open_editor(None)

    def edit_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一行")
            return
        item_id = self.tree.item(selected[0])['values'][0]
        # Find raw data
        item_data = next((x for x in self.data if str(x['id']) == str(item_id)), None)
        if item_data:
            self.open_editor(item_data)

    def delete_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一行")
            return
        if messagebox.askyesno("确认", "确定要删除该记录吗？"):
            item_id = self.tree.item(selected[0])['values'][0]
            self.data = [x for x in self.data if str(x['id']) != str(item_id)]
            self.save_data()
            self.refresh_list()

if __name__ == "__main__":
    root = tk.Tk()
    app = FoodManagerApp(root)
    root.mainloop()
#!/usr/bin/env python3
"""
BLR Airport Cab — Static Site Generator & Build Engine
Compiles Jekyll templates, markdown pages, layouts, includes, and YAML data
into clean, production-ready static HTML for MAMP local development and GitHub Pages hosting.
Zero external dependencies required.
"""

import os
import re
import json
import urllib.parse

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Simple YAML Parser for our structured data files
def parse_simple_yaml(text):
    """Parses basic key-value and list-of-dicts YAML."""
    lines = text.strip().splitlines()
    data = {}
    current_list = None
    current_dict = None
    current_key = None

    # Check if root is a list
    if any(line.strip().startswith("- ") for line in lines if line.strip()):
        root_is_list = True
        root_data = []
    else:
        root_is_list = False
        root_data = {}

    for line in lines:
        raw_line = line
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        # List item with dict: "- id: sedan"
        if stripped.startswith("- "):
            item_text = stripped[2:].strip()
            new_item = {}
            if root_is_list:
                root_data.append(new_item)
                current_dict = new_item
            elif current_list is not None:
                current_list.append(new_item)
                current_dict = new_item

            if ":" in item_text:
                k, v = item_text.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                new_item[k] = v
            else:
                # Simple list of strings
                if root_is_list:
                    root_data[-1] = item_text.strip('"').strip("'")
                elif current_list is not None:
                    current_list[-1] = item_text.strip('"').strip("'")
            continue

        # Sub-item inside a dict
        if ":" in stripped:
            k, v = stripped.split(":", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            
            if indent == 0:
                if not v:
                    current_list = []
                    root_data[k] = current_list
                    current_dict = None
                else:
                    root_data[k] = v
                    current_list = None
                    current_dict = None
            else:
                if current_dict is not None:
                    if not v:
                        current_dict[k] = []
                        current_key = k
                    else:
                        current_dict[k] = v
        elif stripped.startswith("- ") is False and current_dict is not None and current_key:
            pass

    return root_data

def load_data():
    """Loads all data files from _data directory."""
    data = {
        "services": [],
        "vehicles": [],
        "navigation": {},
        "business": {}
    }

    # Load Services
    services_file = os.path.join(ROOT_DIR, "_data", "services.yml")
    if os.path.exists(services_file):
        with open(services_file, "r", encoding="utf-8") as f:
            content = f.read()
            # Parse service blocks
            blocks = content.split("\n- id: ")
            for idx, block in enumerate(blocks):
                if not block.strip():
                    continue
                block_content = ("id: " + block) if idx > 0 else block
                s_dict = {}
                features = []
                for line in block_content.splitlines():
                    ls = line.strip()
                    if ls.startswith("features:"):
                        continue
                    if ls.startswith("- ") and "features" in line:
                        features.append(ls[2:].strip().strip('"'))
                    elif line.startswith("    - "):
                        features.append(ls[2:].strip().strip('"'))
                    elif ":" in ls:
                        k, v = ls.split(":", 1)
                        s_dict[k.strip()] = v.strip().strip('"').strip("'")
                s_dict["features"] = features
                data["services"].append(s_dict)

    # Load Vehicles
    vehicles_file = os.path.join(ROOT_DIR, "_data", "vehicles.yml")
    if os.path.exists(vehicles_file):
        with open(vehicles_file, "r", encoding="utf-8") as f:
            content = f.read()
            if content.startswith("- id: "):
                content = content[2:]
            blocks = content.split("\n- id: ")
            for idx, block in enumerate(blocks):
                if not block.strip():
                    continue
                block_content = ("id: " + block) if idx > 0 else block
                v_dict = {}
                ideal_for = []
                features = []
                mode = None
                for line in block_content.splitlines():
                    ls = line.strip()
                    if ls.startswith("ideal_for:"):
                        mode = "ideal"
                        continue
                    elif ls.startswith("features:"):
                        mode = "feat"
                        continue
                    elif ls.startswith("- ") and mode == "ideal":
                        ideal_for.append(ls[2:].strip().strip('"'))
                    elif ls.startswith("- ") and mode == "feat":
                        features.append(ls[2:].strip().strip('"'))
                    elif ":" in ls and not ls.startswith("- "):
                        mode = None
                        k, v = ls.split(":", 1)
                        v_dict[k.strip()] = v.strip().strip('"').strip("'")
                v_dict["ideal_for"] = ideal_for
                v_dict["features"] = features
                data["vehicles"].append(v_dict)

    return data

def parse_front_matter(content):
    """Extracts front matter and body from markdown/html file."""
    meta = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].strip()
            for line in fm_text.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, body

def render_includes(html, context, baseurl, site_data):
    """Replaces {% include filename ... %} tags."""
    include_pattern = re.compile(r"\{%\s*include\s+([\w\.\-]+)(.*?)\s*%\}")

    def include_replacer(match):
        filename = match.group(1).strip()
        args_str = match.group(2).strip()

        # Parse args
        args = {}
        for part in re.findall(r'(\w+)=(?:"([^"]*)"|\'([^\']*)\'|([\w\.\-]+))', args_str):
            key = part[0]
            val = part[1] or part[2] or part[3]
            args[key] = val

        include_path = os.path.join(ROOT_DIR, "_includes", filename)
        if not os.path.exists(include_path):
            return f"<!-- Include not found: {filename} -->"

        with open(include_path, "r", encoding="utf-8") as inc_f:
            inc_content = inc_f.read()

        # Specialized rendering for service-card and fleet-card
        if filename == "service-card.html" and "service" in args:
            svc_name = args["service"]
            # Look up service
            svc = next((s for s in site_data["services"] if s.get("id") == svc_name or svc_name.endswith(s.get("id", ""))), None)
            if not svc and site_data["services"]:
                svc = site_data["services"][0]
            if svc:
                return render_service_card(inc_content, svc, baseurl)

        if filename == "fleet-card.html" and "vehicle" in args:
            veh_name = args["vehicle"]
            if veh_name == "suv":
                veh_name = "innova-crysta"
            veh = next((v for v in site_data["vehicles"] if v.get("id") == veh_name or (v.get("id") and veh_name.endswith(v.get("id", "")))), None)
            if not veh and site_data["vehicles"]:
                veh = site_data["vehicles"][0]
            if veh:
                return render_fleet_card(inc_content, veh, baseurl)

        # General replacements in include
        rendered_inc = inc_content
        for k, v in args.items():
            rendered_inc = rendered_inc.replace(f"{{{{ include.{k} }}}}", str(v))
            rendered_inc = rendered_inc.replace(f"{{{{ include.{k} | default: page.booking_tab | default: 'airport-drop' }}}}", str(v))
            rendered_inc = rendered_inc.replace(f"{{{{ include.{k} | default: 'airport-drop' }}}}", str(v))

        # Check default_tab fallback
        page_booking_tab = context.get("booking_tab", "airport-drop")
        rendered_inc = rendered_inc.replace("{{ include.default_tab | default: page.booking_tab | default: 'airport-drop' }}", page_booking_tab)
        rendered_inc = rendered_inc.replace("{{ include.default_tab | default: page.booking_tab }}", page_booking_tab)
        rendered_inc = rendered_inc.replace("{{ include.default_tab }}", page_booking_tab)

        return rendered_inc

    # Multi-pass include replacement to handle nested includes
    for _ in range(3):
        if "{% include" not in html:
            break
        html = include_pattern.sub(include_replacer, html)

    return html

def render_service_card(template, svc, baseurl):
    """Renders a single service card."""
    card = template
    card = card.replace("{{ include.service.title }}", svc.get("title", ""))
    card = card.replace("{{ include.service.description }}", svc.get("description", ""))
    card = card.replace("{{ include.service.url }}", svc.get("url", ""))
    card = card.replace("{{ site.baseurl }}", baseurl)
    card = card.replace('{{ include.service.cta | default: "View Service Details" }}', svc.get("cta", "View Service Details"))

    # Features list
    features_html = ""
    for feat in svc.get("features", []):
        features_html += f'<li><svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg><span>{feat}</span></li>\n'
    
    # Replace feature loop
    card = re.sub(r'\{%\s*if include\.service\.features\s*%\}.*?\{%\s*endif\s*%\}', 
                  f'<ul class="service-feature-list">{features_html}</ul>', 
                  card, flags=re.DOTALL)

    # Replace icon condition
    icon = svc.get("icon", "car")
    icon_svg = '<svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.5 3c-.1.2-.1.4-.1.6v4.5c0 .6.4 1 1 1h2m14 0a2 2 0 11-4 0m4 0a2 2 0 10-4 0m-8 0a2 2 0 11-4 0m4 0a2 2 0 10-4 0"/></svg>'
    if icon == "plane-takeoff":
        icon_svg = '<svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg>'
    elif icon == "map-pin":
        icon_svg = '<svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>'
    elif icon == "clock":
        icon_svg = '<svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
    elif icon == "camera":
        icon_svg = '<svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><path d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/></svg>'
    elif icon == "road":
        icon_svg = '<svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"/></svg>'

    card = re.sub(r'\{%\s*if include\.service\.icon.*?\{%\s*endif\s*%\}', icon_svg, card, flags=re.DOTALL)
    return card

def render_fleet_card(template, veh, baseurl):
    """Renders a single vehicle fleet card."""
    card = template
    card = card.replace("{{ include.vehicle.id }}", veh.get("id", ""))
    card = card.replace("{{ include.vehicle.name }}", veh.get("name", ""))
    card = card.replace("{{ include.vehicle.models }}", veh.get("models", ""))
    card = card.replace("{{ include.vehicle.category }}", veh.get("category", ""))
    card = card.replace("{{ include.vehicle.capacity }}", veh.get("capacity", ""))
    card = card.replace("{{ include.vehicle.luggage }}", veh.get("luggage", ""))
    card = card.replace("{{ include.vehicle.ac }}", veh.get("ac", ""))
    card = card.replace("{{ include.vehicle.image }}", veh.get("image", ""))
    card = card.replace("{{ include.vehicle.description }}", veh.get("description", ""))
    card = card.replace("{{ include.vehicle.fare }}", veh.get("fare", ""))
    card = card.replace("{{ include.vehicle.price_note }}", veh.get("price_note", ""))
    card = card.replace("{{ site.baseurl }}", baseurl)
    
    encoded_name = urllib.parse.quote(veh.get("name", ""))
    card = card.replace("{{ include.vehicle.name | url_encode }}", encoded_name)
    encoded_fare = urllib.parse.quote(veh.get("fare", ""))
    card = card.replace("{{ include.vehicle.fare | url_encode }}", encoded_fare)
    return card

def process_site_loops(html, site_data, baseurl):
    """Replaces {% for x in site.data.services %} and {% for y in site.data.vehicles %} loops."""
    # Services Loop
    service_card_path = os.path.join(ROOT_DIR, "_includes", "service-card.html")
    with open(service_card_path, "r", encoding="utf-8") as f:
        svc_template = f.read()

    svc_pattern = re.compile(r'\{%\s*for\s+service\s+in\s+site\.data\.services\s*%\}(.*?)\{%\s*endfor\s*%\}', re.DOTALL)
    def svc_loop_replacer(match):
        res = []
        for svc in site_data["services"]:
            res.append(render_service_card(svc_template, svc, baseurl))
        return "\n".join(res)

    html = svc_pattern.sub(svc_loop_replacer, html)

    # Vehicles Loop
    fleet_card_path = os.path.join(ROOT_DIR, "_includes", "fleet-card.html")
    with open(fleet_card_path, "r", encoding="utf-8") as f:
        fleet_template = f.read()

    veh_pattern = re.compile(r'\{%\s*for\s+vehicle\s+in\s+site\.data\.vehicles\s*%\}(.*?)\{%\s*endfor\s*%\}', re.DOTALL)
    def veh_loop_replacer(match):
        res = []
        for veh in site_data["vehicles"]:
            res.append(render_fleet_card(fleet_template, veh, baseurl))
        return "\n".join(res)

    html = veh_pattern.sub(veh_loop_replacer, html)
    return html

def render_liquid_vars(html, meta, baseurl):
    """Replaces variables and conditional tags."""
    # Site variables
    html = html.replace("{{ site.baseurl }}", baseurl)
    html = html.replace("{{ site.url }}", "https://blrairportcab.com")

    # Clean double slashes
    if baseurl == ".":
        html = html.replace('href="./"', 'href="./"')
        html = re.sub(r'href="\./([a-zA-Z0-9_\-\./#]+)"', r'href="\1"', html)
        html = re.sub(r'src="\./([a-zA-Z0-9_\-\./#]+)"', r'src="\1"', html)
    elif baseurl == "..":
        pass

    # Meta variables
    for k, v in meta.items():
        html = html.replace(f"{{{{ page.{k} }}}}", str(v))
        html = html.replace(f"{{{{ page.{k} | escape }}}}", str(v))
        html = html.replace(f"{{{{ page.{k} | default: '' }}}}", str(v))

    # Fallbacks
    title = meta.get("title", "Bangalore Airport Taxi Service | 24/7 Pickup & Drop | BLR Airport Cab")
    desc = meta.get("description", "Book reliable Bangalore Airport Taxi service for Kempegowda International Airport (BLR). 24/7 airport pickup & drop, local cab packages & outstation trips.")
    h1 = meta.get("h1", title)
    lead = meta.get("lead", desc)
    badge = meta.get("hero_badge", meta.get("category", "24/7 Cab Service"))
    wa_text = meta.get("wa_custom_text", "Hi BLR Airport Cab, I would like to book a cab.")

    html = html.replace("{{ page.title | default: \"Bangalore Airport Taxi Service | 24/7 Pickup & Drop | BLR Airport Cab\" | escape }}", title)
    html = html.replace("{{ page.title | escape }}", title)
    html = html.replace("{{ page.title }}", title)
    html = html.replace("{{ page.description | default: \"Book dependable Bangalore Airport Taxi service for Kempegowda International Airport (BLR). 24/7 airport pickup & drop, local cab packages & outstation trips. Call +91 9180182667.\" | escape }}", desc)
    html = html.replace("{{ page.description | escape }}", desc)
    html = html.replace("{{ page.description }}", desc)
    html = html.replace("{{ page.h1 | default: page.title }}", h1)
    html = html.replace("{{ page.lead | default: page.description }}", lead)
    html = html.replace("{{ page.lead }}", lead)
    html = html.replace("{{ page.hero_badge | default: \"24/7 Cab Service\" }}", badge)
    html = html.replace("{{ page.category | default: \"BLR Airport Cab\" }}", badge)
    html = html.replace("{{ page.og_title | default: page.title | escape }}", title)
    html = html.replace("{{ page.og_description | default: page.description | escape }}", desc)
    og_img = meta.get("og_image", "assets/images/blr-airport-cab-og.jpg")
    html = html.replace("{{ page.og_image | default: 'assets/images/airport-hero.webp' }}", og_img)
    html = html.replace("{{ page.og_image | default: 'assets/images/blr-airport-cab-og.jpg' }}", og_img)
    html = html.replace("{{ page.wa_custom_text | default: 'Hi BLR Airport Cab, I would like to book a cab.' | url_encode }}", urllib.parse.quote(wa_text))
    html = html.replace("{{ page.booking_tab }}", meta.get("booking_tab", "airport-drop"))
    html = html.replace("{{ page.url }}", meta.get("url", "/"))

    # If conditions cleanup
    html = re.sub(r'\{%\s*if page\.keywords\s*%\}(.*?)\{%\s*endif\s*%\}', 
                  f'<meta name="keywords" content="{meta.get("keywords", "")}">' if meta.get("keywords") else '', html)

    html = re.sub(r'\{%\s*if page\.lead\s*%\}(.*?)\{%\s*endif\s*%\}', 
                  f'<p class="lead" style="color: #E2E8F0; max-width: 760px; margin: 0 auto;">{lead}</p>' if meta.get("lead") else '', html, flags=re.DOTALL)

    # Active nav link logic
    page_url = meta.get("url", "/")
    is_home = page_url == "/"
    is_airport = any(x in page_url for x in ["bangalore-airport-taxi", "airport-cab", "airport-pickup", "airport-taxi-fare"])
    is_local = any(x in page_url for x in ["local", "hourly-cab-rental", "sightseeing", "city-pickup-drop"])
    is_outstation = "outstation" in page_url
    is_fleet = "our-fleet" in page_url
    is_contact = "contact" in page_url

    html = re.sub(r'\{%\s*if page\.url == \'/\'\s*%\}.*?\{%\s*endif\s*%\}', "active" if is_home else "", html)
    html = re.sub(r'\{%\s*if page\.url contains \'bangalore-airport-taxi\'.*?%\}.*?\{%\s*endif\s*%\}', "active" if is_airport else "", html)
    html = re.sub(r'\{%\s*if page\.url contains \'local\'.*?%\}.*?\{%\s*endif\s*%\}', "active" if is_local else "", html)
    html = re.sub(r'\{%\s*if page\.url contains \'outstation\'\s*%\}.*?\{%\s*endif\s*%\}', "active" if is_outstation else "", html)
    html = re.sub(r'\{%\s*if page\.url contains \'our-fleet\'\s*%\}.*?\{%\s*endif\s*%\}', "active" if is_fleet else "", html)
    html = re.sub(r'\{%\s*if page\.url contains \'contact\'\s*%\}.*?\{%\s*endif\s*%\}', "active" if is_contact else "", html)

    # Breadcrumb conditions
    html = re.sub(r'\{%\s*if page\.parent_title and page\.parent_url\s*%\}.*?\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}', r'\1', html, flags=re.DOTALL)

    # Any remaining unhandled liquid tags
    html = re.sub(r'\{%\s*if\b.*?%\}.*?\{%\s*endif\s*%\}', '', html, flags=re.DOTALL)
    html = re.sub(r'\{%\s*endif\s*%\}', '', html)

    return html

def build_page(source_file, output_file, depth=0):
    """Compiles a single markdown or html page through layouts and includes."""
    with open(source_file, "r", encoding="utf-8") as f:
        raw_content = f.read()

    meta, body = parse_front_matter(raw_content)
    baseurl = ".." if depth == 1 else "."

    site_data = load_data()

    # Layout chaining
    layout_name = meta.get("layout", "default")
    if layout_name == "service":
        with open(os.path.join(ROOT_DIR, "_layouts", "service.html"), "r", encoding="utf-8") as f:
            svc_layout_meta, svc_layout_body = parse_front_matter(f.read())
        assembled = svc_layout_body.replace("{{ content }}", body)
        layout_name = "default"
    elif layout_name == "landing-page":
        with open(os.path.join(ROOT_DIR, "_layouts", "landing-page.html"), "r", encoding="utf-8") as f:
            lp_meta, lp_body = parse_front_matter(f.read())
        assembled = lp_body.replace("{{ content }}", body)
        layout_name = "default"
    else:
        assembled = body

    if layout_name == "default":
        with open(os.path.join(ROOT_DIR, "_layouts", "default.html"), "r", encoding="utf-8") as f:
            _, default_layout = parse_front_matter(f.read())
        assembled = default_layout.replace("{{ content }}", assembled)

    # Process loops, includes, vars
    assembled = process_site_loops(assembled, site_data, baseurl)
    assembled = render_includes(assembled, meta, baseurl, site_data)
    assembled = render_liquid_vars(assembled, meta, baseurl)

    # Ensure target directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(assembled)

    print(f"Generated: {os.path.relpath(output_file, ROOT_DIR)}")

def main():
    print("Building BLR Airport Cab static website...")
    site_data = load_data()
    print(f"Loaded {len(site_data['services'])} services, {len(site_data['vehicles'])} vehicles.")

    # 1. Homepage
    build_page(os.path.join(ROOT_DIR, "_pages", "index.html"), os.path.join(ROOT_DIR, "index.html"), depth=0)

    # 2. 404 Page
    build_page(os.path.join(ROOT_DIR, "_pages", "404.html"), os.path.join(ROOT_DIR, "404.html"), depth=0)

    # 3. All Service & Static Pages from pages/
    pages_map = [
        ("bangalore-airport-taxi.md", "bangalore-airport-taxi/index.html"),
        ("bangalore-to-airport-cab.md", "bangalore-to-airport-cab/index.html"),
        ("bangalore-airport-pickup.md", "bangalore-airport-pickup/index.html"),
        ("bangalore-local-taxi.md", "bangalore-local-taxi/index.html"),
        ("bangalore-hourly-cab-rental.md", "bangalore-hourly-cab-rental/index.html"),
        ("bangalore-sightseeing-taxi.md", "bangalore-sightseeing-taxi/index.html"),
        ("bangalore-city-pickup-drop.md", "bangalore-city-pickup-drop/index.html"),
        ("bangalore-outstation-cabs.md", "bangalore-outstation-cabs/index.html"),
        ("our-fleet.md", "our-fleet/index.html"),
        ("bangalore-airport-taxi-fare.md", "bangalore-airport-taxi-fare/index.html"),
        ("about-us.md", "about-us/index.html"),
        ("contact.md", "contact/index.html"),
        ("privacy-policy.md", "privacy-policy/index.html"),
        ("booking-terms.md", "booking-terms/index.html"),
        ("thank-you.md", "thank-you/index.html"),
    ]

    for src_name, dest_rel in pages_map:
        src_path = os.path.join(ROOT_DIR, "pages", src_name)
        dest_path = os.path.join(ROOT_DIR, dest_rel)
        if os.path.exists(src_path):
            build_page(src_path, dest_path, depth=1)
        else:
            print(f"Warning: Source not found {src_name}")

    print("Site build complete! 16 pages compiled successfully.")

if __name__ == "__main__":
    main()

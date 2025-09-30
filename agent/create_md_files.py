import json
import re
import sys

def convert_interview_json_to_md(input_file, output_prefix="output", target_size=5000):
    # Carrega el fitxer JSON
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Recupera les metadades i l'array d'entrevistes
    metadata = data.get("metadata", {})
    interview = data.get("interview", [])
    
    # Construeix el front matter en format YAML
    front_matter_lines = ["---"]
    for key, value in metadata.items():
        if isinstance(value, list):
            front_matter_lines.append(f"{key}:")
            for item in value:
                front_matter_lines.append(f"  - {item}")
        else:
            front_matter_lines.append(f"{key}: {value}")
    front_matter_lines.append("---\n")
    front_matter = "\n".join(front_matter_lines)
    
    # Agrupa tots els camps que comencen per "text" segons l'índex
    groups = {}
    for item in interview:
        # Es necessita que cada element tingui la clau "role" i pot tenir diverses claus que comencin per "text"
        role = item.get("role", "").strip()
        for key, value in item.items():
            if key.startswith("text"):
                match = re.match(r'text(\d+)', key)
                if match:
                    idx = match.group(1)
                    if idx not in groups:
                        groups[idx] = {}
                    groups[idx][role] = value.strip()
    
    # Ordena els grups per número (de menor a major)
    sorted_indices = sorted(groups, key=lambda x: int(x))
    
    # Inicialitza el contingut actual amb el front matter
    current_content = front_matter
    file_count = 1
    
    # Funció per escriure el contingut en un fitxer de sortida
    def write_output(content, count):
        filename = f"{output_prefix}_{count}.md"
        with open(filename, "w", encoding="utf-8") as outf:
            outf.write(content)
        print(f"Creat {filename} (mida: {len(content.encode('utf-8'))} bytes)")
    
    # Itera sobre cada grup (cada parell de preguntes/respostes)
    for idx in sorted_indices:
        group = groups[idx]
        pair_text = ""
        if "Entrevistador" in group:
            pair_text += f"**Entrevistador**: {group['Entrevistador']}\n\n"
        if "SOS" in group:
            pair_text += f"**SOS**: {group['SOS']}\n\n"
        # També pots afegir altres rols si n'hi ha, concatenant-los
        
        # Si afegir aquest parell fa que la mida superi el límit...
        tentative = current_content + pair_text
        if len(tentative.encode("utf-8")) < target_size:
            current_content = tentative
        else:
            # Escriu el fitxer actual si ja conté contingut (excloent front matter)
            if len(current_content.encode("utf-8")) > len(front_matter.encode("utf-8")):
                write_output(current_content, file_count)
                file_count += 1
                current_content = front_matter + pair_text
            else:
                # Si current_content només té front matter, escriu aquest parell sol
                current_content = front_matter + pair_text
                write_output(current_content, file_count)
                file_count += 1
                current_content = front_matter

    # Escriu el contingut restant si hi ha algun parell
    if len(current_content.strip()) > len(front_matter.strip()):
        write_output(current_content, file_count)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Ús: python convert_to_md_split.py <fitxer_entrada.json> [<prefix_sortida>]")
        sys.exit(1)
    
    input_filename = sys.argv[1]
    output_prefix = sys.argv[2] if len(sys.argv) > 2 else "output"
    
    convert_interview_json_to_md(input_filename, output_prefix, target_size=5000)


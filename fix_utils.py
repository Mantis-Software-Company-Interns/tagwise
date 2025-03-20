with open("tagwiseapp/reader/utils.py", "r") as f:
    content = f.read()

# Girinti hatalarını düzelt
content = content.replace("    else:
                    category_item['subcategory'] = """, "                else:
                    category_item['subcategory'] = """)
content = content.replace("            corrected_json['main_category'] = ""
        corrected_json['subcategory'] = """, "            corrected_json['main_category'] = ""
            corrected_json['subcategory'] = """)

with open("tagwiseapp/reader/utils.py", "w") as f:
    f.write(content)

print("Girinti hataları düzeltildi.")
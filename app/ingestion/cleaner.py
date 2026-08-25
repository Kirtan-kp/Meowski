import re

def clean(text : str) -> str:
    
    text = text.replace("\x00", "")   #removing null characters
    text = re.sub(r"[ \t]+" , " " , text) #removing extra spaces or tabs with one space
    text = re.sub(r"\n{3,}" , "\n\n" , text)  #removing 3 or more newline sepration with 2 line separation for paragraph separation

    return text.strip()
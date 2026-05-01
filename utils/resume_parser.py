# Simple keyword-based skill extraction

SKILLS = [
    "python", "java", "c++", "machine learning", "deep learning",
    "html", "css", "javascript", "sql", "flask", "react"
]


def extract_skills(text):
    text = text.lower()
    found_skills = []

    for skill in SKILLS:
        if skill in text:
            found_skills.append(skill)

    
    return list(set(found_skills))
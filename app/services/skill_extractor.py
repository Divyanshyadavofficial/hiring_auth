import re

SKILLS_DB = [
    "python",
    "java",
    "c++",
    "fastapi",
    "django",
    "flask",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "docker",
    "kubernetes",
    "tensorflow",
    "pytorch",
    "machine learning",
    "deep learning",
    "langchain",
    "langgraph",
    "react",
    "javascript",
    "typescript",
    "aws",
    "git",
    "linux"
]

def extract_skills(text:str):
    text = text.lower()
    found_skills = set()
    for skill in SKILLS_DB:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern,text):
            found_skills.add(skill)
            
    return list(found_skills)

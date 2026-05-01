from openai import OpenAI
import re
import os

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("QUESTION_KEY")
)

def extract_numbered_questions(text):
    lines = text.split("\n")

    questions = []
    for line in lines:
        line = line.strip()

        if re.match(r'^\d+[\.\)]\s+', line):
            questions.append(line)

    return questions
def generate_questions(skills, role):
    prompt = f"Generate 5 difficult and different interview questions alone for a {role} exactly based on these skills: {skills} the question should be answerable not like develop or something else like not answerable in some 3 lines no extra thing like Here is your questions like that nothing start from 1. and till 5."

    try:
        completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        text = completion.choices[0].message.content

        questions =extract_numbered_questions(text)
        return questions

    except Exception as e:
        print("ERROR:", e)
        return ["Error generating questions"]
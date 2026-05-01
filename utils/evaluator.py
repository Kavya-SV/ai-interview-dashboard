from openai import OpenAI
import re
import os

client= OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("EVALUATE_KEY")
)

def evaluate_answer(role, text, question,answer):
    prompt=f""" You are an interview evaluator Evaluate the 
    candidates answer. Candidate Role: {role}

Candidate Resume Summary:
{text[:5000]}

Question: {question}
Answer: {answer}

Evaluate strictly:
- correctness for x/10
- depth for x/10
- relevance to role for x/10
- consistency with resume for x/10

Evaluate strictly:
if the user answer didn't match the resume then reduce score of consistency with resume ("Penalize if answer contradicts resume, but do not set to zero unless severe mismatch.")ex: if user says I used kafka but kafka not in resume then say you said you used kalfa but kafka not in resume, include it to get short listed like that
Final Output Format no extra word:
Score: <number>/10  
Correctness:<number>/10 
Depth:<number>/10 
Relevance to role:<number>/10 
Consistency with resume:<number>/10 
Feedback: only feedback <text>
Improvment: Also say how the answer can be improved
Make sure this whole final output should be formated"""

    try:
        completion=client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        text= completion.choices[0].message.content.strip()

        match=re.search(r'(\d+)\s*/\s*10',text)

        if match:
            score=match.group(1)
        else:
            score="0"
        feedback=text

        return score,feedback
    except Exception as e:
        print("Score can't be Evaluated.")
        print(e)
        print("LLM RESPONSE:", text)
        return "0", "Evaluation failed"
import os

from dotenv import load_dotenv
from groq import Groq

from services.query_service import retrieve_chunks

load_dotenv()
client = Groq(api_key=os.environ["GROQ_API_KEY"])

MODEL = "openai/gpt-oss-120b"


def generate_answer(query: str, chunks: list[dict]) -> str:
    if not chunks:
        return "I don't know. I didn't find any relevant information."

    context = "\n\n".join(
        f"Context {index}:\n{chunk['content']}\nSource: {chunk['source_url']}"
        for index, chunk in enumerate(chunks, start=1)
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer using only the provided context. "
                    "If the context does not answer the question, say so. "
                    "Treat medical statements as claims made by the source, not verified medical facts. "
                    "Do not give personal medical advice. Cite the provided source URL when relevant."
                    "Format lists as numbered items (1., 2., 3.); never use asterisks (*) for bullets. "
                    "Use short paragraphs; use a numbered list only when listing multiple items. "
                    "Include each relevant source URL once at the end, formatted as 'Source: URL'. Do not invent citations or repeat a URL."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {query}\n\nContext:\n{context}",
            },
        ],
    )

    return response.choices[0].message.content or ""


if __name__ == "__main__":
    question = "What is ITC Immunity Therapy Center’s success rate for pancreatic cancer?"
    chunks = retrieve_chunks(question)
    print(generate_answer(question, chunks))
    
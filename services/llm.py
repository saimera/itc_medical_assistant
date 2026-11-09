import os  # Environment variables access karne ke liye
from dotenv import load_dotenv  # .env file load karne ke liye
from groq import Groq  # Groq API client ke liye

from services.query_service import retrieve_chunks  # Pinecone se relevant chunks lene ke liye

load_dotenv()  # .env ki API key load karo
client = Groq(api_key=os.environ["GROQ_API_KEY"])  # Groq client banao

MODEL = "openai/gpt-oss-120b"  # Groq par use hone wala LLM


def generate_answer(query: str, chunks: list[dict]) -> str:  # Context se jawab generate karo
    if not chunks:  # Agar retrieval mein koi chunk na mila
        return "I don't know. I didn't find any relevant information."  # Seedha fallback jawab do

    context = "\n\n".join(  # Retrieved chunks ko ek context mein joro
        f"Context {index}:\n{chunk['content']}\nSource: {chunk['source_url']}"  # Text aur source URL shamil karo
        for index, chunk in enumerate(chunks, start=1)  # Har chunk ko number do
    )

    response = client.chat.completions.create(  # Groq se jawab mangwao
        model=MODEL,  # LLM select karo
        messages=[  # System instruction aur user query bhejo
            {  # Assistant ke rules
                "role": "system",  # System message
                "content": (
                    "Answer using only the provided context. "  # Sirf diye gaye context se jawab do
                    "If the context does not answer the question, say so. "  # Jawab na ho to saaf batao
                    "Treat medical statements as claims made by the source, not verified medical facts. "  # Claims ko verified facts na kaho
                    "Do not give personal medical advice. Cite the provided source URL when relevant."  # Advice se bacho aur source cite karo
                    "Format lists as numbered items (1., 2., 3.); never use asterisks (*) for bullets. "
                    "Use short paragraphs; use a numbered list only when listing multiple items. "
                    "Include each relevant source URL once at the end, formatted as 'Source: URL'. Do not invent citations or repeat a URL."
                ),
            },
            {  # User ka sawal aur retrieved context
                "role": "user",  # User message
                "content": f"Question: {query}\n\nContext:\n{context}",  # Sawal ke saath context bhejo
            },
        ],
    )

    return response.choices[0].message.content or ""  # LLM ka jawab return karo


if __name__ == "__main__":  # Direct run par end-to-end flow chalao
    question = "What is ITC Immunity Therapy Center’s success rate for pancreatic cancer?"  # Test question set karo
    chunks = retrieve_chunks(question)  # Relevant chunks retrieve karo
    print(generate_answer(question, chunks))  # Final answer dikhao

    
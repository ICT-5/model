import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_google_vertexai import ChatVertexAI
import vertexai

# =====================================
# 5) LLM 체인 초기화 (Vertex AI + LangChain)
# =====================================
def init_llm_chain():
    PROJECT_ID = os.getenv("VERTEX_PROJECT_ID", "magnificent-ray-469309-m3")
    REGION = os.getenv("VERTEX_REGION", "us-central1")

    vertexai.init(project=PROJECT_ID, location=REGION)
    llm = ChatVertexAI(model="gemini-2.0-flash-001", temperature=0.7)

    system_message = SystemMessage(content="""
    당신은 면접관입니다. 다음 원칙을 반드시 지키세요:
    - 질문은 항상 한 개씩만 생성하세요.
    - 이미 생성된 질문은 다시 하지 마세요.
    - 질문은 전달받은 이력서 키워드를 기반으로 만들어야 합니다.
    - 허구 내용 생성은 금지입니다.
    - 질문은 불필요하게 장황하지 않게, 간결하고 명확하게 작성하세요.
    - 한 가지 주제에 대해 꼬리질문 3개이상 금지입니다.
    - 이력서 키워드를 기반으로 질문을 생성하되 무조건 직무관련 질문일 필요는 없습니다.
    - 질문을 할 때 괄호로 예시 내용을 제공하지 마세요.
    """)

    persona_template = ChatPromptTemplate.from_messages([
        ("system", system_message.content),
        ("human", """
        면접 유형: {interview_type}
        면접관 성향: {personality}

        지금까지 질문: {previous_question}
        지원자 답변: {previous_answer}

        지원자의 이력서 키워드: {keywords}
            
        이전 대화 내용: {history}

        위 정보를 참고하여, 중복되지 않고 심층적인 다음 질문을 한 개 생성하세요.
        해당 질문은 면접 유형과 부합하며, 질문만 출력하고 분석이나 설명은 하지 마세요.
        """)
    ])

    memory = ConversationBufferMemory(
        memory_key="history",
        input_key="previous_answer",
        return_messages=False
    )

    chain = LLMChain(llm=llm, prompt=persona_template, memory=memory, verbose=True)
    return chain

# =====================================
# 6) 꼬리질문 생성 호출
# =====================================
def generate_follow_up_questions(chain, question, answer, keywords, interview_type, personality):
    variables = {
        "previous_question": question,
        "previous_answer": answer,
        "keywords": ", ".join(keywords),
        "interview_type": interview_type,
        "personality": personality,
    }
    response = chain.run(variables)  # 프롬프트가 "질문만 출력"하게 구성됨
    return response.strip()